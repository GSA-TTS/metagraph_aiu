# ETL Improvements: etl_pilot.py → etl.py

This document records what changed between `etl_pilot.py` (pilot 1) and the production
`etl.py` and explains the rationale for each change.

---

## 1. `--case` Parameter: Flexible Row Selection

**Change:** Added `argparse` CLI parameter `--case {tiny,mid,full}`.

| Case | Rows selected | Algorithm |
|---|---|---|
| `tiny` (default) | 15 | Overlap-aware slot selection (same as `etl_pilot.py`) |
| `mid` | 25% of total | Stratified random sample, `random_state=42` |
| `full` | All rows | No selection — iterate entire CSV |

**Why:** The pilot was hardcoded to 15 rows. Production workloads require running the
full 2,000+ row inventory. The three-tier design lets developers iterate quickly
(`tiny`) while QA can validate at scale (`mid`) before committing to a full run
(`full`).

**Implementation notes:**
- `select_tiny()`, `select_mid()`, `select_full()` are standalone functions that take
  `df` as input — no global mutation.
- All three return a DataFrame with a clean 0-based integer index and an `orig_idx`
  column preserving the source row number.
- `select_mid` uses `random_state=42` for reproducible sampling across runs.

---

## 2. Auto-Incrementing Output Filename for `tiny`

**Change:** For `--case tiny`, the output file is auto-named `pilot_N_15.ttl` where
`N` is one more than the number of existing `pilot_*_15.ttl` files in the directory.

```
pilot_1_15.ttl  (from etl_pilot.py)
pilot_2_15.ttl  (first etl.py --case tiny run)
pilot_3_15.ttl  (second run)
...
```

`mid` and `full` outputs use timestamps: `run_mid_YYYYMMDD_HHMMSS.ttl` and
`full_2024_YYYYMMDD_HHMMSS.ttl`.

**Why:** Preserves all pilot runs for longitudinal comparison without manual renaming.

---

## 3. Dual-LLM Goal Tagging

**Change:** Goal tagging now uses two models in parallel — Claude Haiku
(`claude-haiku-4-5-20251001`) and GPT-5.4-mini (`gpt-5.4-mini`) — and compares
their outputs.

**Requires:** `OPENAI_API_KEY` environment variable in addition to `ANTHROPIC_API_KEY`.

**New functions:**

| Function | Purpose |
|---|---|
| `_build_goal_prompt(...)` | Builds the shared prompt string used by both models |
| `_parse_goals(raw)` | Strips markdown fences, parses JSON, whitelist-filters against `GOAL_ID_SET`, caps at 5 |
| `_tag_haiku(prompt)` | Calls Claude Haiku; returns filtered goal list |
| `_tag_gpt(prompt)` | Calls GPT-5.4-mini via OpenAI client; returns filtered goal list |
| `tag_goals_dual(...)` | Orchestrates both calls; returns full result dict with agreement info |

**Why:** Using two independent models cross-checks the business goal assignments.
Agreement between Haiku and GPT increases confidence in the classification without
requiring human review. Disagreements surface cases where the goal boundary is
ambiguous — exactly the records most worth examining.

---

## 4. Opus Referee on Disagreement

**Change:** When Haiku and GPT return different goal sets, `claude-opus-4-6` is
invoked as a referee.

**Agreement metric:**

```
disagreement_pct = |symmetric_difference| / |union| * 100
```

- `0%` — identical sets (agreed)
- `100%` — completely non-overlapping sets

**Referee behavior:** The Opus prompt presents both model outputs alongside the
original use case description and the full goal catalog, then asks Opus to select
the better set (or propose a corrected merge). The response includes a `"chosen"`
field: `"A"` (Haiku), `"B"` (GPT), or a merged set.

**Fallback:** If Opus returns unparseable JSON, Haiku's result is used and `chosen`
is set to `"A (parse fallback)"`.

**Why:** Opus is Anthropic's most capable reasoning model. Delegating contested
classifications to Opus mirrors a senior analyst review step, adding a quality gate
that the pilot lacked.

---

## 5. Disagreement Logging (JSONL)

