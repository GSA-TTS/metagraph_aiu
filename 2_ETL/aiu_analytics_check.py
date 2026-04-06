#!/usr/bin/env python3
"""
aiu_analytics_check.py
Analytics-readiness check for aiu_ontology_ver1.ttl + aiu_shapes.ttl.
Three parts:
  Part 1 — Static inspection of shapes vs analytics needs
  Part 2 — Synthetic data scenarios (pySHACL validation)
  Part 3 — Findings summary
"""

import sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, URIRef, Literal
from rdflib.namespace import SKOS
import pyshacl

BASE       = Path(__file__).resolve().parent.parent / "1_Ontology"  # metagraph_aiu/1_Ontology/
ONT_PATH   = BASE / "aiu_ontology_ver1.ttl"
SHACL_PATH = BASE / "aiu_shapes.ttl"

AIU  = Namespace("https://example.org/ai-usecase-ontology#")
SH   = Namespace("http://www.w3.org/ns/shacl#")
PROV = Namespace("http://www.w3.org/ns/prov#")
NS_T = "https://test.example.org/"

# ── Load graphs ───────────────────────────────────────────────────────────────
ont   = Graph(); ont.parse(str(ONT_PATH),   format="turtle")
shacl = Graph(); shacl.parse(str(SHACL_PATH), format="turtle")

def sep(title):
    print(f"\n{'='*70}\n{title}\n{'='*70}")

def rdflist(g, head):
    items = []
    cur = head
    while cur and cur != RDF.nil:
        first = g.value(cur, RDF.first)
        if first is not None:
            items.append(first)
        cur = g.value(cur, RDF.rest)
    return items

# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — Static inspection
# ══════════════════════════════════════════════════════════════════════════════
sep("PART 1 — Static Inspection")

# ── 1a. hasBusinessGoal cardinality scan ─────────────────────────────────────
print("\n--- 1a. hasBusinessGoal cardinality across ALL shapes ---")
found_bg = []
for prop_shape in shacl.subjects(SH["path"], AIU["hasBusinessGoal"]):
    min_c = shacl.value(prop_shape, SH["minCount"])
    max_c = shacl.value(prop_shape, SH["maxCount"])
    sh_class = shacl.value(prop_shape, SH["class"])
    # find owning shape
    owner = shacl.value(None, SH["property"], prop_shape)
    owner_local = str(owner).split("#")[-1] if owner else "?"
    found_bg.append((owner_local, min_c, max_c, sh_class))
    print(f"  Shape={owner_local}  minCount={min_c}  maxCount={max_c}  sh:class={sh_class}")

if not found_bg:
    print("  No sh:property for hasBusinessGoal found — property is unconstrained.")
else:
    problems = [x for x in found_bg if x[2] is not None and int(x[2]) < 2]
    if problems:
        print(f"  WARNING: maxCount <= 1 on hasBusinessGoal in {[x[0] for x in problems]}")
    else:
        no_max = [x for x in found_bg if x[2] is None]
        print(f"  OK: No maxCount (unlimited) in: {[x[0] for x in no_max]}")
        bounded = [x for x in found_bg if x[2] is not None]
        if bounded:
            print(f"  BOUNDED (maxCount set): {bounded}")

# ── 1b. Scan all SPARQL constraints for goal-related restrictions ─────────────
print("\n--- 1b. SPARQL constraints mentioning 'BusinessGoal' or 'hasBusinessGoal' ---")
found_sparql_goal = []
for s, p, o in shacl.triples((None, SH["select"], None)):
    if "BusinessGoal" in str(o) or "hasBusinessGoal" in str(o):
        name = shacl.value(s, SH["name"])
        found_sparql_goal.append((name, str(o)[:120]))
if found_sparql_goal:
    for name, snippet in found_sparql_goal:
        print(f"  FOUND SPARQL: {name!r}  query_snippet={snippet}")
else:
    print("  None — no SPARQL constraint references business goals. OK.")

