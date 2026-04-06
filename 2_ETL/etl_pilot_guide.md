# ETL Pilot — 15-Row End-to-End Walkthrough

**Script:** `etl_pilot.py`  
**Inputs:** `aiu_ontology_ver1.ttl`, `aiu_shapes.ttl`, `taxonomy_bizGoals.md`, 2024 inventory CSV  
**Outputs:** `pilot_1_15.ttl`, console report  
**Runtime:** ~60–90 seconds (15 LLM API calls + pySHACL validation pass)  
**Requires:** `ANTHROPIC_API_KEY` environment variable or any compatible LLM Api key

---

## Purpose

`etl_pilot.py` is a runnable proof-of-concept ETL that validates the complete pipeline before processing all pilot rows. It performs six steps:

| Step | What it does |
|------|-------------|
| 1 | Loads ontology, shapes, and business-goal taxonomy into memory |
| 2 | Selects 15 representative rows from the CSV (diversity-aware) |
| 3 | Converts each CSV row to RDF using the ontology property mapping |
| 4 | Tags each use case with business goals via Claude Haiku LLM |
| 5 | Runs pySHACL validation and reports violations per record |
| 6 | Prints summary statistics |

---

## Installation

```bash
pip install rdflib pyshacl anthropic pandas
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

```bash
cd guide/
python3 etl_pilot.py
```

Paths are hard-coded as absolute paths to the `guide/` directory. Edit `GUIDE`, `CSV_PATH`, and `OUT_PATH` at the top of the script if needed.

---

## Row Selection Logic

The pilot selects 15 rows to maximise coverage of the shapes' gate conditions:

| Slot | Count | Criteria |
|------|-------|----------|
| Rights-impacting full records | 3+ | `commercial_ai = None of the Above`, impact ∈ {Rights, Both} |
| Safety-impacting full records | 3+ | impact ∈ {Safety, Both} |
| HISP-supporting full records | 3+ | `hisp_supp = Yes` |
| Neither-impact full records | filler to 10 | PII diversity preferred |
| COTS records | 5 | `commercial_ai ≠ None of the Above` |

Greedy agency+topic diversity: rows are sorted so that no two consecutive selections share the same `agency|topic_area|dev_stage` key.

---

## Pilot Run Results

Results for the 2024 inventory 15-record run are in [`etl_pilot_1_results.md`](etl_pilot_1_results.md).

---

## Known ETL Bugs Fixed During Pilot

| Bug | Fix |
|-----|-----|
| Taxonomy regex parser: `##\s` lookahead matched inside `### N.M` headings, returning 0 sub-goals | Replaced with a line-by-line FSM parser |
| `lookup()` exact-match failed for `int_review`/`data_docs` where CSV appends long explanations after the concept label | Added prefix-match fallback |
| Seven column indices wrong: `impact_assess` (45), `real_test` (46), `key_risks` (47), `monitor` (49), `auto_impact` (50), `appeal` (58), `opt_out` (60) | Corrected CI dictionary |
| `CodeAccess` values use "Yes/No – …" CSV prefix not found in SKOS labels | Added `CA_ALIASES` dictionary |
| `to_bool()` only matched exact "yes"/"no"; CSV uses "No - Some individual decisions…" format | Extended to handle first-word prefix |
| Goal tagging: TF-IDF cosine similarity across mismatched vocabularies → 40% coverage | Replaced with Claude Haiku LLM → 100% coverage |

These fixes reduced SHACL violations 36 → 18 (all remaining are real data gaps) and raised goal tagging coverage from 40% to 100%.

---

## Extending to the Full 2133-Row Inventory

```python
import pyshacl
from rdflib import Graph

ont_g = Graph()
ont_g.parse("guide/aiu_ontology_ver1.ttl", format="turtle")

data_g = Graph()
data_g.parse("guide/pilot_1_15.ttl", format="turtle")   # swap for full output

conforms, results_g, results_text = pyshacl.validate(
    data_g,
    shacl_graph="guide/aiu_shapes.ttl",
    ont_graph=ont_g,
    inference="none",
    allow_warnings=True,
    abort_on_first=False,
    advanced=True,
)
```

To scale, batch the 2133 rows in chunks of ~200, accumulate into one graph, then validate once. pySHACL with `advanced=True` (SPARQL targets) is the bottleneck at ~2–5 s per 200-row chunk on a laptop.

---

## Related Files

| File | Role |
|------|------|
| `aiu_ontology_ver1.ttl` | OWL ontology — source of SKOS concept maps |
| `aiu_shapes.ttl` | SHACL shapes — gate logic for validation |
| `taxonomy_bizGoals.md` | 10 clusters, 39 sub-goals with seed examples |
| `aiu_inventory_field_mapping.md` | Authoritative column → property mapping |
| `pilot_1_15.ttl` | Output RDF from pilot 1 (15 records, 2024 inventory) |
| `etl_pilot_1_results.md` | Selected records, SHACL violations, and goal tagging results for pilot 1 |
| `aiu_validation.py` | Synthetic SHACL unit tests (run after ontology/shapes edits) |
| `aiu_analytics_check.py` | Analytics-readiness check for graph algorithm queries |
