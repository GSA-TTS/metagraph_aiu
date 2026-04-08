# 2_ETL — Inventory ETL Pipeline

This folder contains the extraction, transformation, and loading (ETL) pipeline that converts the OMB Federal AI Use Case Inventory CSV into RDF graph data conforming to the AIU ontology. It also includes two supporting quality-assurance scripts that should be run before and after the ETL to verify ontology health and graph analytics readiness.

Ontology and shapes files live in [`../1_Ontology/`](../1_Ontology/README.md). This folder contains only pipeline code and its outputs.

Examples use Anthropic LLM and you can substitute with any LLM API of your choice. We do not endorse prefer one LLM over others. 

---

## Pipeline Overview

Three scripts work in sequence. Run them in this order when setting up or after any ontology/shapes change:

```
1. aiu_validation.py       ← regression-test the ontology + shapes pair
2. aiu_analytics_check.py  ← verify graph structure supports planned analytics
3. etl.py                  ← run the ETL; produces RDF output + SHACL report
```

`etl_pilot.py` is the original 15-row prototype. `etl.py` is the production script with `--case` parameter, dual-LLM tagging (Sonnet + GPT-5.4-mini), intersection-based disagreement resolution, checkpoint/resume, and concurrent row processing.
Data flow:

```
../1_Ontology/
  aiu_ontology_ver1.ttl   ──┐
  aiu_shapes.ttl            ├──► aiu_validation.py     (no output file)
  taxonomy_bizGoals.md    ──┘         │
                                      ▼
                               aiu_analytics_check.py  (no output file)
                                      │
                                      ▼
/tmp/inventory_2024.csv  ──────► etl.py --case tiny/mid/full
  (source CSV, placed                  │
   manually before run)                ├──► pilot_N_15.ttl  (tiny)
                                        ├──► run_mid_*.ttl   (mid)
                                        ├──► full_2024_*.ttl (full)
                                        ├──► disagreements_*.jsonl (if any)
                                        └──► console report
```

The ETL reads ontology files from `../1_Ontology/` using paths relative to `__file__`. The source CSV must be placed at `/tmp/inventory_2024.csv` before running.

---

## ETL Pipeline Steps

`etl.py` (and its prototype `etl_pilot.py`) executes six steps end-to-end:

| Step | What it does |
|---|---|
| 1 | Loads `aiu_ontology_ver1.ttl`, `aiu_shapes.ttl`, and `taxonomy_bizGoals.md` into memory; builds SKOS concept lookup tables |
| 2 | Selects rows per `--case` (tiny=15, mid=25%, full=all); see Row Selection below |
| 3 | Converts each CSV row to RDF triples using the ontology property mapping from `aiu_inventory_field_mapping.md` |
| 4 | Tags business goals with **dual LLM** (Claude Sonnet + GPT-5.4-mini) in parallel; resolves disagreements by intersection of the two goal sets (union fallback if empty); writes `aiu:hasBusinessGoal` triples and logs disagreements to JSONL |
| 5 | Runs `pyshacl.validate()` with `advanced=True` (SPARQL targets) and `inference="none"`; reports violations per record |
| 6 | Prints summary statistics: triple counts, goal coverage, SHACL conformance, dual-LLM agreement rate |

### Row Selection

The 15 rows are chosen to maximise coverage of SHACL gate conditions and key analytics dimensions:

| Slot | Count | Selection criteria |
|---|---|---|
| Both-impact + HISP + PII | 2 | Full record, impact ∈ {Both}, HISP=Yes, PII=Yes |
| Rights-impacting + PII | 1 | Full record, impact ∈ {Rights, Both}, PII=Yes |
| Safety-impacting + HISP | 1 | Full record, impact ∈ {Safety, Both}, HISP=Yes |
| Other full records | 6 | Full record, filler (PII diversity preferred) |
| COTS records | 5 | `commercial_ai ≠ None of the Above` |

Greedy agency+topic diversity: no two consecutive selections share the same `agency|topic_area|dev_stage` key.

### Business Goal Tagging

Each use case is classified against the 39-sub-goal business goal taxonomy using two LLMs called in parallel. The same prompt supplies the use case name, purpose/benefits text, AI outputs, topic area, and development stage alongside the full goal catalog. Each model returns JSON `{"goals": ["aiu:BG_X_Y", ...]}`. Returned IDs are whitelist-filtered against the ontology's `GOAL_ID_SET` and capped at 5 per record, preventing hallucinated IRIs. `aiu:BG_8_3` (Regulatory compliance programs) is pre-assigned to all use cases and excluded from LLM selection.

**Agreement evaluation:**
- Exact set match between Sonnet and GPT → written to TTL as-is
- Mismatch → **intersection** `S ∩ G` is written to TTL; if the intersection is empty, the union `S ∪ G` is used as fallback; the disagreement (`sonnet_goals`, `gpt_goals`, `intersection_goals`, `final_goals`, `disagreement_pct`, abbreviated prompt) is appended to the JSONL log