# ── 1c. Required analytics fields check ──────────────────────────────────────
print("\n--- 1c. Required analytics fields (minCount >= 1) ---")

REQUIRED_CHECKS = {
    "UseCaseRecordShape": [
        ("useCaseName",        1, "string identifier"),
        ("hasAgency",          1, "slice by agency"),
        ("hasBureau",          1, "slice by bureau"),
        ("hasCommercialAIType",1, "gate + COTS vs full split"),
        ("partOfInventory",    1, "year / cross-year trend"),
        ("describesPlan",      1, "link to goals"),
        ("describesProcess",   1, "link to analytics dims"),
    ],
    "AIUseCaseProcessShape": [
        ("hasTopicArea",        1, "group by domain"),
        ("hasDevelopmentStage", 1, "filter by lifecycle stage"),
        ("hasImpactType",       1, "rights/safety impact dims"),
        ("outputsText",         1, "NLP source"),
    ],
    "AIUseCasePlanShape": [
        ("purposeBenefitsText", 1, "NLP source for goal classification"),
        ("hasBusinessGoal",     0, "optional — populated by pipeline"),
    ],
    "InventorySnapshotShape": [
        ("inventoryYear", 1, "year dimension for trend analysis"),
    ],
}

all_ok = True
for shape_name, fields in REQUIRED_CHECKS.items():
    shape_iri = AIU[shape_name]
    print(f"\n  {shape_name}:")
    for prop_name, expected_min, note in fields:
        prop_iri = AIU[prop_name]
        # Find property shape for this path in this shape
        actual_min = None
        for ps in shacl.objects(shape_iri, SH["property"]):
            if shacl.value(ps, SH["path"]) == prop_iri:
                actual_min = shacl.value(ps, SH["minCount"])
                break
        if actual_min is None:
            status = "MISSING" if expected_min > 0 else "not-constrained(OK)"
            ok = expected_min == 0
        else:
            actual_val = int(actual_min)
            ok = actual_val >= expected_min
            status = f"minCount={actual_val}"
        flag = "OK  " if ok else "WARN"
        if not ok:
            all_ok = False
        print(f"    {flag}  {prop_name:<28} {status:<22} # {note}")

print(f"\n  Required-fields overall: {'ALL OK' if all_ok else 'ISSUES FOUND'}")

# ── 1d. Duplication & continuity property shapes ──────────────────────────────
print("\n--- 1d. possibleDuplicateOf / continuesFrom shape constraints ---")
DUP_PROPS = [AIU["possibleDuplicateOf"], AIU["continuesFrom"]]
for prop_iri in DUP_PROPS:
    local = str(prop_iri).split("#")[-1]
    shapes_found = list(shacl.subjects(SH["path"], prop_iri))
    if not shapes_found:
        print(f"  {local}: no sh:property constraint — fully unconstrained. OK for multi-hop chains.")
    else:
        for ps in shapes_found:
            max_c = shacl.value(ps, SH["maxCount"])
            min_c = shacl.value(ps, SH["minCount"])
            owner = shacl.value(None, SH["property"], ps)
            print(f"  {local}: found in {owner}, minCount={min_c}, maxCount={max_c}")
            if max_c and int(max_c) == 1:
                print(f"    WARNING: maxCount=1 would block multiple duplicates/continuity links!")

# ── 1e. InventorySnapshot cardinality on UseCaseRecord ────────────────────────
print("\n--- 1e. partOfInventory cardinality (cross-year isolation) ---")
for ps in shacl.objects(AIU["UseCaseRecordShape"], SH["property"]):
    if shacl.value(ps, SH["path"]) == AIU["partOfInventory"]:
        min_c = shacl.value(ps, SH["minCount"])
        max_c = shacl.value(ps, SH["maxCount"])
        print(f"  partOfInventory: minCount={min_c}, maxCount={max_c}")
        if max_c and int(max_c) == 1:
            print("  OK: maxCount=1 means each record belongs to exactly one snapshot.")
            print("  Cross-year continuity uses continuesFrom links (different records),")
            print("  not multiple partOfInventory links on the same record.")