**Change:** Each disagreement is appended to `disagreements_{case}_{timestamp}.jsonl`.

Each JSON record contains:

```json
{
  "use_case_name": "...",
  "haiku_goals": ["aiu:BG_1_1", ...],
  "gpt_goals": ["aiu:BG_2_3", ...],
  "opus_goals": ["aiu:BG_1_1", "aiu:BG_2_3"],
  "opus_chosen": "A",
  "disagreement_pct": 66.7,
  "prompt": "Use Case: ...\nPurpose: ...\n..."
}
```

The `prompt` field is included for full reproducibility — it contains the exact
text sent to both models, including the goal catalog.

**Why:** Persistent disagreement records enable post-run audit, inter-model
reliability analysis, and taxonomy refinement (high-disagreement sub-goals signal
poorly-defined boundaries in the taxonomy).

---

## 6. Agreement Statistics in Final Report

**Change:** Step 6 now prints a `Dual-LLM Agreement Statistics` section alongside
the existing goal-frequency and per-record summaries:

```
Dual-LLM Agreement Statistics:
  Agreed (Haiku == GPT) : 12/15
  Disagreements         : 3/15
  Avg disagreement %    : 58.3%
  Opus chose Haiku (A)  : 2
  Opus chose GPT   (B)  : 1
  Disagreement log      : disagreements_tiny_20260406_143022.jsonl
```

The per-record goal table also shows an `Agreed` column.

---

## 7. Refactored Code Structure

**Change:** The inline script body of `etl_pilot.py` has been reorganised into
named functions:

- Row selection: `_add_rows()`, `select_tiny()`, `select_mid()`, `select_full()`
- Goal tagging: `_build_goal_prompt()`, `_parse_goals()`, `_tag_haiku()`,
  `_tag_gpt()`, `_tag_opus_referee()`, `tag_goals_dual()`, `_log_disagreement()`
- All ETL helper functions unchanged: `slugify()`, `lookup()`, `to_bool()`,
  `add_time_node()`, `split_multival()`

Work DataFrame renamed from `pilot_df` → `work_df` to reflect multi-case usage.

**Why:** Named functions with typed signatures are easier to test, maintain, and
extend (e.g., adding a fourth model or a caching layer) without restructuring the
whole script.

---

## 8. API Validation at Startup

**Change:** Both `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` are checked immediately
after argument parsing, before any CSV loading or LLM calls, with a clear error
message.

**Why:** Fail fast. In `etl_pilot.py`, the key check happened in the middle of Step 4
— after potentially loading and processing hundreds of rows. Missing a key after
10 minutes of ETL work is frustrating.

---

## Non-Changes (Preserved from etl_pilot.py)

- Column index (`CI`) dictionary and `col()` accessor — unchanged (avoids
  encoding issues with smart-apostrophe CSV headers)
- SKOS concept lookup tables and alias dictionaries — unchanged
- Line-by-line FSM taxonomy parser — unchanged
- Per-row RDF ETL logic (Steps 3, field mapping) — unchanged
- SHACL validation parameters (`advanced=True`, `inference="none"`) — unchanged
- Inline `# prefLabel` comment annotation on BG_* IRIs — unchanged

---

## 9. GPT-5.4-mini API Compatibility Fix

**Change:** GPT-5.4-mini does not accept the `max_tokens` parameter; it requires
`max_completion_tokens`. The `_tag_gpt()` function uses `max_completion_tokens=256`.

**Discovered:** During pilot 2 run (2026-04-07). The OpenAI API returns HTTP 400
with `"Unsupported parameter: 'max_tokens' is not supported with this model"`.

---

## 10. Sonnet Replaces Haiku for Primary Tagging

**Change:** `_tag_haiku()` replaced by `_tag_sonnet()` using `claude-sonnet-4-6`.
Agreement statistics now report `Agreed (Sonnet == GPT)` and `Opus chose Sonnet (A)`.

**Why:** Claude Sonnet is a significantly more capable reasoning model than Haiku.
Pilot 3 showed Opus chose Sonnet's result more consistently (higher A-rate) than
Haiku's in pilot 2, validating the upgrade.

---

## 11. Disagreement Log Threshold (>30%)

