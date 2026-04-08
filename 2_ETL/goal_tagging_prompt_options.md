# Goal Tagging Prompt Design Options

This document records three prompt design options for improving LLM goal classification
agreement in `etl.py`. The root problem is that LLMs default to **recognition** (scanning
the catalog for what feels right) rather than **evaluation** (systematically checking each
goal against the use case). These options force evaluation.

Identified during pilot 6/7 analysis (2026-04-07).

---

## Background: Why Agreement Is Low

The current prompt presents the use case text and a 38-goal catalog, then asks for a
JSON list. The model forms an initial interpretation of the use case and scans the catalog
for confirming matches — it does not check each goal systematically.

Consequences observed:
- BG_4_1 ("Process efficiency") dominates (9/15 records) because it matches almost
  any productivity AI tool
- GPT-5.4-mini returns more goals than Sonnet in 10/14 disagreements; Sonnet is never
  a superset of GPT — indicating a systematic asymmetric over-selection by GPT
- BG_7_1 and BG_4_3 are over-applied by GPT (4× each) to records where they are not
  the primary mission
- Parse fallbacks increase when the cap is tightened, suggesting GPT generates plausible
  IDs from its own knowledge rather than strictly selecting from the catalog

---

## Option A: Inline Chain-of-Thought (single call, structured reasoning)

Require the model to articulate themes and evaluate all 38 goals before committing.

### Prompt template

```
Use Case: {name}
Purpose/Benefits: {purpose[:1200]}
AI Outputs: {outputs[:300]}
Topic Area: {topic}
Development Stage: {stage}

Business Goal Catalog:
{GOAL_CATALOG}

Instructions:
Step 1 — Read the use case above and list the 3–5 core things this system does
         or achieves (one line each).
Step 2 — For each goal in the catalog, decide: does it match one of those core
         things? Write a one-line verdict per goal: "aiu:BG_X_Y: yes/no — reason".
Step 3 — From the "yes" goals, select the 1–3 strongest matches.

Respond in this exact format:
THEMES:
- ...

EVALUATION:
aiu:BG_X_Y: yes/no — reason
...

GOALS: {"goals": ["aiu:BG_X_Y", ...]}
```

### Parsing

Extract the `GOALS:` line from the response and parse the JSON from it.

### Parameters

- `max_tokens`: ~1500 (38 evaluation lines × ~15 tokens + themes + JSON)
- Calls per record: 3 (Sonnet + GPT + Opus if disagreement) — same as current

### Trade-offs

| Pro | Con |
|---|---|
| Forces both models through all 38 goals | Longest response; highest token cost |
| Full evaluation trail in JSONL log | Parsing more complex (extract GOALS: line) |
| Single call per model | 38-goal evaluation may still anchor on early entries |

---

## Option B: Cluster-First Filtering (single call, two-stage within one prompt)

Exploit the 10-cluster structure of the taxonomy. The model first identifies which
clusters are relevant (coarse filter), then evaluates sub-goals only within those
clusters (fine-grained evaluation). Reduces evaluation scope from 38 to ~8–12 goals.

### Prompt template

```
Use Case: {name}
Purpose/Benefits: {purpose[:1200]}
AI Outputs: {outputs[:300]}
Topic Area: {topic}
Development Stage: {stage}

Goal Clusters (coarse level):
1. Strategic Direction    — mission alignment, strategy, portfolio, business model
2. Market and Customer    — market understanding, customer acquisition, CX, retention
3. Product and Innovation — product development, R&D speed, quality, innovation
4. Operations             — process efficiency, supply chain, controls, scaling
5. Financial              — revenue, cost, risk, capital, reporting
6. Human Capital          — workforce, talent, learning, culture
7. Governance             — regulatory compliance, governance, ethics, transparency
8. Data and Technology    — data quality, infrastructure, cybersecurity, AI/ML ops
9. Service and Delivery   — service delivery, accessibility, citizen/stakeholder CX
10. Risk and Safety       — product safety, crisis management, resilience

Step 1: Which 1–3 clusters best match this use case? List their numbers.

Full Goal Catalog (evaluate only goals within your chosen clusters):
{GOAL_CATALOG}

Step 2: For each goal within your chosen clusters, write one line:
  aiu:BG_X_Y: yes/no — one-sentence reason

Step 3: From the "yes" goals, select the 1–3 strongest. Be conservative —
  if uncertain, exclude.

Respond in this exact format:
CLUSTERS: [1, 4, 8]
EVALUATION:
aiu:BG_X_Y: yes — reason
aiu:BG_X_Y: no — reason
GOALS: {"goals": ["aiu:BG_X_Y", ...]}
```