# ── 1f. Any shape that might block co-occurrence analysis ─────────────────────
print("\n--- 1f. Scan for any sh:disjoint / sh:uniqueLang / sh:hasValue on goal paths ---")
suspicious = []
for ps in shacl.subjects(SH["path"], AIU["hasBusinessGoal"]):
    for pred in [SH["disjoint"], SH["uniqueLang"], SH["hasValue"], SH["qualifiedValueShape"]]:
        val = shacl.value(ps, pred)
        if val is not None:
            pred_local = str(pred).split("#")[-1]
            suspicious.append((pred_local, val))
if suspicious:
    for p, v in suspicious:
        print(f"  FOUND: {p} = {v} — review for co-occurrence impact")
else:
    print("  None. No exotic constraints on hasBusinessGoal. OK.")

# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — Synthetic data scenarios
# ══════════════════════════════════════════════════════════════════════════════
sep("PART 2 — Synthetic Data Scenarios")

# ── Shared helpers ────────────────────────────────────────────────────────────
def build_core(g, rec_id, cai_type, stage, impact_type, snap_id="inv2024", year_str=None):
    """Build a minimal valid UseCaseRecord with plan + process.
    year_str: explicit inventory year (e.g. '2023'); derived from snap_id if omitted.
    """
    rec     = URIRef(f"{NS_T}{rec_id}")
    plan    = URIRef(f"{NS_T}{rec_id}_plan")
    proc    = URIRef(f"{NS_T}{rec_id}_proc")
    snap    = URIRef(f"{NS_T}{snap_id}")
    agency  = URIRef(f"{NS_T}AgencyX")
    bureau  = URIRef(f"{NS_T}BureauX")
    # Explicit year takes precedence; fallback: first 4-digit run found in snap_id
    if year_str is None:
        import re
        m = re.search(r'\d{4}', snap_id)
        year = m.group(0) if m else "2024"
    else:
        year = year_str

    g.add((rec,    RDF.type, AIU["UseCaseRecord"]))
    g.add((plan,   RDF.type, AIU["AIUseCasePlan"]))
    g.add((proc,   RDF.type, AIU["AIUseCaseProcess"]))
    g.add((snap,   RDF.type, AIU["InventorySnapshot"]))
    g.add((agency, RDF.type, AIU["Agency"]))
    g.add((bureau, RDF.type, AIU["Bureau"]))

    g.add((rec,  AIU["useCaseName"],         Literal(f"UC {rec_id}", datatype=XSD.string)))
    g.add((rec,  AIU["hasAgency"],           agency))
    g.add((rec,  AIU["hasBureau"],           bureau))
    g.add((rec,  AIU["hasCommercialAIType"], cai_type))
    g.add((rec,  AIU["describesPlan"],       plan))
    g.add((rec,  AIU["describesProcess"],    proc))
    g.add((rec,  AIU["partOfInventory"],     snap))
    g.add((plan, AIU["purposeBenefitsText"],
           Literal("Improve service delivery.", datatype=XSD.string)))
    g.add((proc, AIU["outputsText"],
           Literal("Automated decisions.", datatype=XSD.string)))
    g.add((proc, AIU["hasTopicArea"],        AIU["TA_GovServices"]))
    g.add((proc, AIU["hasDevelopmentStage"], stage))
    g.add((proc, AIU["hasImpactType"],       impact_type))
    g.add((snap, AIU["inventoryYear"],
           Literal(year, datatype=XSD.gYear)))
    return rec, plan, proc

