#!/usr/bin/env python3
"""
aiu_validation.py — 5-point check of aiu_ontology_ver1.ttl + aiu_shapes.ttl
Points:
  1. IRI + SKOS enum completeness
  2. SPARQL prefixes & SHACL-SPARQL compatibility
  3. PROV properties: OWL vs SHACL
  4. TimeInstant modeling & constraints
  5. Gate logic on synthetic test graphs
"""

import sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, URIRef, Literal
from rdflib.namespace import SKOS
import pyshacl

# ── Paths ────────────────────────────────────────────────────────────────────
BASE       = Path(__file__).resolve().parent.parent / "1_Ontology"  # metagraph_aiu/1_Ontology/
ONT_PATH   = BASE / "aiu_ontology_ver1.ttl"
SHACL_PATH = BASE / "aiu_shapes.ttl"

# ── Namespaces ────────────────────────────────────────────────────────────────
AIU  = Namespace("https://example.org/ai-usecase-ontology#")
SH   = Namespace("http://www.w3.org/ns/shacl#")
PROV = Namespace("http://www.w3.org/ns/prov#")

# ── Load graphs ───────────────────────────────────────────────────────────────
print("=== Loading graphs ===")
ont   = Graph(); ont.parse(str(ONT_PATH),   format="turtle")
shacl = Graph(); shacl.parse(str(SHACL_PATH), format="turtle")
print(f"Ontology triples : {len(ont)}")
print(f"Shapes   triples : {len(shacl)}")
print()

# ── Helper: walk rdf:List → Python list ──────────────────────────────────────
def rdflist_to_list(g, head):
    items = []
    cur = head
    while cur and cur != RDF.nil:
        first = g.value(cur, RDF.first)
        if first is not None:
            items.append(first)
        cur = g.value(cur, RDF.rest)
    return items


# ══════════════════════════════════════════════════════════════════════════════
# POINT 1 — IRI + SKOS enum completeness
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("POINT 1 — IRI + SKOS enum completeness")
print("=" * 70)

SCHEME_DEFS = [
    ("CommercialAITypeScheme",  "commercial AI type (gate field)", 20),
    ("HISPScheme",              "supports HISP",                   38),
    ("TopicAreaScheme",         "topic area",                      10),
    ("DevStageScheme",          "development stage",                5),
    ("ImpactTypeScheme",        "impact type",                      4),
    ("DevMethodScheme",         "development method",               3),
    ("CodeAccessScheme",        "code access type",                 3),
    ("MonitoringMaturityScheme","monitoring maturity",              4),
    ("DataDocLevelScheme",      "data documentation level",         4),
    ("TestingLevelScheme",      "real-world testing level",         5),
    ("InternalReviewScheme",    "internal review level",            4),
    ("DemoFeatureScheme",       "uses demographic feature",        12),
]

# 1a. Collect ontology members per scheme
ont_scheme_members = {}
for scheme_name, _, _ in SCHEME_DEFS:
    scheme_iri = AIU[scheme_name]
    members = sorted(str(s) for s in ont.subjects(SKOS.inScheme, scheme_iri))
    ont_scheme_members[scheme_name] = members

# 1b. Collect sh:in list members per property name (from shapes)
# Walk every blank-node property shape that has sh:in
sh_in_by_name = {}  # sh:name string → list of IRI strings
for prop_shape in shacl.subjects(SH["in"], None):
    head = shacl.value(prop_shape, SH["in"])
    if head is None:
        continue
    items = rdflist_to_list(shacl, head)
    name = shacl.value(prop_shape, SH["name"])
    if name is None:
        path = shacl.value(prop_shape, SH["path"])
        name = str(path).split("#")[-1] if path else str(prop_shape)
    key = str(name)
    if key not in sh_in_by_name:
        sh_in_by_name[key] = []
    sh_in_by_name[key].extend(str(i) for i in items)

print("sh:in lists found (property name → count):")
for k, v in sh_in_by_name.items():
    print(f"  {k!r}: {len(v)} items")
print()