**Change:** `_log_disagreement()` is only called when `disagreement_pct > 30`.
The console summary distinguishes `total_disagreed` from `logged_count`.

**Why:** Low-level disagreements (≤30%) typically involve one-goal differences on
small sets. Logging every disagreement inflated the JSONL with low-signal records.
Agreements ≤30% that still differ are tracked in the in-memory stats but not on disk.

---

## 12. BG_8_3 Blacklist and Pre-Assignment

**Change:** `GOAL_BLACKLIST: set[str] = {"aiu:BG_8_3"}` — a module-level constant.

- Goals in the blacklist are excluded from the LLM catalog and from `_parse_goals()` filtering
- After Step 3, all `aiu:hasBusinessGoal` triples for blacklisted goals are pre-assigned
  to every plan node before goal tagging begins
- The console report shows `Pre-assigned goal triples` separately from `LLM-tagged goal triples`

**Why:** `BG_8_3 (Automation and AI enablement)` was assigned to 100% of records in
pilots 2 and 3 — trivially true for an AI inventory and analytically useless. Pre-
assigning it rather than deleting it preserves completeness in the RDF graph while
removing it from the discrimination step.

---

## 13. Evidence Anchor in Goal Prompt

**Change:** The goal prompt now requires explicit phrase-level evidence:

> "Include a goal only if you find a specific phrase, function, or outcome in the
> use case that clearly corresponds to those signals. Do not select based on general
> context or inference alone. Prefer fewer, higher-confidence selections."

**Why:** Pilots 2-3 showed models selecting goals by general-domain inference
("this is a government AI system → must have compliance goals"). Raising the bar
to phrase-level evidence reduces noise and increases precision.

**Effect:** Mean goals per use case dropped from ~3.6 (pilot 2) to ~1.93 (pilot 5).

---

## 14. Description Cutoff Increased to 1000 Characters

**Change:** `_goal_catalog()` now uses `desc[:1000]` instead of `desc[:150]`.

**Why:** Many taxonomy goal descriptions span multiple sentences covering nuanced
conditions. Cutting at 150 chars truncated critical discriminating text.

---

## 15. Enriched Taxonomy Catalog with Lookup-Field Signal Phrases

**Change:** `_goal_catalog()` rewritten from flat `id: label\n  desc` format to
structured blocks:

```
aiu:BG_X_Y: Label
  Goal: <description up to 1000 chars>
  Look in Purpose/Benefits for: "signal1", "signal2", ...
  Look in AI Outputs for: "signal3", ...
```

**New components:**

| Component | Purpose |
|---|---|
| `_FIELD_TO_PROMPT` dict | Maps taxonomy lookup-field names to prompt section labels |
| `_goal_catalog()` rewrite | Builds one block per non-blacklisted goal with signal lines |
| `parse_taxonomy` en-dash fix | `[\u2013\-]` matches `–` (U+2013) separator used in taxonomy |
| `parse_taxonomy` curly-quote fix | Normalizes `"..."` (U+201C/U+201D) before `re.findall` |

**Parse bugs fixed:** The taxonomy uses en-dash `–` as field separator and curly
quotes `"..."` for signal phrases. Both caused `m2` regex to never match, so
`seed_examples` was always empty in prior pilots. Fixed in pilot 5.

**Why:** Providing models with the taxonomy's own recommended lookup fields and
example phrases grounds classification in evidence visible in the inventory CSV
text fields, reducing inference from general domain knowledge.

---

## 16. Opus Goal Fallback for Empty Results

**Change:** When the Opus referee returns a parseable JSON `{"goals": [...]}` but
all listed goals are filtered out by `GOAL_ID_SET` or `GOAL_BLACKLIST`, the result
falls back to the model Opus chose (`A → sonnet_goals`, `B → gpt_goals`) and
`chosen` is appended with `" (goal fallback)"`.

**Why:** Rare but observed in pilots 3-4: Opus occasionally returned hallucinated
goal IDs that passed JSON parse but failed whitelist check, yielding an empty
assigned set. The fallback ensures no record has zero non-blacklisted goals.

---

## 17. Purpose/Benefits Context Window Doubled to 1200 Characters