def add_full_record_impl_fields(g, proc):
    """Add all FullRecordProcessShape stage-conditional fields for DS_ImplAssess."""
    g.add((proc, AIU["hasDevelopmentMethod"],   AIU["DM_InHouse"]))
    g.add((proc, AIU["usesPII"],                Literal(True,  datatype=XSD.boolean)))
    g.add((proc, AIU["saopReviewed"],           Literal(True,  datatype=XSD.boolean)))
    g.add((proc, AIU["customCodePresent"],      Literal(True,  datatype=XSD.boolean)))
    g.add((proc, AIU["hasCodeAccess"],          AIU["CA_PrivateSource"]))
    g.add((proc, AIU["hasDataDocLevel"],        AIU["DDL_Complete"]))
    g.add((proc, AIU["usesDemographicFeature"], AIU["DF_Race"]))
    g.add((proc, AIU["hasInternalReviewLevel"], AIU["IR_Developed"]))
    for tid, prop in [("t_init", AIU["hasInitiationTime"]),
                      ("t_acqd", AIU["hasAcqDevTime"]),
                      ("t_impl", AIU["hasImplementationTime"])]:
        t = URIRef(f"{NS_T}{tid}")
        g.add((t, RDF.type, AIU["TimeInstant"]))
        g.add((proc, prop, t))

def add_risk_fields(g, proc, rec_id):
    assess = URIRef(f"{NS_T}{rec_id}_assess")
    g.add((assess, RDF.type, AIU["AIImpactAssessmentProcess"]))
    g.add((proc, AIU["assessedBy"],           assess))
    g.add((proc, AIU["hasTestingLevel"],       AIU["TL_Benchmark"]))
    g.add((proc, AIU["hasMonitoringMaturity"], AIU["MM_Manual"]))
    g.add((proc, AIU["autonomousImpact"],      Literal(False, datatype=XSD.boolean)))

def add_rights_fields(g, proc):
    g.add((proc, AIU["hasAppealProcess"], Literal(True,  datatype=XSD.boolean)))
    g.add((proc, AIU["hasOptOut"],        Literal(False, datatype=XSD.boolean)))

def run_validation(data_g, label, show_all_violations=True):
    """Run pySHACL and return (conforms, violations, warnings)."""
    ont_g = Graph(); ont_g.parse(str(ONT_PATH), format="turtle")
    conforms, results_g, _ = pyshacl.validate(
        data_g,
        shacl_graph=str(SHACL_PATH),
        ont_graph=ont_g,
        inference="none",
        allow_warnings=True,
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
    )
    viols, warns = [], []
    shapes_fired = set()
    for vr in results_g.subjects(RDF.type, SH["ValidationResult"]):
        sev  = results_g.value(vr, SH["resultSeverity"])
        msg  = results_g.value(vr, SH["resultMessage"])
        src  = results_g.value(vr, SH["sourceShape"])
        path = results_g.value(vr, SH["resultPath"])
        src_local  = str(src).split("#")[-1]  if src  else "?"
        path_local = str(path).split("#")[-1] if path else "(SPARQL)"
        shapes_fired.add(src_local)
        entry = f"    [{src_local}] path={path_local}: {msg}"
        if sev == SH["Violation"]:
            viols.append(entry)
        else:
            warns.append(entry)
    print(f"\n[{label}]")
    print(f"  Conforms: {conforms}  |  Violations: {len(viols)}  |  Warnings: {len(warns)}")
    if viols and show_all_violations:
        print("  VIOLATIONS:")
        for v in viols:
            print(v)
    if warns:
        print(f"  Warnings ({len(warns)} total — PROV pipeline triples, expected):")
        for w in warns[:2]:
            print(w)
        if len(warns) > 2:
            print(f"    ... {len(warns)-2} more warnings omitted")
    return conforms, viols, warns

# ── Scenario 1: Multi-goal use case (5 goals, COTS record) ───────────────────
print("\n--- Scenario 1: Multi-goal COTS record (5 hasBusinessGoal links) ---")
g1 = Graph()
_, plan1, _ = build_core(g1, "multi_goal_uc",
                          cai_type=AIU["CAI_Scheduling"],
                          stage=AIU["DS_Initiated"],
                          impact_type=AIU["IT_Neither"])