# 1c. Cross-check
print("Cross-check per scheme:")
all_ok = True
for scheme_name, prop_name, expected_count in SCHEME_DEFS:
    # Find matching sh:in entry (partial match on prop_name)
    matching_keys = [k for k in sh_in_by_name if prop_name.lower() in k.lower()]
    if not matching_keys:
        print(f"  MISS  {scheme_name}: no sh:in found for prop '{prop_name}'")
        all_ok = False
        continue

    # Merge all matching lists (same property can appear in multiple shapes)
    sh_iris_list = []
    for mk in matching_keys:
        sh_iris_list.extend(sh_in_by_name[mk])

    sh_iris_set = set(sh_iris_list)
    ont_iris_set = set(ont_scheme_members.get(scheme_name, []))

    # Duplicate check
    dupes = [x for x in sh_iris_list if sh_iris_list.count(x) > 1]
    dupes = list(set(dupes))

    missing_in_ont = sh_iris_set - ont_iris_set
    missing_in_sh  = ont_iris_set - sh_iris_set

    status = "OK  " if (not missing_in_ont and not missing_in_sh and not dupes) else "ERR "
    if status == "ERR ":
        all_ok = False
    print(f"  {status} {scheme_name} (expected={expected_count}, "
          f"ont={len(ont_iris_set)}, sh:in={len(sh_iris_set)})")
    if dupes:
        print(f"       DUPLICATES in sh:in: {dupes}")
    for x in sorted(missing_in_ont):
        local = x.split("#")[-1]
        print(f"       sh:in has '{local}' but NOT in ontology")
    for x in sorted(missing_in_sh):
        local = x.split("#")[-1]
        print(f"       ontology has '{local}' but NOT in sh:in")

print()
print(f"POINT 1 RESULT: {'ALL MATCH — no missing or extra IRIs.' if all_ok else 'MISMATCHES DETECTED (see above).'}")
print()


# ══════════════════════════════════════════════════════════════════════════════
# POINT 2 — SPARQL prefixes & SHACL-SPARQL compatibility
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("POINT 2 — SPARQL prefixes & SHACL-SPARQL compatibility")
print("=" * 70)

SHAPES_IRI = URIRef("https://example.org/ai-usecase-shapes")

# 2a. sh:declare on shapes ontology node
declares = list(shacl.objects(SHAPES_IRI, SH["declare"]))
print(f"sh:declare entries on <{SHAPES_IRI}>: {len(declares)}")
for d in declares:
    pfx = shacl.value(d, SH["prefix"])
    ns  = shacl.value(d, SH["namespace"])
    print(f"  sh:prefix={str(pfx)!r}  sh:namespace={str(ns)!r}")
print()

# 2b. All sh:prefixes references
prefixes_refs = set(shacl.objects(None, SH["prefixes"]))
print(f"Unique sh:prefixes target IRIs: {len(prefixes_refs)}")
for ref in sorted(prefixes_refs, key=str):
    count = sum(1 for _ in shacl.subjects(SH["prefixes"], ref))
    ok = "(CORRECT — on shapes ontology node)" if ref == SHAPES_IRI else "WARNING — unexpected target"
    print(f"  {ref}  ← {count} usages  {ok}")
print()

# 2c. sh:SPARQLTarget nodes
sparql_targets = list(shacl.subjects(RDF.type, SH["SPARQLTarget"]))
print(f"sh:SPARQLTarget nodes: {len(sparql_targets)}")
for t in sparql_targets:
    pfx_ref = shacl.value(t, SH["prefixes"])
    # Find which shape owns it
    owner = shacl.value(None, SH["target"], t)
    print(f"  shape={owner}  sh:prefixes→{pfx_ref}")
print()

# 2d. sh:sparql constraint nodes
sparql_cns = list(shacl.subjects(SH["select"], None))
print(f"sh:sparql constraint nodes (sh:select): {len(sparql_cns)}")
wrong_prefix = []
for c in sparql_cns:
    pfx_ref = shacl.value(c, SH["prefixes"])
    name    = shacl.value(c, SH["name"])
    if pfx_ref != SHAPES_IRI:
        wrong_prefix.append((name, pfx_ref))