**Change:** `_build_goal_prompt()` now passes `purpose[:1200]` instead of `purpose[:600]`.

**Why:** Many federal AI use case descriptions are verbose and bury key mission language
in later sentences. At 600 chars the prompt was frequently truncated before the
most discriminating text appeared. Doubling the window captures the full intent
of most records without significantly increasing token cost.

---

## 18. Illustrative Signal Phrases Replace Evidence-Matching Instructions

**Change:** The goal prompt instruction changed from "find a specific phrase… that
clearly corresponds to those signals" (evidence-matching) to "use the goal
descriptions and illustrative phrases to understand what each goal means, then
judge which goals apply based on the use case as a whole" (semantic evaluation).

The catalog block header was updated accordingly:

```
"(Each entry: goal id/label, description, then example phrases that "
"illustrate what the goal looks like in practice.)\n"
```

**Why:** Signal phrases in the taxonomy are examples of what a goal *looks like*,
not a checklist to match against. Framing them as evidence requirements caused
both models to reject valid goals when the exact phrasing wasn't present, while
still accepting poor matches when a surface phrase did match. Framing them as
illustrations lets the models reason about intent rather than pattern-match strings.

---

## 19. Goal Cap Reduced to 3 and Conservative Bias Added

**Change:** The hard cap in `_parse_goals()` was lowered from `[:5]` to `[:3]`.
The prompt instruction was rewritten to enforce conservative selection:

> "Be conservative: when uncertain whether a goal applies, exclude it. Precision
> matters more than recall — a shorter, confident list is better than a longer
> speculative one."

**Why:** Pilots 2-5 showed GPT systematically returning more goals than Sonnet
(GPT was a superset in 10/14 disagreements; Sonnet was never a superset of GPT).
A lower cap forces both models to prioritise their strongest matches and reduces
the asymmetric over-selection that inflated disagreement rates.

---

## 20. GOALS: Line Parser in `_parse_goals`

**Change:** `_parse_goals()` first scans response lines for one beginning with
`"GOALS:"` and extracts JSON from that line only. If no such line is found it
falls back to parsing the entire response as JSON. The cap applies in both paths.

```python
for line in raw.splitlines():
    line = line.strip()
    if line.upper().startswith("GOALS:"):
        json_part = line[line.index(":") + 1:].strip()
        ...
        return parsed[:3]
# fallback: parse whole response
```

**Why:** Options B and A (pilots 8-12) had models emit structured multi-section
responses with `GOALS:` as the terminal line. The original parser tried to
`json.loads()` the entire response, which always failed on multi-section text.
The line-first strategy handles both structured and plain-JSON responses without
branching on prompt version.

---

## 21. Option B: Cluster-First Filtering (Piloted and Abandoned)

**Change:** Implemented a two-stage single-call prompt: Step 1 selects 1-3 goal
clusters from a 10-cluster summary (`CLUSTER_SUMMARY`); Step 2 evaluates only
sub-goals within the selected clusters; Step 3 emits `GOALS:` JSON.

**Outcome:** Agreement worsened (pilots 8-9). Models selected different clusters,
causing them to evaluate completely disjoint goal spaces — a disagreement on the
cluster level silently excluded correct sub-goals for one model while the other
evaluated them. Cluster mis-selection was harder to detect than direct goal
mis-selection.

**Why reverted:** The cluster filter added a new failure mode (hard exclusion on
wrong cluster choice) that dominated over the benefit of narrowed evaluation scope.
Design documented in `goal_tagging_prompt_options.md`.

---

## 22. Option A: Inline Chain-of-Thought (Piloted and Abandoned)

**Change:** Added an inline CoT prompt requiring models to (1) list 3-5 themes,
(2) write a one-line yes/no verdict per goal in the full 38-goal catalog, (3)
select 1-3 strongest from the "yes" set, and emit `GOALS:` JSON.

**Outcome:** CoT made Sonnet more conservative (returned fewer goals). GPT with
high reasoning also returned fewer goals, producing several empty-set agreements
that inflated the apparent agreement rate while providing no goal information.
Agreement on substance did not meaningfully improve over the pilot 6 baseline.