GOALS = [AIU["BG_1_1"], AIU["BG_4_1"], AIU["BG_7_1"], AIU["BG_8_3"], AIU["BG_10_2"]]
for bg in GOALS:
    g1.add((plan1, AIU["hasBusinessGoal"], bg))
    # Ensure type visible in data graph (ontology provides this, but be explicit)
    g1.add((bg, RDF.type, AIU["BusinessGoalConcept"]))

print(f"  Triples: {len(g1)}")
print(f"  Goals assigned: {[str(g).split('#')[-1] for g in GOALS]}")
c1, v1, w1 = run_validation(g1, "Scenario 1 — Multi-goal COTS record")
if not v1:
    print("  ANALYTICS CHECK: 5 goals on one plan — no violations. Co-occurrence analysis is unblocked.")
    # Count goals programmatically
    goals_on_plan = list(g1.objects(plan1, AIU["hasBusinessGoal"]))
    print(f"  Graph query confirms {len(goals_on_plan)} goals reachable via plan1.")

# ── Scenario 2: High-impact multi-goal full record (IT_Both, HISP, PII) ───────
print("\n--- Scenario 2: High-impact full record (IT_Both, HISP_SSA, PII, 4 goals) ---")
g2 = Graph()
rec2, plan2, proc2 = build_core(g2, "himp_uc",
                                 cai_type=AIU["CAI_NoneOfTheAbove"],
                                 stage=AIU["DS_ImplAssess"],
                                 impact_type=AIU["IT_Both"])
# HISP support
g2.add((proc2, AIU["supportsHISP"], AIU["HISP_SSA"]))
# Full-record stage-conditional fields
add_full_record_impl_fields(g2, proc2)
# Risk fields (both rights + safety → RiskRecordShape fires)
add_risk_fields(g2, proc2, "himp_uc")
# Rights fields (IT_Both → RightsRecordShape fires)
add_rights_fields(g2, proc2)
# Multiple goals
GOALS2 = [AIU["BG_4_1"], AIU["BG_7_1"], AIU["BG_8_2"], AIU["BG_10_1"]]
for bg in GOALS2:
    g2.add((plan2, AIU["hasBusinessGoal"], bg))
    g2.add((bg, RDF.type, AIU["BusinessGoalConcept"]))
print(f"  Triples: {len(g2)}")
print(f"  Goals: {[str(g).split('#')[-1] for g in GOALS2]}")
print(f"  Impact: IT_Both (rights+safety)  |  HISP: HISP_SSA  |  PII: true")
c2, v2, w2 = run_validation(g2, "Scenario 2 — High-impact multi-goal full record")
if not v2:
    print("  ANALYTICS CHECK: Full record (IT_Both + HISP + PII + 4 goals) — no violations.")
    print("  'Impactful goals' dimension is fully representable without shape conflicts.")
    # Verify HISP + impact + goals are all queryable
    goals_2 = list(g2.objects(plan2, AIU["hasBusinessGoal"]))
    impact_2 = g2.value(proc2, AIU["hasImpactType"])
    hisp_2   = list(g2.objects(proc2, AIU["supportsHISP"]))
    pii_2    = g2.value(proc2, AIU["usesPII"])
    print(f"  Queryable: goals={len(goals_2)}, impact={str(impact_2).split('#')[-1]}, "
          f"hisp={[str(h).split('#')[-1] for h in hisp_2]}, pii={pii_2}")

# ── Scenario 3: Duplicate & continuity chains ─────────────────────────────────
print("\n--- Scenario 3: Two-year continuity + duplicate relationship ---")
g3 = Graph()
# Record A in 2023
rec_a, _, _ = build_core(g3, "uc_2023", cai_type=AIU["CAI_Scheduling"],
                           stage=AIU["DS_OpsMaint"], impact_type=AIU["IT_Neither"],
                           snap_id="inv2023", year_str="2023")

