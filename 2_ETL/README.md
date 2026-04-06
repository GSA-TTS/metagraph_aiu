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
3. etl_pilot.py            ← run the ETL; produces RDF output + SHACL report
```
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
/tmp/inventory_2024.csv  ──────► etl_pilot.py
  (source CSV, placed                  │
   manually before run)                ▼
                               pilot_1_15.ttl  (RDF output, written here)
                               + console report
```

The ETL reads ontology files from `../1_Ontology/` using paths relative to `__file__`. The source CSV must be placed at `/tmp/inventory_2024.csv` before running. The RDF output is written to `pilot_1_15.ttl` in this directory.

---

## ETL Pipeline Steps

`etl_pilot.py` executes six steps end-to-end:

| Step | What it does |
|---|---|
| 1 | Loads `aiu_ontology_ver1.ttl`, `aiu_shapes.ttl`, and `taxonomy_bizGoals.md` into memory; builds SKOS concept lookup tables |
| 2 | Selects 15 representative rows from the CSV using a diversity-aware algorithm (see Row Selection below) |
| 3 | Converts each CSV row to RDF triples using the ontology property mapping from `aiu_inventory_field_mapping.md` |
| 4 | Calls Claude Haiku once per use case to assign 0–5 business goals from the 39-sub-goal taxonomy; writes `aiu:hasBusinessGoal` triples to `AIUseCasePlan` nodes |
| 5 | Runs `pyshacl.validate()` with `advanced=True` (SPARQL targets) and `inference="none"`; reports violations per record |
| 6 | Prints summary statistics: triple counts, goal coverage, SHACL conformance, top violations |

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

Each use case is classified against the 39-sub-goal business goal taxonomy using LLM. The prompt supplies the use case name, purpose/benefits text, AI outputs, topic area, and development stage alongside the full goal catalog. The model returns JSON `{"goals": ["aiu:BG_X_Y", ...]}`. Returned IDs are whitelist-filtered against the ontology's `GOAL_ID_SET` and capped at 5 per record, preventing hallucinated IRIs.

The LLM approach is necessary because the taxonomy uses business-management vocabulary ("process efficiency", "regulatory compliance") while agencies may write in government/technical language ("radiation portal monitors", "anomaly detection at land border ports").

---

## Prerequisites

**Python:** 3.10+

**Dependencies:**

```bash
pip install rdflib pyshacl anthropic pandas packaging
```

**API key** (required for goal tagging in `etl_pilot.py`; not needed for validation scripts):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
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

# Step 3 — Run the ETL pilot (requires API key + source CSV)
python3 2_ETL/etl_pilot.py
```

All three scripts resolve paths relative to `__file__`, so the working directory does not matter.

---

## Output

`etl_pilot.py` produces two outputs:

**`pilot_1_15.ttl`** — RDF graph in Turtle format serialised to this directory. Contains:
- 15 `UseCaseRecord`, 15 `AIUseCasePlan`, 15 `AIUseCaseProcess` nodes
- 413 triples (353 ETL-mapped fields + 60 `hasBusinessGoal` triples)
- Inline `# prefLabel` comments on all `aiu:BG_*` IRIs for human readability

**Console report** — printed to stdout:
- Row selection summary (agency, stage, impact type per record)
- Per-record goal assignment table
- SHACL conformance result and violation breakdown
- Triple counts and goal coverage statistics

Results from pilot 1 are archived in [`etl_pilot_1_results.md`](etl_pilot_1_results.md).

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
| `etl_pilot.py` | Python | Main ETL pipeline — 6-step CSV→RDF conversion with LLM goal tagging |
| `aiu_validation.py` | Python | 5-point ontology + shapes regression test; run after any TTL edit |
| `aiu_analytics_check.py` | Python | 4-scenario graph analytics readiness check |
| `etl_pilot_guide.md` | Markdown | Detailed walkthrough of `etl_pilot.py`: row selection logic, bug log, scaling guide |
| `etl_pilot_1_results.md` | Markdown | Pilot 1 results: selected records, SHACL violations, goal assignments, quality assessment |
| `pilot_1_15.ttl` | Turtle (RDF) | Output graph from pilot 1 (15 records, 2024 inventory, 413 triples) |

---

## Scaling to the Full 2,133-Row or more Inventory

The pilot validates the complete pipeline on a representative sample. To run at full scale:

1. Use the same `etl_pilot.py` structure but remove the 15-row selection step and iterate over all rows.
2. Batch rows in chunks of ~200; accumulate triples into one graph; validate once at the end.
3. For LLM tagging, batch 3–5 use cases per API call and wrap with `tenacity` retry for rate-limit resilience.
4. pySHACL with `advanced=True` (SPARQL targets) runs at ~2–5 s per 200-row chunk on a laptop.

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
| ETL pilot detailed guide | [`etl_pilot_guide.md`](etl_pilot_guide.md) |
| Pilot 1 results | [`etl_pilot_1_results.md`](etl_pilot_1_results.md) |