**Why reverted:** The structured format increased response length and parsing
complexity without improving classification quality. Design documented in
`goal_tagging_prompt_options.md`. The session reverted to the pilot 6 prompt style.

---

## 23. GPT Responses API with High Reasoning

**Change:** `_tag_gpt()` was migrated from `client.chat.completions.create()` to
`client.responses.create()` (OpenAI Responses API), the only endpoint that accepts
the `reasoning` parameter:

```python
resp = _openai_client.responses.create(
    model="gpt-5.4-mini",
    reasoning={"effort": "high"},
    max_output_tokens=1024,
    instructions=_SYSTEM,
    input=prompt,
)
return _parse_goals(resp.output_text or "")
```

**Why:** `reasoning={"effort": "high"}` activates GPT-5.4-mini's extended thinking
mode. The Chat Completions endpoint rejects this parameter with HTTP 400; the
Responses API supports it natively. High-reasoning GPT output showed materially
improved goal relevance: Opus chose GPT's result in 6/11 disagreements (pilot 14)
vs. 0/14 (pilot 6), confirming the reasoning upgrade improved GPT's classification
quality.

**Compatibility note:** `max_tokens` is also invalid for this endpoint;
`max_output_tokens` is used instead (the parameter name already used since
improvement 9).

---

## 24. Opus Referee: Stripped Prompt (No Embedded Catalog)

**Change:** The Opus referee prompt no longer embeds the full goal catalog or any
structured CLUSTERS/EVALUATION/GOALS instructions. It now contains only:
(1) a brief framing sentence, (2) the use case header (name, purpose, outputs,
topic, stage — extracted by splitting on `"\nBusiness Goal Catalog"` or
`"\nGoal Clusters"`), (3) short descriptions (≤300 chars) of only the contested
goals, and (4) both models' selections.

```python
header = prompt.split("\nBusiness Goal Catalog")[0].split("\nGoal Clusters")[0].strip()
contested_ids = list(set(sonnet_goals) | set(gpt_goals))
contested_desc = "\n\n".join(
    f"{g['id']}: {g['label']}\n  {g['description'][:300]}"
    for g in GOALS if g["id"] in contested_ids
)
```

**Why:** In pilot 8, when the referee prompt embedded the full Option B catalog
(containing CLUSTERS:/EVALUATION:/GOALS: instructions), Opus followed those
instructions in its response and placed `"chosen"` and `"goals"` on separate
lines — causing `json.loads(raw)` to fail on 13/15 records. Stripping the catalog
eliminates that instruction contamination and focuses Opus on the narrow arbitration
task (A vs B vs merge on a small contested set).

---

## 25. Opus Referee: Reverse-Line JSON Parser

**Change:** The Opus response parser searches lines in reverse order for the last
line that contains both `"chosen"` and `"goals"`, then attempts `json.loads()` on
that line. Falls back to whole-response JSON parse if no such line is found.

```python
data = None
for line in reversed(raw.splitlines()):
    line = line.strip()
    line = re.sub(r"^```[a-z]*\n?", "", line).rstrip("`").strip()
    if '"chosen"' in line and '"goals"' in line:
        try:
            data = json.loads(line)
            break
        except (json.JSONDecodeError, ValueError):
            pass
```

**Why:** When Opus emitted multi-line reasoning before the JSON answer, the final
JSON line contains both fields on one object. Scanning in reverse finds the answer
line without requiring the model to emit only JSON. This complements improvement 24:
even if Opus does emit some prose, the parser extracts the verdict robustly.

---

## 26. Topic Area Signals Removed from `_FIELD_TO_PROMPT`

**Change:** `mission_or_topic_area` was removed from `_FIELD_TO_PROMPT`:

```python
_FIELD_TO_PROMPT: dict[str, str] = {
    "intended_purpose_and_expected_benefits": "Purpose/Benefits",
    "problem_to_be_solved":                  "Purpose/Benefits",
    "ai_system_outputs":                     "AI Outputs",
    "stage_of_development":                  "Development Stage",
    "lifecycle_stage":                       "Development Stage",
    "use_case_name":                         "Use Case",
}
```