if wrong_prefix:
    print("  WRONG sh:prefixes on:")
    for name, ref in wrong_prefix:
        print(f"    {name!r} → {ref}")
else:
    print(f"  All {len(sparql_cns)} nodes reference <{SHAPES_IRI}> — CORRECT")
print()

# 2e. pySHACL version compatibility
print(f"pySHACL version: {pyshacl.__version__}")
from packaging.version import Version  # type: ignore[import-untyped]
pv = Version(pyshacl.__version__)
checks = [
    (pv >= Version("0.14.0"), "sh:SPARQLTarget (SHACL-SPARQL) support"),
    (pv >= Version("0.20.0"), "sh:prefixes resolution on ontology node"),
    (pv >= Version("0.25.0"), "sh:declare in shapes graph"),
]
for ok, feature in checks:
    print(f"  {'OK' if ok else 'FAIL'}  {feature}")
print()


# ══════════════════════════════════════════════════════════════════════════════
# POINT 3 — PROV properties: OWL vs SHACL
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("POINT 3 — PROV properties: OWL vs SHACL")
print("=" * 70)

UCR = AIU["UseCaseRecord"]
UCR_SHAPE = AIU["UseCaseRecordShape"]

# 3a. OWL restrictions
print("OWL restrictions on aiu:UseCaseRecord (owl:Restriction):")
for sc in ont.objects(UCR, RDFS.subClassOf):
    if isinstance(sc, URIRef):
        continue
    on_prop  = ont.value(sc, OWL.onProperty)
    some_of  = ont.value(sc, OWL.someValuesFrom)
    all_of   = ont.value(sc, OWL.allValuesFrom)
    if on_prop:
        quant = f"someValuesFrom={some_of}" if some_of else f"allValuesFrom={all_of}"
        prop_local = str(on_prop).split("#")[-1].split("/")[-1]
        print(f"  onProperty={prop_local}  {quant}")
print()

# 3b. SHACL property shapes for PROV properties
print("SHACL property shapes for prov:* in aiu:UseCaseRecordShape:")
prov_base = "http://www.w3.org/ns/prov#"
for prop_shape in shacl.objects(UCR_SHAPE, SH["property"]):
    path = shacl.value(prop_shape, SH["path"])
    if not (path and str(path).startswith(prov_base)):
        continue
    name      = shacl.value(prop_shape, SH["name"])
    min_count = shacl.value(prop_shape, SH["minCount"])
    max_count = shacl.value(prop_shape, SH["maxCount"])
    severity  = shacl.value(prop_shape, SH["severity"])
    sh_class  = shacl.value(prop_shape, SH["class"])
    datatype  = shacl.value(prop_shape, SH["datatype"])
    path_local = str(path).split("#")[-1]
    sev_local  = str(severity).split("#")[-1] if severity else "Violation (default)"
    print(f"  prov:{path_local}")
    print(f"    sh:name     = {str(name)!r}")
    print(f"    sh:minCount = {min_count}   sh:maxCount = {max_count}")
    print(f"    sh:severity = {sev_local}")
    print(f"    sh:class    = {sh_class}   sh:datatype = {datatype}")
print()
print("OWL vs SHACL discrepancy:")
print("  OWL : owl:someValuesFrom → open-world 'must have at least one value' for a complete model")
print("  SHACL: sh:minCount=0 + sh:severity sh:Warning → INTENTIONAL soft check")
print("  Rationale: PROV triples are computed by the ingest pipeline (not from CSV fields).")
print("  Raw data loaded before PROV enrichment will legitimately lack them.")
print("  To promote to hard errors post-enrichment: set sh:minCount=1, sh:severity=sh:Violation.")
print()


# ══════════════════════════════════════════════════════════════════════════════
# POINT 4 — TimeInstant modeling & constraints
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("POINT 4 — TimeInstant modeling & constraints")
print("=" * 70)