### Parsing

Extract the `GOALS:` line and parse JSON from it.

### Parameters

- `max_tokens`: ~1024
- Calls per record: 3 (same as current)

### Trade-offs

| Pro | Con |
|---|---|
| Reduces evaluation scope from 38 to ~8–12 goals | Cluster mis-selection hard-excludes correct sub-goals |
| Cluster selection is a strong forcing function | More complex to parse |
| Lower token cost than Option A | Adds one layer of reasoning that can fail |
| Single call per model | |

### Risk mitigation

Log the selected clusters in the JSONL disagreement record so post-run audits
can identify cluster-level mis-selections.

---

## Option C: Two-Call Pipeline (separate theme extraction + goal matching)

Split into two sequential API calls per model. Call 1 characterises the use case;
Call 2 matches those characterisations against the catalog.

### Call 1 — Theme extraction

```
Analyze this federal AI use case and identify its core business functions.

Use Case: {name}
Purpose/Benefits: {purpose[:1200]}
AI Outputs: {outputs[:300]}
Topic Area: {topic}
Development Stage: {stage}

List 3–5 specific business functions this system performs (not what technology
it uses — what business outcome it achieves). Be concrete and precise.
Respond as JSON: {"themes": ["...", "...", "..."]}
```

### Call 2 — Goal matching (fed themes from Call 1)

```
Match these business functions to the goal catalog below.

Functions this use case performs:
{themes from Call 1}

For each goal in the catalog, answer: does any of the functions above directly
correspond to this goal?
aiu:BG_X_Y: yes/no — one-line reason

Then select the 1–3 strongest matching goals.

{GOAL_CATALOG}

Respond:
EVALUATION:
aiu:BG_X_Y: yes/no — reason
GOALS: {"goals": [...]}
```

### Parameters

- `max_tokens`: Call 1 ~128, Call 2 ~1024
- Calls per record: 5 (2× Sonnet + 2× GPT + Opus if disagreement)

### Trade-offs

| Pro | Con |
|---|---|
| Theme extraction eliminates catalog anchoring | Doubles API calls and cost |
| Themes are loggable and reusable | Theme quality is a new failure point |
| Highest expected agreement (both models evaluate same themes in Call 2) | Adds latency |
| Cleanest separation of concerns | |

---

## Summary Comparison

| Dimension | Option A | Option B | Option C |
|---|---|---|---|
| Calls per record | 3 | 3 | 5 |
| Max tokens per call | ~1500 | ~1024 | ~128 + ~1024 |
| Goals evaluated | All 38 | ~8–12 (within clusters) | All 38 |
| Catalog anchoring risk | Medium (38 goals in sequence) | Low (cluster pre-filter) | Low (themes first) |
| Failure modes | Long response may drift | Cluster mis-selection silently excludes | Bad themes propagate |
| Audit trail | Full per-goal reasoning | Cluster + sub-goal reasoning | Themes + per-goal reasoning |
| Implementation complexity | Low | Medium | High |

**Recommended progression:** Implement B first (cost-efficient, strong forcing function).
If cluster mis-selection proves to be a problem, escalate to C.