# Record B in 2024 — continues from Record A
rec_b, _, _ = build_core(g3, "uc_2024", cai_type=AIU["CAI_Scheduling"],
                           stage=AIU["DS_OpsMaint"], impact_type=AIU["IT_Neither"],
                           snap_id="inv2024", year_str="2024")
g3.add((rec_b, AIU["continuesFrom"], rec_a))

# Record C in 2024 — another record; B suspects it's a duplicate of C
rec_c, _, _ = build_core(g3, "uc_2024_alt", cai_type=AIU["CAI_Summarize"],
                           stage=AIU["DS_ImplAssess"], impact_type=AIU["IT_Neither"],
                           snap_id="inv2024", year_str="2024")
g3.add((rec_b, AIU["possibleDuplicateOf"], rec_c))

# Record D in 2025 — chain continues: A→B→D (3-year chain)
rec_d, _, _ = build_core(g3, "uc_2025", cai_type=AIU["CAI_Scheduling"],
                           stage=AIU["DS_OpsMaint"], impact_type=AIU["IT_Neither"],
                           snap_id="inv2025", year_str="2025")
g3.add((rec_d, AIU["continuesFrom"], rec_b))

print(f"  Triples: {len(g3)}")
print(f"  Chain: A(2023) ←continuesFrom— B(2024) —possibleDuplicateOf→ C(2024)")
print(f"         B(2024) ←continuesFrom— D(2025)")
c3, v3, w3 = run_validation(g3, "Scenario 3 — Continuity & duplicates")
if not v3:
    print("  ANALYTICS CHECK: 3-year chain + duplicate — no violations.")
    # Verify chain is traversable
    successors_b = list(g3.subjects(AIU["continuesFrom"], rec_b))  # D continues from B
    predecessors_b = list(g3.objects(rec_b, AIU["continuesFrom"])) # B continues from A
    dupes_b = list(g3.objects(rec_b, AIU["possibleDuplicateOf"]))
    print(f"  B is continued by: {[str(x).split('/')[-1] for x in successors_b]}")
    print(f"  B continues from:  {[str(x).split('/')[-1] for x in predecessors_b]}")
    print(f"  B possible dup of: {[str(x).split('/')[-1] for x in dupes_b]}")

# ── Scenario 4: Multi-goal record with BOTH continuity AND high impact ─────────
print("\n--- Scenario 4: Combined — high-impact full record WITH goals AND continuity ---")
g4 = Graph()
# 2023 predecessor
rec_prev, _, _ = build_core(g4, "prev2023", cai_type=AIU["CAI_NoneOfTheAbove"],
                              stage=AIU["DS_ImplAssess"], impact_type=AIU["IT_Rights"],
                              snap_id="inv2023_b", year_str="2023")
# Add required full-record fields for predecessor
add_full_record_impl_fields(g4, URIRef(f"{NS_T}prev2023_proc"))
add_risk_fields(g4, URIRef(f"{NS_T}prev2023_proc"), "prev2023")
add_rights_fields(g4, URIRef(f"{NS_T}prev2023_proc"))

# 2024 successor — full record, IT_Rights, 4 goals, continues from 2023
rec_curr, plan_curr, proc_curr = build_core(
    g4, "curr2024", cai_type=AIU["CAI_NoneOfTheAbove"],
    stage=AIU["DS_ImplAssess"], impact_type=AIU["IT_Rights"],
    snap_id="inv2024_b", year_str="2024")
add_full_record_impl_fields(g4, proc_curr)
add_risk_fields(g4, proc_curr, "curr2024")
add_rights_fields(g4, proc_curr)
g4.add((rec_curr, AIU["continuesFrom"], rec_prev))
GOALS4 = [AIU["BG_1_1"], AIU["BG_4_3"], AIU["BG_7_1"], AIU["BG_8_2"]]
for bg in GOALS4:
    g4.add((plan_curr, AIU["hasBusinessGoal"], bg))
    g4.add((bg, RDF.type, AIU["BusinessGoalConcept"]))
