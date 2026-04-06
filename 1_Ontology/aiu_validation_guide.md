# AIU Ontology & Shapes Validation Script

**File:** `aiu_validation.py`  
**Depends on:** `aiu_ontology_ver1.ttl`, `aiu_shapes.ttl`  
**Runtime:** Python 3.10+, rdflib ≥ 7.0, pySHACL ≥ 0.14

---

## Purpose

`aiu_validation.py` is a self-contained consistency checker for the Federal AI Use Case ontology/shapes pair. It performs five systematic checks:

| Point | What it checks |
|---|---|
| 1 | Every IRI in every `sh:in` list resolves as a `skos:inScheme` member of the correct SKOS scheme in the ontology — no orphans, no missing concepts, no duplicates |
| 2 | `sh:declare` / `sh:prefixes` wiring is correct for pySHACL and Apache Jena; all SPARQL-based shapes and targets reference the shapes ontology node |
| 3 | Documents the intentional discrepancy between OWL `someValuesFrom` restrictions on PROV properties and their soft SHACL `sh:Warning` counterparts |
| 4 | Confirms `aiu:TimeInstant` subclasses `bfo:0000203` only (no temporal-region conflict), and that the placeholder shape has no premature literal constraints |
| 5 | Runs pySHACL against five synthetic RDF test graphs to verify gate logic: COTS-only records, full records, rights-impacting records, safety-only records |

Run it after any edit to either TTL file to catch regressions before loading data.

---

## Installation

```bash
pip install rdflib pyshacl packaging
```

Tested with rdflib 7.6.0 and pySHACL 0.31.0.

---

## Usage

```bash
cd guide/
python3 aiu_validation.py
```

The script hard-codes paths relative to the `guide/` directory (`BASE = Path(...)/guide`). Run it from any working directory as long as the `guide/` folder is intact.

Expected runtime: 10–30 seconds (pySHACL runs five separate validation passes).

---

## Expected Output Summary

A clean run (no regressions) should end with:

```
Test                                     Conforms   Viol   Warn  Notes
------------------------------------------------------------------------------------------
A — COTS-only                                True      0      0  Only core shapes; ...
B — Full/Neither/Initiated                  False      1      0  FullRecord fires, ...
C — Rights/ImplAssess COMPLETE               True      0      0  All shapes fire and pass
D — Rights/ImplAssess MISSING               False     17      0  Multiple Violations ...
E — Safety/ImplAssess no rights              True      0      0  RightsRecordShape must NOT fire
```

Test B's single violation (`hasInitiationTime` required for non-Retired stages) is **expected and correct** — a full record at `DS_Initiated` is not Retired and legitimately needs a date-initiated value. Test D's 17 violations are also expected (all conditional fields are intentionally absent).

---

## What Each Test Proves

### Test A — COTS-only record
- `CAI_Scheduling`, stage `DS_Initiated`, impact `IT_Neither`
- Validates that `FullRecordProcessShape`, `RiskRecordShape`, and `RightsRecordShape` are **silent** for COTS records (gate field ≠ `CAI_NoneOfTheAbove`).

### Test B — Full record, Neither/Initiated
- `CAI_NoneOfTheAbove`, stage `DS_Initiated`, impact `IT_Neither`
- `FullRecordProcessShape` fires. Only the non-Retired `hasInitiationTime` SPARQL guard triggers; AcqDev+/ImplAssess+ guards do not.
- Risk and rights shapes are silent (impact = Neither).

### Test C — Rights-impacting full record (complete)
- `CAI_NoneOfTheAbove`, stage `DS_ImplAssess`, impact `IT_Rights`
- All stage-conditional full-record fields provided; all risk fields provided; all rights fields provided.
- Verifies `conforms=True` when the record is fully compliant.

### Test D — Rights-impacting full record (fields missing)
- Same gate/stage/impact as Test C, but no conditional fields added.
- Expected 17 violations: 4 from `RiskRecordShape`, 2 from `RightsRecordShape`, 11 from `FullRecordProcessShape` SPARQL constraints.
- Verifies that the shapes actually fire and catch missing data.

### Test E — Safety-only full record (no rights fields)
- `CAI_NoneOfTheAbove`, stage `DS_ImplAssess`, impact `IT_Safety`
- All risk fields provided; `hasAppealProcess` and `hasOptOut` deliberately absent.
- Verifies that `RightsRecordShape` (which targets only `IT_Rights`/`IT_Both`) does **not** fire for safety-only records.

---

## Interpreting Failures

### Point 1 failure
An IRI appears in `sh:in` but not in `skos:inScheme` (or vice versa). Causes: a concept was added to the ontology but the shapes file was not updated, or a typo in an IRI.

### Point 2 failure
A `sh:prefixes` reference points to an unexpected IRI (e.g., a stale `aiu:SPARQLPrefixes` node). The SPARQL constraint or target will silently fail to resolve prefixes at runtime, producing incorrect validation results. Fix: update the reference to `<https://example.org/ai-usecase-shapes>`.

### Point 3 observation
If PROV enrichment has been completed for the loaded dataset, consider promoting the two PROV property shapes from `sh:Warning` + `sh:minCount 0` to `sh:minCount 1` + `sh:severity sh:Warning` (soft absent-warning) or `sh:Violation` (hard error). The script documents this transition path in its output.

### Point 4 failure
`aiu:TimeInstant` no longer subclasses `bfo:0000203`, or it also subclasses `bfo:0000008` (temporal region — a BFO conflict). Fix in the ontology before reloading.

### Point 5 unexpected violation count
- Test A violations > 0: a `sh:targetClass` shape has an incorrect target, or a SPARQL target is selecting COTS records when it should not.
- Test C violations > 0: a shape fires a false positive on a complete record; check the SPARQL guard conditions.
- Test E violations related to `hasAppealProcess`/`hasOptOut`: `RightsRecordShape` SPARQL target is selecting safety-only records — check the `FILTER (?impact IN (aiu:IT_Rights, aiu:IT_Both))` condition.

---

## Reusing the pySHACL Invocation

To validate real inventory data against the shapes:

```python
import pyshacl
from rdflib import Graph

ont_g = Graph()
ont_g.parse("guide/aiu_ontology_ver1.ttl", format="turtle")

data_g = Graph()
data_g.parse("your_data.ttl", format="turtle")   # or .json-ld, etc.

conforms, results_g, results_text = pyshacl.validate(
    data_g,
    shacl_graph="guide/aiu_shapes.ttl",
    ont_graph=ont_g,
    inference="none",       # avoid unresolvable external OWL imports
    allow_warnings=True,    # PROV warnings don't block conforms=True
    abort_on_first=False,
    advanced=True,          # required for sh:SPARQLTarget
)

print(conforms)
print(results_text)
```

`inference="none"` is important: the ontology imports BFO/CCO/IAO/PROV-O which are not locally available, so OWL inference must be disabled to avoid import-resolution errors. Pass the ontology as `ont_graph` for class/property metadata only.

---

## Related Files

| File | Role |
|---|---|
| `aiu_ontology_ver1.ttl` | OWL ontology — the source of truth for all classes, properties, and SKOS concepts |
| `aiu_shapes.ttl` | SHACL shapes — validated by Point 2 prefix checks and Point 5 gate tests |
| `aiu_inventory_field_mapping.md` | Maps all 67 inventory fields to ontology predicates; the authoritative spec for both the shapes file and the ingest pipeline |
| `draft1_ontology_documentation.md` | Narrative documentation of the ontology design decisions |