`disagreement_pct = |symmetric_difference| / |union| × 100`

The LLM approach is necessary because the taxonomy uses business-management vocabulary ("process efficiency", "regulatory compliance") while agencies may write in government/technical language ("radiation portal monitors", "anomaly detection at land border ports").

---

## Prerequisites

**Python:** 3.10+

**Dependencies:**

```bash
pip install rdflib pyshacl anthropic openai pandas packaging
```

**API keys** (required for `etl.py`; not needed for validation scripts):

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # Claude Sonnet tagging
export OPENAI_API_KEY=sk-...          # GPT-5.4-mini tagging
```

**Source CSV** (required for `etl_pilot.py` only):

Place the 2024 Federal AI Use Case Inventory CSV at `/tmp/inventory_2024.csv` before running. The file is not included in this repository.

---

## Usage

Run from any working directory:

```bash
# Step 1 — Verify ontology + shapes are internally consistent
python3 2_ETL/aiu_validation.py

# Step 2 — Verify graph structure supports analytics queries
python3 2_ETL/aiu_analytics_check.py

# Step 3 — Run the ETL (requires both API keys + source CSV)
python3 2_ETL/etl.py --case tiny    # 15 rows, auto-named pilot_N_15.ttl
python3 2_ETL/etl.py --case mid     # 25% of rows
python3 2_ETL/etl.py --case full    # all rows
python3 2_ETL/etl.py --n 50         # exact row count (random_state=42)

# Performance / resilience options
python3 2_ETL/etl.py --case full --concurrent 5 --checkpoint-interval 50
python3 2_ETL/etl.py --case full --no-validate   # skip SHACL (faster for large runs)
python3 2_ETL/etl.py --resume path/to/run.checkpoint.jsonl  # resume a crashed run

# Prototype (original single-model, 15-row run)
python3 2_ETL/etl_pilot.py
```

All three scripts resolve paths relative to `__file__`, so the working directory does not matter.

---

## Output

`etl.py` produces up to three outputs:

**`pilot_N_15.ttl` / `run_mid_*.ttl` / `full_2024_*.ttl`** — RDF graph in Turtle format, written to this directory. Contains `UseCaseRecord`, `AIUseCasePlan`, and `AIUseCaseProcess` nodes with inline `# prefLabel` comments on all `aiu:BG_*` IRIs for human readability.

**`disagreements_{case}_{timestamp}.jsonl`** — Created when Sonnet and GPT disagree on at least one record. Each line is a JSON record with: `use_case_name`, `sonnet_goals`, `gpt_goals`, `intersection_goals`, `final_goals`, `disagreement_pct`, `prompt` (catalog text stripped to keep file size manageable). Flushed to disk every `--checkpoint-interval` rows.

**`run.checkpoint.jsonl`** — Written every N rows (default 50). Stores output paths plus per-row goal assignments. Pass to `--resume` to continue a crashed run from the last checkpoint.

**`etl_{stem}_results.md`** — Auto-generated markdown report co-located with the TTL: selected records table, goal assignments per use case, top goals by frequency, dual-LLM agreement stats, SHACL violations.

**Console report** — printed to stdout:
- Row selection summary (agency, stage, impact type per record)
- Per-record goal table with agreement flag and ETA
- Dual-LLM agreement statistics (agreed, intersection, union fallback counts)
- SHACL conformance result and violation breakdown
- Triple counts, goal coverage, and summary block

Results from pilot 1 (etl_pilot.py) are archived in [`etl_pilot_1_results.md`](etl_pilot_1_results.md).

---

## Validation Script Reference

`aiu_validation.py` runs five checks. Expected output on a clean ontology/shapes pair:

```
Test                                     Conforms   Viol   Warn  Notes
------------------------------------------------------------------------------------------
A — COTS-only                                True      0      0  FullRecord/Risk/Rights silent
B — Full/Neither/Initiated                  False      1      0  hasInitiationTime required
C — Rights/ImplAssess COMPLETE               True      0      0  All shapes fire and pass
D — Rights/ImplAssess MISSING               False     17      0  Expected: all conditional fields absent
E — Safety/ImplAssess no rights              True      0      0  RightsRecordShape must NOT fire
```

Test B's single violation and Test D's 17 violations are **expected and correct** — they confirm the gate logic fires as designed. Run this script after any edit to `aiu_ontology_ver1.ttl` or `aiu_shapes.ttl` before running the ETL.

---

## Files in This Directory