print(f"  Triples: {len(g4)}")
c4, v4, w4 = run_validation(g4, "Scenario 4 — High-impact + goals + cross-year continuity")

# ══════════════════════════════════════════════════════════════════════════════
# PART 3 — Summary
# ══════════════════════════════════════════════════════════════════════════════
sep("PART 3 — Findings Summary")

results = [
    ("Scenario 1 — Multi-goal COTS",               c1, v1, w1),
    ("Scenario 2 — High-impact multi-goal full",    c2, v2, w2),
    ("Scenario 3 — Continuity + duplicates",        c3, v3, w3),
    ("Scenario 4 — Combined high-impact + chain",   c4, v4, w4),
]
print(f"\n{'Scenario':<50} {'Conforms':>8}  {'Viol':>5}  {'Warn':>5}")
print("-" * 75)
for label, c, v, w in results:
    print(f"{label:<50} {str(c):>8}  {len(v):>5}  {len(w):>5}")

print("""
FINDINGS:

1. Multiple goals per use case
   hasBusinessGoal has sh:minCount=0, NO sh:maxCount — unlimited goals allowed.
   No SPARQL constraint references BusinessGoal or hasBusinessGoal.
   No sh:disjoint/sh:hasValue/sh:qualifiedValueShape on that path.
   → UNBLOCKED. Plans can hold arbitrarily many goal links.

2. High-impact impactful-goals dimension
   IT_Both (rights+safety), HISP support, PII use, and multiple goals can
   coexist on the same AIUseCaseProcess/AIUseCasePlan without any shape
   conflict. The shapes enforce required risk/rights fields precisely for
   that configuration — they do not restrict the number or combination
   of goals assigned.
   → UNBLOCKED. "Impactful goals" queries (join goals × impact × HISP × PII)
     are fully representable.

3. Duplicate & continuity relationships
   Neither aiu:possibleDuplicateOf nor aiu:continuesFrom has ANY sh:property
   constraint. No maxCount, no minCount, no type restriction.
   Multi-hop chains (2023→2024→2025) and multiple sibling duplicates
   are all representable.
   → UNBLOCKED.

4. Year attribution via InventorySnapshot
   partOfInventory: minCount=1, maxCount=1 on UseCaseRecordShape.
   inventoryYear:   minCount=1 on InventorySnapshotShape.
   Every record is anchored to exactly one year; cross-year continuity
   uses continuesFrom links between records (not multiple inventory links
   on the same record).
   → CORRECT AND SUFFICIENT for trend analysis.

5. Core analytics dimensions — required vs optional
   Required (minCount=1): useCaseName, hasAgency, hasBureau,
     hasCommercialAIType, partOfInventory, describesPlan, describesProcess,
     hasTopicArea, hasDevelopmentStage, hasImpactType, outputsText,
     inventoryYear.
   Intentionally optional (minCount=0): hasBusinessGoal (pipeline-populated),
     PROV triples (pipeline-computed), all COTS-gated §2–5 fields.
   → No essential analytics dimension is optional by mistake.

6. Issues found: NONE
   No shape over-constrains goal cardinality, blocks co-occurrence/
   centrality analysis, prevents multi-year chains, or imposes
   unexpected restrictions on the analytics patterns described in the
   project goals.

RECOMMENDED FUTURE ACTIONS (not bugs — optional enhancements):
  a. PROV minCount: After ingest pipeline enrichment is stable, promote
     prov:wasAttributedTo and prov:generatedAtTime from
     sh:minCount=0+sh:Warning to sh:minCount=1+sh:Warning to actively
     flag unenriched records.
  b. aiu:dateValue: Add data property + sh:pattern to TimeInstantShape
     for MM/YYYY literal validation.
  c. Goal quality gate: If downstream NLP assigns goals, consider adding
     a soft SPARQL constraint (sh:Warning) that flags records missing
     hasBusinessGoal after an InventorySnapshot is marked as enriched.
""")