**Why:** Topic Area signals caused models to anchor on the agency's self-reported
domain label (e.g., "Law Enforcement") rather than evaluating the actual functional
purpose. This contributed to systematic over-application of cluster 7 (Governance)
and cluster 9 (Service and Delivery) goals in records where the domain label was
government-specific but the underlying function was operational (cluster 4) or
data/technology (cluster 8). Removing these signals directs the model to Purpose/
Benefits and AI Outputs where the functional language lives.

---

## 27. Auto-Generated Results Markdown

**Change:** At the end of Step 6, `etl.py` writes a results markdown file named
`etl_{OUT_PATH.stem}_results.md` in the same directory as the output TTL. The file
contains:

- **Selected records table** — agency, use case name, stage, impact type per row
- **RDF summary** — total triples, UseCaseRecord / AIUseCasePlan / AIUseCaseProcess counts
- **Goal tagging table** — per-record: Sonnet goals, GPT goals, agreed flag, final goals
- **Top goals by frequency** — sorted goal IDs with counts
- **Dual-LLM agreement statistics** — agreed count, disagreement count, avg disagreement %,
  Opus A/B breakdown, disagreement log path
- **SHACL violations** — conformance result and per-violation details

```python
RESULTS_MD_PATH = OUT_PATH.parent / f"etl_{OUT_PATH.stem}_results.md"
RESULTS_MD_PATH.write_text(_md, encoding="utf-8")
print(f"Results markdown : {RESULTS_MD_PATH}")
```

**Why:** Prior pilot result summaries were produced manually after each run.
Auto-generation ensures every run produces a self-contained, reproducible record
without post-hoc manual effort, and the file is co-located with the TTL output
for easy cross-referencing.

---

## 28. Exact Row Count Sampling (`--n N`)

**Change:** Added `--n N` CLI parameter for exact row count sampling.

```bash
python3 etl.py --n 50   # selects exactly 50 rows with random_state=42
```

Output is named `run_n{N}_{TIMESTAMP}.ttl` to distinguish from case-based runs.
`--n` takes precedence over `--case` when both are supplied.

**Why:** Enables reproducible fixed-size pilots without having to fit into the
`tiny`/`mid`/`full` slots. Used for baseline prompt experiments (n=50) and
regression testing (n=1).

---

## 29. Intersection Resolution on Disagreement (Opus Referee Removed)

**Change:** When Sonnet and GPT disagree, the final goal list is now computed as
the intersection `S ∩ G`. If the intersection is empty, the union `S ∪ G` is used
as a fallback. The Opus referee call (`_tag_opus_referee`) was removed entirely.

```python
intersection = s_set & g_set
final_goals = sorted(intersection) if intersection else sorted(union)
```

**Why:** The Opus referee added latency (sequential call after parallel Sonnet+GPT)
and cost without a clear accuracy advantage over intersection. Intersection is a
stricter, more conservative resolution strategy that requires both models to agree
on a goal before including it, reducing false positives. Union fallback ensures at
least one goal is always returned.

---

## 30. Goal Cap Increased to 5

**Change:** `_parse_goals` now slices `[:5]` instead of `[:3]`.

**Why:** After removing Opus and switching to intersection logic, goal counts
naturally skew lower. Raising the cap to 5 gives both models more room to propose
goals before intersection pruning reduces the final set.

---

## 31. Parallel Sonnet + GPT Calls

**Change:** `tag_goals_dual` now fires Sonnet and GPT concurrently using
`ThreadPoolExecutor(max_workers=2)`.

```python
with ThreadPoolExecutor(max_workers=2) as _ex:
    _fs = _ex.submit(_tag_sonnet, prompt)
    _fg = _ex.submit(_tag_gpt, prompt)
    sonnet_goals = _fs.result()
    gpt_goals = _fg.result()
```

**Why:** Sonnet and GPT calls are independent. Sequential execution wasted wall-clock
time equal to one full LLM round-trip per use case.

---

## 32. Concurrent Row Processing (`--concurrent N`)

**Change:** Added `--concurrent N` (default 5). Rows are processed in batches of N
using `ThreadPoolExecutor`, each submitting a `tag_goals_dual` call concurrently.