| File | Format | Role |
|---|---|---|
| `etl.py` | Python | Production ETL — `--case/--n`, dual-LLM (Sonnet+GPT) tagging, intersection resolution, checkpoint/resume, concurrent rows, JSONL disagreement log |
| `etl_pilot.py` | Python | Original prototype — 15-row pilot, single Haiku model |
| `aiu_validation.py` | Python | 5-point ontology + shapes regression test; run after any TTL edit |
| `aiu_analytics_check.py` | Python | 4-scenario graph analytics readiness check |
| `etl_improvements.md` | Markdown | Changelog from `etl_pilot.py` → `etl.py`: design decisions and rationale |
| `etl_pilot_guide.md` | Markdown | Detailed walkthrough of `etl_pilot.py`: row selection logic, bug log, scaling guide |
| `etl_pilot_1_results.md` | Markdown | Pilot 1 results: selected records, SHACL violations, goal assignments, quality assessment |
| `pilot_1_15.ttl` | Turtle (RDF) | Output graph from pilot 1 (15 records, 2024 inventory, 413 triples) |
| `pilot_2_15.ttl` | Turtle (RDF) | Output graph from pilot 2 (15 records, dual-LLM Sonnet+GPT, Opus referee, 402 triples) |
| `pilot_3_15.ttl` | Turtle (RDF) | Output graph from pilot 3 (15 records, Sonnet+GPT, Opus referee, 400 triples) |
| `pilot_4_15.ttl` | Turtle (RDF) | Output graph from pilot 4 (15 records, Sonnet+GPT, Opus referee, 390 triples) |
| `pilot_N_15.ttl` | Turtle (RDF) | Output graphs from subsequent `etl.py --case tiny` runs (auto-numbered) |
| `etl_pilot_2_15_results.md` | Markdown | Pilot 2 results: dual-LLM agreement stats, goal assignments, SHACL violations |
| `etl_pilot_3_15_results.md` | Markdown | Pilot 3 results: Sonnet+GPT+Opus, goal assignments, SHACL violations |
| `etl_pilot_4_15_results.md` | Markdown | Pilot 4 results: intersection resolution (no Opus), goal assignments, SHACL violations |
| `disagreements_*.jsonl` | JSONL | Per-run disagreement log: sonnet_goals, gpt_goals, intersection_goals, final_goals, disagreement_pct |

---

## Scaling to the Full 2,133-Row or more Inventory

Use `python3 2_ETL/etl.py --case full` to run the entire inventory. `etl.py` includes
built-in resilience features for large runs:

1. **Concurrent processing** (`--concurrent N`, default 5) — processes N rows simultaneously with `ThreadPoolExecutor`; Sonnet and GPT are called in parallel within each row.
2. **Tenacity retry** — `_tag_sonnet` and `_tag_gpt` automatically retry on `APIConnectionError` / `RateLimitError` with exponential backoff (4–60 s, up to 5 attempts).
3. **Checkpoint/resume** (`--checkpoint-interval N`, default 50) — TTL and disagreement log are flushed to disk every N rows; a crashed run resumes with `--resume path/to/run.checkpoint.jsonl`.
4. **Skip SHACL for speed** (`--no-validate`) — run SHACL separately as a post-processing step once ETL completes.

pySHACL with `advanced=True` (SPARQL targets) runs at ~2–5 s per 200-row chunk on a laptop.

```python
import pyshacl
from rdflib import Graph

ont_g = Graph()
ont_g.parse("1_Ontology/aiu_ontology_ver1.ttl", format="turtle")

data_g = Graph()
data_g.parse("2_ETL/pilot_1_15.ttl", format="turtle")  # swap for full output

conforms, results_g, results_text = pyshacl.validate(
    data_g,
    shacl_graph="1_Ontology/aiu_shapes.ttl",
    ont_graph=ont_g,
    inference="none",      # BFO/CCO/IAO not locally available
    allow_warnings=True,   # PROV warnings do not block conforms=True
    abort_on_first=False,
    advanced=True,         # required for sh:SPARQLTarget gate logic
)
```

---

## Related Documentation

| Resource | Location |
|---|---|
| Ontology design, SHACL methodology, field mapping | [`../1_Ontology/README.md`](../1_Ontology/README.md) |
| Authoritative column → predicate mapping (67 fields) | [`../1_Ontology/aiu_inventory_field_mapping.md`](../1_Ontology/aiu_inventory_field_mapping.md) |
| Business goal taxonomy (10 clusters, 39 sub-goals) | [`../1_Ontology/taxonomy_bizGoals.md`](../1_Ontology/taxonomy_bizGoals.md) |
| ETL improvements changelog | [`etl_improvements.md`](etl_improvements.md) |
| ETL pilot detailed guide | [`etl_pilot_guide.md`](etl_pilot_guide.md) |
| Pilot 1 results | [`etl_pilot_1_results.md`](etl_pilot_1_results.md) |
| Pilot 2 results | [`etl_pilot_2_15_results.md`](etl_pilot_2_15_results.md) |
| Pilot 3 results | [`etl_pilot_3_15_results.md`](etl_pilot_3_15_results.md) |
| Pilot 4 results | [`etl_pilot_4_15_results.md`](etl_pilot_4_15_results.md) |