TI       = AIU["TimeInstant"]
TI_SHAPE = AIU["TimeInstantShape"]
BFO_INSTANT = URIRef("http://purl.obolibrary.org/obo/BFO_0000203")
BFO_T_REGION = URIRef("http://purl.obolibrary.org/obo/BFO_0000008")

# 4a. OWL class
ti_supers = list(ont.objects(TI, RDFS.subClassOf))
print("aiu:TimeInstant rdfs:subClassOf:")
for s in ti_supers:
    local = str(s).split("_")[-1] if "BFO_" in str(s) else str(s).split("#")[-1]
    marker = ""
    if s == BFO_INSTANT:
        marker = "  ← BFO temporal instant (CORRECT)"
    elif s == BFO_T_REGION:
        marker = "  ← WARNING: temporal region conflict"
    print(f"  {s}{marker}")
has_instant = BFO_INSTANT in ti_supers
has_region  = BFO_T_REGION in ti_supers
print(f"  subClassOf bfo:0000203 (temporal instant): {'YES — CORRECT' if has_instant else 'NO — MISSING'}")
print(f"  subClassOf bfo:0000008 (temporal region):  {'YES — CONFLICT' if has_region else 'NO — no conflict'}")
print()

# 4b. TimeInstantShape
ti_target  = shacl.value(TI_SHAPE, SH["targetClass"])
ti_props   = list(shacl.objects(TI_SHAPE, SH["property"]))
ti_sparqls = list(shacl.objects(TI_SHAPE, SH["sparql"]))
print(f"aiu:TimeInstantShape:")
print(f"  sh:targetClass = {ti_target}")
print(f"  sh:property constraints : {len(ti_props)}")
print(f"  sh:sparql constraints   : {len(ti_sparqls)}")
if not ti_props and not ti_sparqls:
    print("  STATUS: Placeholder only — no literal validation yet (expected).")
    print("  Gap: No sh:pattern/sh:datatype for MM/YYYY literal date value.")
    print("  Recommended future property: aiu:dateValue xsd:gYearMonth or xsd:string")
    print("  with sh:pattern \"^(0[1-9]|1[0-2])/[0-9]{4}$\"")
print()

# 4c. Object properties → TimeInstant
temporal_props = [
    ("hasInitiationTime",    "field 18_date_initiated"),
    ("hasAcqDevTime",        "field 19_date_acq_dev_began"),
    ("hasImplementationTime","field 20_date_implemented"),
    ("hasRetirementTime",    "field 21_date_retired"),
]
print("Object properties with rdfs:range aiu:TimeInstant:")
for prop_name, field in temporal_props:
    prop_iri = AIU[prop_name]
    rng = ont.value(prop_iri, RDFS.range)
    rng_local = str(rng).split("#")[-1] if rng else "MISSING"
    ok = "OK" if rng == TI else "WRONG"
    print(f"  aiu:{prop_name} → {rng_local}  [{ok}]  ({field})")
print()
# Check no data property aiu:dateValue exists
has_date_val = (AIU["dateValue"], RDF.type, OWL.DatatypeProperty) in ont
print(f"  aiu:dateValue defined in ontology: {has_date_val} (expected False — gap to fill)")
print()


# ══════════════════════════════════════════════════════════════════════════════
# POINT 5 — Gate logic on synthetic test graphs
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("POINT 5 — Gate logic on synthetic test graphs")
print("=" * 70)

NS_TEST = "https://test.example.org/"