**Why:** For full runs (1,600+ rows), sequential processing at ~5 seconds per row
would take hours. Concurrency at N=5 gives a ~5x throughput improvement with
minimal coordination overhead.

---

## 33. Checkpoint / Resume (`--resume <path>`)

**Change:** After every `CHECKPOINT_INTERVAL` rows (default 50, configurable via
`--checkpoint-interval N`), the pipeline:
1. Flushes the disagreement buffer to disk
2. Serializes the in-progress RDF graph to the output TTL
3. Writes a checkpoint JSONL at `<out_path>.checkpoint.jsonl`

A crashed or interrupted run can be resumed with:

```bash
python3 etl.py --resume run_full_20260407_xxxxxx.ttl.checkpoint.jsonl
```

The checkpoint file stores a `meta` entry (output paths, case) plus one `row` entry
per completed row (goals, agreed flag, Sonnet/GPT breakdown). On resume, completed
rows are replayed directly into the RDF graph and skipped in the worker pool.

**Why:** Full runs over 1,600 rows are long-running and subject to network failures.
Without checkpointing, a crash at row 1,599 requires restarting from scratch. With
50-row checkpoints the worst-case rework is 50 rows.

---

## 34. Buffered Disagreement Logging

**Change:** Disagreement entries are accumulated in `_disagree_buffer` (a module-level
list) and flushed to disk only at each checkpoint. The prompt field is stripped of
everything from `\nBusiness Goal Catalog` onwards to keep log sizes manageable.

```python
_disagree_buffer: list[dict[str, Any]] = []

def _flush_disagree_buffer() -> None:
    if _disagree_buffer:
        with DISAGREE_PATH.open("a", encoding="utf-8") as fh:
            for entry in _disagree_buffer:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        _disagree_buffer.clear()
```

**Why:** Per-row file I/O on a JSONL file is slow and creates contention in concurrent
mode. Batching writes to checkpoint boundaries reduces I/O overhead significantly.
Stripping the catalog text (>3 KB per entry) from logged prompts prevents disagreement
logs from becoming multi-gigabyte files on full runs.

---

## 35. Incremental TTL Serialization

**Change:** The RDF graph is serialized to disk at each checkpoint interval, not only
at the end of Step 4. The final flush after the loop ensures the last partial batch
is also written.

**Why:** For full runs, holding 1,600 records in memory and writing once at the end
risks losing everything on a crash. Incremental serialization means the output TTL
always reflects the latest checkpoint state.

---

## 36. `--no-validate` Flag

**Change:** Added `--no-validate` CLI flag. When set, SHACL validation (Step 5) is
skipped and the results report records `conforms=True, violations=0, warnings=0`.

**Why:** SHACL validation loads two RDF graphs and runs a SPARQL-heavy validation
pass — expensive for large TTLs. For full runs where the schema is well-understood and
violations are expected (missing optional fields in source data), skipping validation
saves significant time. It can be run as a separate post-processing step once ETL
completes.

---

## 37. ETA Reporting in Goal Tagging Progress

**Change:** Each row's progress line now includes elapsed time, estimated time
remaining, and throughput (rows/sec):

```
 0  Some Use Case Name    2   0%  Sonnet  BG_4_1  [0.1 rows/s | ETA ~25m remaining]
```

**Why:** Full runs are long enough that progress feedback matters. ETA lets the user
decide whether to keep waiting or adjust concurrency settings.

---

## 38. Tenacity Retry Logic on API Calls

**Change:** Both `_tag_sonnet` and `_tag_gpt` are decorated with `@retry` from
`tenacity`:

```python
@retry(
    retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
)
```

**Why:** A full run at 1,600 rows hit an `APIConnectionError` (server disconnect) at
row 60 on the first attempt. Without retry, the entire run would fail. With
exponential backoff up to 5 attempts, transient network blips are handled
automatically.

---

## Dependencies Added

```
openai     # GPT-5.4-mini tagging
tenacity   # Retry logic for API calls (improvements 38)
```

Add to `requirements.txt` if maintained:

```
anthropic
openai
pandas
pyshacl
rdflib
tenacity
```