def build_base(g, rec_id, cai_type, stage, impact_type):
    """Minimal valid core record."""
    rec     = URIRef(f"{NS_TEST}{rec_id}")
    plan    = URIRef(f"{NS_TEST}{rec_id}_plan")
    proc    = URIRef(f"{NS_TEST}{rec_id}_proc")
    snap    = URIRef(f"{NS_TEST}inv2024")
    agency  = URIRef(f"{NS_TEST}DeptX")
    bureau  = URIRef(f"{NS_TEST}BureauX")

    g.add((rec,    RDF.type, AIU["UseCaseRecord"]))
    g.add((plan,   RDF.type, AIU["AIUseCasePlan"]))
    g.add((proc,   RDF.type, AIU["AIUseCaseProcess"]))
    g.add((snap,   RDF.type, AIU["InventorySnapshot"]))
    g.add((agency, RDF.type, AIU["Agency"]))
    g.add((bureau, RDF.type, AIU["Bureau"]))

    g.add((rec,  AIU["useCaseName"],         Literal("Test UC", datatype=XSD.string)))
    g.add((rec,  AIU["hasAgency"],           agency))
    g.add((rec,  AIU["hasBureau"],           bureau))
    g.add((rec,  AIU["hasCommercialAIType"], cai_type))
    g.add((rec,  AIU["describesPlan"],       plan))
    g.add((rec,  AIU["describesProcess"],    proc))
    g.add((rec,  AIU["partOfInventory"],     snap))

    g.add((plan, AIU["purposeBenefitsText"],
           Literal("Automate processing.", datatype=XSD.string)))

    g.add((proc, AIU["outputsText"],
           Literal("Risk flags.", datatype=XSD.string)))
    g.add((proc, AIU["hasTopicArea"],        AIU["TA_GovServices"]))
    g.add((proc, AIU["hasDevelopmentStage"], stage))
    g.add((proc, AIU["hasImpactType"],       impact_type))

    g.add((snap, AIU["inventoryYear"],
           Literal("2024", datatype=XSD.gYear)))
    return rec, plan, proc


def run_shacl_check(data_g, label, show_warnings=False):
    """Run pySHACL validation and report results."""
    ont_g = Graph()
    ont_g.parse(str(ONT_PATH), format="turtle")
    try:
        conforms, results_g, results_text = pyshacl.validate(
            data_g,
            shacl_graph=str(SHACL_PATH),
            ont_graph=ont_g,
            inference="none",
            allow_warnings=True,
            abort_on_first=False,
            meta_shacl=False,
            advanced=True,   # Required for sh:SPARQLTarget
        )
        violations = []
        warnings   = []
        for vr in results_g.subjects(RDF.type, SH["ValidationResult"]):
            sev  = results_g.value(vr, SH["resultSeverity"])
            msg  = results_g.value(vr, SH["resultMessage"])
            src  = results_g.value(vr, SH["sourceShape"])
            path = results_g.value(vr, SH["resultPath"])
            src_local  = str(src).split("#")[-1]  if src  else "?"
            path_local = str(path).split("#")[-1] if path else "?"
            if sev == SH["Violation"]:
                violations.append(f"  VIOLATION [{src_local}] path={path_local}: {msg}")
            elif sev == SH["Warning"]:
                warnings.append(f"  WARNING   [{src_local}] path={path_local}: {msg}")
        print(f"\n[{label}]")
        print(f"  Conforms (no violations): {conforms}")
        print(f"  Violations: {len(violations)}   Warnings: {len(warnings)}")
        for v in violations:
            print(v)
        if show_warnings:
            for w in warnings[:3]:
                print(w)
            if len(warnings) > 3:
                print(f"  ... {len(warnings)-3} more warnings omitted")
        return conforms, violations, warnings
    except Exception as exc:  # noqa: BLE001
        import traceback
        print(f"[{label}] pySHACL ERROR: {exc}")
        traceback.print_exc()
        return None, [], []


# ── Test A: COTS-only record ─────────────────────────────────────────────────
print("\n--- TEST A: COTS-only (CAI_Scheduling, Initiated, Neither) ---")
g_a = Graph()
build_base(g_a, "cots1",
           cai_type=AIU["CAI_Scheduling"],
           stage=AIU["DS_Initiated"],
           impact_type=AIU["IT_Neither"])
print(f"  Triples: {len(g_a)}")
ca, va, wa = run_shacl_check(g_a, "A — COTS-only", show_warnings=True)

# ── Test B: Full record, Neither/Initiated (no risk gate) ────────────────────
print("\n--- TEST B: Full record (CAI_NoneOfTheAbove, Initiated, Neither) ---")
g_b = Graph()
build_base(g_b, "full1",
           cai_type=AIU["CAI_NoneOfTheAbove"],
           stage=AIU["DS_Initiated"],
           impact_type=AIU["IT_Neither"])
print(f"  Triples: {len(g_b)}")
cb, vb, wb = run_shacl_check(g_b, "B — Full/Neither/Initiated", show_warnings=False)

# ── Test C: Full record, Rights/ImplAssess — ALL required fields provided ────
print("\n--- TEST C: Full Rights record (NoneOfTheAbove, ImplAssess, Rights) — COMPLETE ---")
g_c = Graph()
_, _, proc_c = build_base(g_c, "rights1",
                           cai_type=AIU["CAI_NoneOfTheAbove"],
                           stage=AIU["DS_ImplAssess"],
                           impact_type=AIU["IT_Rights"])
# Risk fields (RiskRecordShape)
assess_c = URIRef(f"{NS_TEST}rights1_assess")
g_c.add((assess_c, RDF.type, AIU["AIImpactAssessmentProcess"]))
g_c.add((proc_c, AIU["assessedBy"],           assess_c))
g_c.add((proc_c, AIU["hasTestingLevel"],       AIU["TL_Benchmark"]))
g_c.add((proc_c, AIU["hasMonitoringMaturity"], AIU["MM_Manual"]))
g_c.add((proc_c, AIU["autonomousImpact"],      Literal(False, datatype=XSD.boolean)))
# Rights fields (RightsRecordShape)
g_c.add((proc_c, AIU["hasAppealProcess"],  Literal(True,  datatype=XSD.boolean)))
g_c.add((proc_c, AIU["hasOptOut"],         Literal(False, datatype=XSD.boolean)))
# FullRecordProcessShape stage-conditional (ImplAssess triggers most sparql gates)
g_c.add((proc_c, AIU["hasDevelopmentMethod"],   AIU["DM_InHouse"]))
g_c.add((proc_c, AIU["usesPII"],                Literal(False, datatype=XSD.boolean)))
g_c.add((proc_c, AIU["saopReviewed"],           Literal(True,  datatype=XSD.boolean)))
g_c.add((proc_c, AIU["customCodePresent"],      Literal(False, datatype=XSD.boolean)))
g_c.add((proc_c, AIU["hasCodeAccess"],          AIU["CA_PrivateSource"]))
g_c.add((proc_c, AIU["hasDataDocLevel"],        AIU["DDL_Complete"]))
g_c.add((proc_c, AIU["usesDemographicFeature"], AIU["DF_None"]))
g_c.add((proc_c, AIU["hasInternalReviewLevel"], AIU["IR_Developed"]))
t_init = URIRef(f"{NS_TEST}t_init")
t_acqd = URIRef(f"{NS_TEST}t_acqd")
t_impl = URIRef(f"{NS_TEST}t_impl")
for t in [t_init, t_acqd, t_impl]:
    g_c.add((t, RDF.type, AIU["TimeInstant"]))
g_c.add((proc_c, AIU["hasInitiationTime"],     t_init))
g_c.add((proc_c, AIU["hasAcqDevTime"],         t_acqd))
g_c.add((proc_c, AIU["hasImplementationTime"], t_impl))
print(f"  Triples: {len(g_c)}")
cc, vc, wc = run_shacl_check(g_c, "C — Rights/ImplAssess COMPLETE", show_warnings=True)

# ── Test D: Full record, Rights/ImplAssess — missing ALL risk/rights fields ──
print("\n--- TEST D: Full Rights record (NoneOfTheAbove, ImplAssess, Rights) — MISSING fields ---")
g_d = Graph()
build_base(g_d, "rights2",
           cai_type=AIU["CAI_NoneOfTheAbove"],
           stage=AIU["DS_ImplAssess"],
           impact_type=AIU["IT_Rights"])
# NO risk, rights, or conditional full-record fields added
print(f"  Triples: {len(g_d)}")
cd, vd, wd = run_shacl_check(g_d, "D — Rights/ImplAssess MISSING fields", show_warnings=False)

# ── Test E: Safety-only record — verify RightsRecordShape does NOT fire ──────
print("\n--- TEST E: Safety-only (NoneOfTheAbove, ImplAssess, Safety) — should NOT need rights fields ---")
g_e = Graph()
_, _, proc_e = build_base(g_e, "safety1",
                           cai_type=AIU["CAI_NoneOfTheAbove"],
                           stage=AIU["DS_ImplAssess"],
                           impact_type=AIU["IT_Safety"])
# Add risk fields (RiskRecordShape fires for safety too)
assess_e = URIRef(f"{NS_TEST}safety1_assess")
g_e.add((assess_e, RDF.type, AIU["AIImpactAssessmentProcess"]))
g_e.add((proc_e, AIU["assessedBy"],           assess_e))
g_e.add((proc_e, AIU["hasTestingLevel"],       AIU["TL_None"]))
g_e.add((proc_e, AIU["hasMonitoringMaturity"], AIU["MM_None"]))
g_e.add((proc_e, AIU["autonomousImpact"],      Literal(True, datatype=XSD.boolean)))
# FullRecord stage-conditional fields
g_e.add((proc_e, AIU["hasDevelopmentMethod"],   AIU["DM_Contracting"]))
g_e.add((proc_e, AIU["usesPII"],                Literal(True,  datatype=XSD.boolean)))
g_e.add((proc_e, AIU["saopReviewed"],           Literal(True,  datatype=XSD.boolean)))
g_e.add((proc_e, AIU["customCodePresent"],      Literal(False, datatype=XSD.boolean)))
g_e.add((proc_e, AIU["hasCodeAccess"],          AIU["CA_NoAccess"]))
g_e.add((proc_e, AIU["hasDataDocLevel"],        AIU["DDL_Partial"]))
g_e.add((proc_e, AIU["usesDemographicFeature"], AIU["DF_Race"]))
g_e.add((proc_e, AIU["hasInternalReviewLevel"], AIU["IR_Limited"]))
t_e1 = URIRef(f"{NS_TEST}te1"); t_e2 = URIRef(f"{NS_TEST}te2"); t_e3 = URIRef(f"{NS_TEST}te3")
for t in [t_e1, t_e2, t_e3]:
    g_e.add((t, RDF.type, AIU["TimeInstant"]))
g_e.add((proc_e, AIU["hasInitiationTime"],     t_e1))
g_e.add((proc_e, AIU["hasAcqDevTime"],         t_e2))
g_e.add((proc_e, AIU["hasImplementationTime"], t_e3))
# Intentionally NO hasAppealProcess / hasOptOut
print(f"  Triples: {len(g_e)}")
ce, ve, we = run_shacl_check(g_e, "E — Safety-only/ImplAssess (no rights fields)", show_warnings=True)


# ══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════════════
print()
print("=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
summary = [
    ("A — COTS-only",                       ca, va, wa,
     "Only core shapes; FullRecord/Risk/Rights must NOT fire"),
    ("B — Full/Neither/Initiated",          cb, vb, wb,
     "FullRecord fires, stage=Initiated → most SPARQL guards skip; no Risk/Rights"),
    ("C — Rights/ImplAssess COMPLETE",      cc, vc, wc,
     "All shapes fire and pass; only PROV Warnings expected"),
    ("D — Rights/ImplAssess MISSING",       cd, vd, wd,
     "Multiple Violations from Risk/Rights/FullRecord SPARQL shapes"),
    ("E — Safety/ImplAssess no rights",     ce, ve, we,
     "RiskRecordShape fires; RightsRecordShape must NOT fire (safety-only)"),
]
print(f"{'Test':<40} {'Conforms':>8}  {'Viol':>5}  {'Warn':>5}  Notes")
print("-" * 90)
for label, conforms, viols, warns, notes in summary:
    c_str = str(conforms) if conforms is not None else "ERROR"
    print(f"{label:<40} {c_str:>8}  {len(viols):>5}  {len(warns):>5}  {notes}")
print()
print("See individual test sections above for full violation/warning details.")
