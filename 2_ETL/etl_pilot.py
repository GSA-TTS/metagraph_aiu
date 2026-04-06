#!/usr/bin/env python3
"""
etl_pilot.py — End-to-end ETL pilot: 15 rows from 2024 Federal AI Use Case Inventory.
Steps:
  1. Load ontology, shapes, taxonomy
  2. Select 15 representative CSV rows
  3. CSV → RDF ETL → pilot_1_15.ttl
  4. Business-goal tagging (Claude Haiku LLM)
  5. SHACL validation
  6. Final report
"""

import json, re, warnings
from pathlib import Path

import anthropic
import pandas as pd
from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, URIRef, Literal
from rdflib.namespace import SKOS
import pyshacl

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────
_HERE      = Path(__file__).resolve().parent          # metagraph_aiu/2_ETL/
ONTOLOGY   = _HERE.parent / "1_Ontology"              # metagraph_aiu/1_Ontology/
ONT_PATH   = ONTOLOGY / "aiu_ontology_ver1.ttl"
SHACL_PATH = ONTOLOGY / "aiu_shapes.ttl"
TAX_PATH   = ONTOLOGY / "taxonomy_bizGoals.md"
CSV_PATH   = Path("/tmp/inventory_2024.csv")          # place source CSV here before running
OUT_PATH   = _HERE / "pilot_1_15.ttl"

AIU  = Namespace("https://example.org/ai-usecase-ontology#")
PROV = Namespace("http://www.w3.org/ns/prov#")
SH   = Namespace("http://www.w3.org/ns/shacl#")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Load ontology + shapes + taxonomy
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("STEP 1 — Loading ontology, shapes, taxonomy")
print("=" * 70)

ont   = Graph(); ont.parse(str(ONT_PATH),   format="turtle")
shacl = Graph(); shacl.parse(str(SHACL_PATH), format="turtle")
print(f"Ontology  : {len(ont)} triples")
print(f"Shapes    : {len(shacl)} triples")

# ── Build SKOS concept lookup tables from ontology ───────────────────────────
def concept_map(scheme_local):
    """Return {normalised_label: URIRef} for a SKOS scheme."""
    scheme_iri = AIU[scheme_local]
    m = {}
    for c in ont.subjects(SKOS.inScheme, scheme_iri):
        lbl = ont.value(c, SKOS.prefLabel)
        if lbl:
            key = str(lbl).lower().strip().rstrip('.')
            m[key] = c
    return m

CAI_MAP  = concept_map("CommercialAITypeScheme")
TA_MAP   = concept_map("TopicAreaScheme")
DS_MAP   = concept_map("DevStageScheme")
IT_MAP   = concept_map("ImpactTypeScheme")
DM_MAP   = concept_map("DevMethodScheme")
CA_MAP   = concept_map("CodeAccessScheme")
MM_MAP   = concept_map("MonitoringMaturityScheme")
DDL_MAP  = concept_map("DataDocLevelScheme")
TL_MAP   = concept_map("TestingLevelScheme")
IR_MAP   = concept_map("InternalReviewScheme")
HISP_MAP = concept_map("HISPScheme")
DF_MAP   = concept_map("DemoFeatureScheme")

# DevStage: add aliases for non-standard CSV values
DS_ALIASES = {
    "in production":                 AIU["DS_OpsMaint"],
    "in mission":                    AIU["DS_OpsMaint"],
    "planned":                       AIU["DS_Initiated"],
    "acquisition and/or development":AIU["DS_AcqDev"],
    "implementation and assessment": AIU["DS_ImplAssess"],
    "operation and maintenance":     AIU["DS_OpsMaint"],
    "initiated":                     AIU["DS_Initiated"],
    "retired":                       AIU["DS_Retired"],
}
DS_MAP.update(DS_ALIASES)

# ImpactType: aliases
IT_ALIASES = {
    "rights-impacting": AIU["IT_Rights"],
    "safety-impacting": AIU["IT_Safety"],
    "both":             AIU["IT_Both"],
    "neither":          AIU["IT_Neither"],
}
IT_MAP.update(IT_ALIASES)

# CodeAccess: CSV values use "Yes/No – ..." prefix not found in SKOS labels
CA_ALIASES = {
    "yes \x96 agency has access to source code, but it is not public":
        AIU["CA_PrivateSource"],
    "yes \x96 source code is publicly available":
        AIU["CA_PublicSource"],
    "no \x96 agency does not have access to source code":
        AIU["CA_NoAccess"],
    "yes – agency has access to source code, but it is not public":
        AIU["CA_PrivateSource"],
    "yes – source code is publicly available":
        AIU["CA_PublicSource"],
    "no – agency does not have access to source code":
        AIU["CA_NoAccess"],
}
CA_MAP.update(CA_ALIASES)

print(f"Concept maps built: CAI={len(CAI_MAP)}, TA={len(TA_MAP)}, DS={len(DS_MAP)}, IT={len(IT_MAP)}")

# ── Parse taxonomy ────────────────────────────────────────────────────────────
def parse_taxonomy(path):
    """Parse taxonomy_bizGoals.md → list of sub-goal dicts (line-by-line FSM)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    goals = []
    current = None   # sub-goal being accumulated
    in_lookup = False

    def flush():
        if current:
            goals.append({
                "id":           current["id"],
                "label":        current["label"],
                "description":  " ".join(current["desc"][:6]),
                "lookup_fields": current["lf"],
                "seed_examples": current["seeds"],
            })

    for raw in lines:
        # ── sub-goal heading: ### N.M label ──────────────────────────────────
        m = re.match(r'^###\s+(\d+\.\d+)\s+(.*)', raw)
        if m:
            flush()
            sub_id = f"aiu:BG_{m.group(1).replace('.', '_')}"
            current = {"id": sub_id, "label": m.group(2).strip(),
                       "desc": [], "lf": [], "seeds": {}}
            in_lookup = False
            continue

        # ── cluster heading: ## N. label ─────────────────────────────────────
        if re.match(r'^##\s+\d+\.', raw):
            flush()
            current = None
            in_lookup = False
            continue

        if current is None:
            continue

        s = raw.strip()
        # ── lookup-fields section marker ──────────────────────────────────────
        if '**lookup-fields**' in s or s.startswith('**lookup-field'):
            in_lookup = True
            continue

        if not in_lookup:
            # description bullets
            if s.startswith('-') or s.startswith('*'):
                current["desc"].append(s.lstrip('-* '))
        else:
            # field line: - `fieldname` – description with "examples"
            m2 = re.match(r'-\s+`([^`]+)`\s*[–\-]\s*(.*)', s)
            if m2:
                fname = m2.group(1).strip()
                ex_text = m2.group(2).strip()
                current["lf"].append(fname)
                found = re.findall(r'"([^"]+)"', ex_text)
                if not found:
                    found = [t.strip() for t in ex_text.split(',')
                             if t.strip() and len(t.strip()) < 80]
                current["seeds"][fname] = found

    flush()
    return goals

GOALS = parse_taxonomy(TAX_PATH)
print(f"Parsed {len(GOALS)} sub-goals from taxonomy")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Load CSV and select 15 representative rows
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 2 — Loading CSV and selecting 15 representative rows")
print("=" * 70)

df_raw = pd.read_csv(CSV_PATH, encoding='latin-1')
c = df_raw.columns  # keep column objects to avoid encoding issues when indexing

# ── Column index aliases (handle special characters in names safely) ──────────
CI = {
    'name':            0,  'agency':     1,  'abr':        2,  'bureau':  3,
    'topic_area':      4,  'commercial': 6,  'purpose':    7,  'outputs': 8,
    'dev_stage':       9,  'impact':    10,  'date_init': 11,  'date_acq':12,
    'date_impl':      13,  'date_ret':  14,  'dev_method':15,
    'hisp_supp':      17,  'hisp_name': 18,
    'pii':            22,  'saop':      23,  'agency_data':26,
    'data_docs':      27,  'demo_feat': 28,  'custom_code':30,
    'code_access':    31,  'has_ato':   33,  'sys_name':   34,
    'int_review':     43,  'impact_assess':45,'real_test': 46,
    'key_risks':      47,  'monitor':   49,  'auto_impact':50,
    'appeal':         58,  'opt_out':   60,
}

def col(name): return c[CI[name]]

# ── Create normalized working DataFrame ─────────────────────────────────────
def nstr(s): return str(s).strip() if pd.notna(s) else ""

df = df_raw.copy()
df['_cai']  = df[col('commercial')].fillna('').str.strip().str.lower()
df['_imp']  = df[col('impact')].fillna('').str.strip().str.lower()
df['_hisp'] = df[col('hisp_supp')].fillna('').str.strip().str.lower()
df['_pii']  = df[col('pii')].fillna('').str.strip().str.lower()
df['_stage']= df[col('dev_stage')].fillna('').str.strip().str.lower()
df['_ta']   = df[col('topic_area')].fillna('').str.strip().str.lower()
df['_agency']= df[col('abr')].fillna('').str.strip()

IS_FULL    = df['_cai'].str.contains('none of the above', case=False, na=False)
IS_RIGHTS  = df['_imp'].str.contains('rights', case=False, na=False)
IS_SAFETY  = df['_imp'].str.contains('safety', case=False, na=False)
IS_BOTH    = df['_imp'].str.contains('^both$', case=False, na=False)
IS_HISP    = df['_hisp'] == 'yes'
IS_PII     = df['_pii'] == 'yes'

full_df    = df[IS_FULL]
cots_df    = df[~IS_FULL & df['_cai'].ne('')]

print(f"Total rows: {len(df)}, Full records: {len(full_df)}, COTS: {len(cots_df)}")
print(f"Full+Rights: {(IS_FULL & IS_RIGHTS).sum()}, Full+Safety: {(IS_FULL & IS_SAFETY).sum()}, "
      f"Full+Both: {(IS_FULL & IS_BOTH).sum()}")
print(f"Full+HISP: {(IS_FULL & IS_HISP).sum()}, Full+PII: {(IS_FULL & IS_PII).sum()}")

# ── Greedy selection satisfying criteria ─────────────────────────────────────
selected = []

def add_rows(mask, n, label, exclude=None):
    excl = set(exclude or [])
    pool = df[mask].copy()
    pool = pool[~pool.index.isin(excl)]
    # Prefer diversity: different agencies and topic areas
    pool['_sort_key'] = pool['_agency'] + '|' + pool['_ta'] + '|' + pool['_stage']
    # De-duplicate by sort key to spread agencies/topics
    pool_sorted = pool.sort_values('_sort_key').drop_duplicates('_sort_key')
    rows = pool_sorted.head(n)
    if len(rows) < n:
        # fallback: take any
        pool2 = pool[~pool.index.isin(rows.index)]
        rows = pd.concat([rows, pool2.head(n - len(rows))])
    return list(rows.head(n).index)

excl = []
# 10 full records guaranteeing: ≥3 rights-or-both, ≥3 safety-or-both, ≥3 HISP, ≥3 PII
IS_RGTB = IS_FULL & (IS_RIGHTS | IS_BOTH)   # rights-or-both full records
IS_SFTB = IS_FULL & (IS_SAFETY | IS_BOTH)   # safety-or-both full records

# Slot A: 2 rows satisfying Both+HISP+PII simultaneously (multi-constraint coverage)
both_hisp_pii = add_rows(IS_FULL & IS_BOTH & IS_HISP & IS_PII, 2, "both+hisp+pii", excl)
excl += both_hisp_pii
# Slot B: 1 row Rights/Both + PII (brings rights≥3 and PII≥3)
rights_pii = add_rows(IS_RGTB & IS_PII, 1, "rights+pii", excl)
excl += rights_pii
# Slot C: 1 row Safety/Both + HISP (brings safety≥3 and HISP≥3)
safety_hisp = add_rows(IS_SFTB & IS_HISP, 1, "safety+hisp", excl)
excl += safety_hisp
# Slot D: 6 filler full records for agency/topic diversity
other_full = add_rows(IS_FULL, 6, "other_full", excl)
excl += other_full
full_indices = both_hisp_pii + rights_pii + safety_hisp + other_full

# 5 COTS records from at least 3 agencies
cots_indices = add_rows(~IS_FULL & df['_cai'].ne(''), 5, "cots", excl)

selected_idx = full_indices + cots_indices
pilot_df = df.loc[selected_idx].copy().reset_index(drop=False)
pilot_df.rename(columns={'index': 'orig_idx'}, inplace=True)

# Print overview
print(f"\nSelected {len(pilot_df)} rows:")
print(f"{'#':>2}  {'Agency':>8}  {'CAI':>12}  {'Stage':>14}  {'Impact':>16}  "
      f"{'HISP':>4}  {'PII':>3}  Use Case Name")
print("-" * 110)
for i, row in pilot_df.iterrows():
    cai_short = "NoneOfAbove" if 'none of the above' in str(row[col('commercial')]).lower() else "COTS"
    imp = str(row[col('impact')]).strip()[:15]
    stage = str(row[col('dev_stage')]).strip()[:14]
    name = str(row[col('name')])[:35]
    hisp = str(row[col('hisp_supp')]).strip()[:3]
    pii  = str(row[col('pii')]).strip()[:3]
    print(f"{i:>2}  {str(row[col('abr')]):>8}  {cai_short:>12}  {stage:>14}  "
          f"{imp:>16}  {hisp:>4}  {pii:>3}  {name}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — CSV → RDF ETL
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 3 — CSV → RDF ETL")
print("=" * 70)

kg = Graph()
# Bind prefixes
kg.bind("aiu",  AIU)
kg.bind("rdf",  RDF)
kg.bind("rdfs", RDFS)
kg.bind("owl",  OWL)
kg.bind("xsd",  XSD)
kg.bind("skos", SKOS)
kg.bind("prov", PROV)

# ── Shared InventorySnapshot ─────────────────────────────────────────────────
INV_IRI = AIU["inv2024"]
kg.add((INV_IRI, RDF.type,             AIU["InventorySnapshot"]))
kg.add((INV_IRI, AIU["inventoryYear"], Literal("2024", datatype=XSD.gYear)))

def slugify(s, maxlen=30):
    """Safe IRI fragment from a string."""
    s = re.sub(r'[^\w\s-]', '', str(s).strip())
    s = re.sub(r'[\s-]+', '_', s)
    return s[:maxlen].strip('_') or "UNK"

def lookup(val, mapping, fallback=None):
    """Case-insensitive map lookup with strip + period removal.
    Falls back to prefix match when CSV cells contain long explanatory text
    appended after the concept label (e.g. 'Documentation has been developed: ...')."""
    key = str(val).strip().lower().rstrip('.')
    if key in mapping:
        return mapping[key]
    # Prefix fallback: find longest concept label that is a prefix of key
    best = None
    best_len = 0
    for label, iri in mapping.items():
        if key.startswith(label) and len(label) > best_len:
            best, best_len = iri, len(label)
    return best if best else fallback

def to_bool(val):
    v = str(val).strip().lower()
    if v in ('yes', 'true', '1'):   return Literal(True,  datatype=XSD.boolean)
    if v in ('no', 'false', '0'):   return Literal(False, datatype=XSD.boolean)
    # Handle "Yes – ..." / "No - ..." prefix forms common in inventory CSV
    first = v.split()[0].rstrip('.-\u2013\u2014') if v.split() else ''
    if first == 'yes':  return Literal(True,  datatype=XSD.boolean)
    if first == 'no':   return Literal(False, datatype=XSD.boolean)
    return None

def add_time_node(g, prop, rec_iri, date_str, suffix):
    if not date_str or pd.isna(date_str) or str(date_str).strip() in ('', 'nan'):
        return
    ti = AIU[f"ti_{rec_iri.split('#')[-1]}_{suffix}"]
    g.add((ti, RDF.type, AIU["TimeInstant"]))
    g.add((rec_iri, prop, ti))   # process → TimeInstant

def split_multival(val, mapping):
    """Split a comma/semicolon-separated multi-value field and map each."""
    if not val or pd.isna(val):
        return []
    results = []
    for part in re.split(r'[,;]', str(val)):
        mapped = lookup(part, mapping)
        if mapped:
            results.append(mapped)
    return results

# ── Per-row ETL ───────────────────────────────────────────────────────────────
ucr_iris  = {}  # row_i -> URIRef (for goal tagging later)
plan_iris = {}
proc_iris = {}

for i, row in pilot_df.iterrows():
    abr  = slugify(nstr(row[col('abr')]) or nstr(row[col('agency')])[:8], 10)
    rid  = f"2024_{abr}_{i}"

    ucr_iri  = AIU[f"ucr_{rid}"]
    plan_iri = AIU[f"plan_{rid}"]
    proc_iri = AIU[f"proc_{rid}"]
    ucr_iris[i]  = ucr_iri
    plan_iris[i] = plan_iri
    proc_iris[i] = proc_iri

    # ── Agency + Bureau nodes ─────────────────────────────────────────────────
    agency_iri = AIU[f"agency_{slugify(nstr(row[col('abr')]), 20)}"]
    bureau_iri = AIU[f"bureau_{slugify(nstr(row[col('bureau')]), 25)}"]
    if (agency_iri, RDF.type, AIU["Agency"]) not in kg:
        kg.add((agency_iri, RDF.type,      AIU["Agency"]))
        kg.add((agency_iri, RDFS.label,    Literal(nstr(row[col('agency')]), datatype=XSD.string)))
    if (bureau_iri, RDF.type, AIU["Bureau"]) not in kg:
        kg.add((bureau_iri, RDF.type,      AIU["Bureau"]))
        kg.add((bureau_iri, RDFS.label,    Literal(nstr(row[col('bureau')]), datatype=XSD.string)))

    # ── UseCaseRecord ─────────────────────────────────────────────────────────
    kg.add((ucr_iri, RDF.type,              AIU["UseCaseRecord"]))
    kg.add((ucr_iri, AIU["useCaseName"],    Literal(nstr(row[col('name')]), datatype=XSD.string)))
    kg.add((ucr_iri, AIU["hasAgency"],      agency_iri))
    kg.add((ucr_iri, AIU["hasBureau"],      bureau_iri))
    kg.add((ucr_iri, AIU["partOfInventory"],INV_IRI))
    kg.add((ucr_iri, AIU["describesPlan"],  plan_iri))
    kg.add((ucr_iri, AIU["describesProcess"],proc_iri))

    cai_val = lookup(row[col('commercial')], CAI_MAP)
    if cai_val:
        kg.add((ucr_iri, AIU["hasCommercialAIType"], cai_val))
    else:
        # Fallback: try substring match
        cai_raw = str(row[col('commercial')]).lower()
        fallback = AIU["CAI_NoneOfTheAbove"] if 'none' in cai_raw else AIU["CAI_Search"]
        kg.add((ucr_iri, AIU["hasCommercialAIType"], fallback))

    is_full = 'none of the above' in str(row[col('commercial')]).lower()

    # ── AIUseCasePlan ─────────────────────────────────────────────────────────
    purpose_text = nstr(row[col('purpose')])
    outputs_text = nstr(row[col('outputs')])
    plan_text = (purpose_text + " " + outputs_text).strip() or "No description provided."
    kg.add((plan_iri, RDF.type,                  AIU["AIUseCasePlan"]))
    kg.add((plan_iri, AIU["purposeBenefitsText"], Literal(plan_text, datatype=XSD.string)))

    # ── AIUseCaseProcess ──────────────────────────────────────────────────────
    kg.add((proc_iri, RDF.type, AIU["AIUseCaseProcess"]))
    kg.add((proc_iri, AIU["outputsText"], Literal(outputs_text or "N/A", datatype=XSD.string)))

    # Topic area
    ta_val = lookup(row[col('topic_area')], TA_MAP)
    kg.add((proc_iri, AIU["hasTopicArea"],
            ta_val if ta_val else AIU["TA_MissionEnabling"]))

    # Dev stage
    ds_val = lookup(row[col('dev_stage')], DS_MAP)
    kg.add((proc_iri, AIU["hasDevelopmentStage"],
            ds_val if ds_val else AIU["DS_Initiated"]))

    # Impact type
    it_val = lookup(row[col('impact')], IT_MAP)
    kg.add((proc_iri, AIU["hasImpactType"],
            it_val if it_val else AIU["IT_Neither"]))

    # ── Full-record-only fields ───────────────────────────────────────────────
    if is_full:
        # Date fields
        add_time_node(kg, AIU["hasInitiationTime"],     proc_iri, row[col('date_init')], "init")
        add_time_node(kg, AIU["hasAcqDevTime"],         proc_iri, row[col('date_acq')],  "acq")
        add_time_node(kg, AIU["hasImplementationTime"], proc_iri, row[col('date_impl')], "impl")
        add_time_node(kg, AIU["hasRetirementTime"],     proc_iri, row[col('date_ret')],  "ret")

        # Dev method
        dm_val = lookup(row[col('dev_method')], DM_MAP)
        if dm_val:
            kg.add((proc_iri, AIU["hasDevelopmentMethod"], dm_val))

        # HISP
        if str(row[col('hisp_supp')]).strip().lower() == 'yes':
            hisp_val = lookup(row[col('hisp_name')], HISP_MAP)
            if hisp_val:
                kg.add((proc_iri, AIU["supportsHISP"], hisp_val))

        # PII / SAOP
        pii_b  = to_bool(row[col('pii')])
        saop_b = to_bool(row[col('saop')])
        if pii_b  is not None: kg.add((proc_iri, AIU["usesPII"],       pii_b))
        if saop_b is not None: kg.add((proc_iri, AIU["saopReviewed"],  saop_b))

        # Data docs
        ddl_val = lookup(row[col('data_docs')], DDL_MAP)
        if ddl_val: kg.add((proc_iri, AIU["hasDataDocLevel"], ddl_val))

        # Demographic features (multi-valued)
        for df_val in split_multival(row[col('demo_feat')], DF_MAP):
            kg.add((proc_iri, AIU["usesDemographicFeature"], df_val))

        # Custom code
        cc_b = to_bool(row[col('custom_code')])
        if cc_b is not None: kg.add((proc_iri, AIU["customCodePresent"], cc_b))

        # Code access
        ca_val = lookup(row[col('code_access')], CA_MAP)
        if ca_val: kg.add((proc_iri, AIU["hasCodeAccess"], ca_val))

        # Internal review
        ir_val = lookup(row[col('int_review')], IR_MAP)
        if ir_val: kg.add((proc_iri, AIU["hasInternalReviewLevel"], ir_val))

        # Real-world testing
        tl_val = lookup(row[col('real_test')], TL_MAP)
        if tl_val: kg.add((proc_iri, AIU["hasTestingLevel"], tl_val))

        # Monitoring maturity
        mm_val = lookup(row[col('monitor')], MM_MAP)
        if mm_val: kg.add((proc_iri, AIU["hasMonitoringMaturity"], mm_val))

        # Autonomous impact
        ai_b = to_bool(row[col('auto_impact')])
        if ai_b is not None: kg.add((proc_iri, AIU["autonomousImpact"], ai_b))

        # Appeal process
        ap_b = to_bool(row[col('appeal')])
        if ap_b is not None: kg.add((proc_iri, AIU["hasAppealProcess"], ap_b))

        # Opt out
        oo_b = to_bool(row[col('opt_out')])
        if oo_b is not None: kg.add((proc_iri, AIU["hasOptOut"], oo_b))

        # Impact assessment process (if assessed)
        imp_ass_raw = str(row[col('impact_assess')]).strip().lower()
        if imp_ass_raw == 'yes':
            assess_iri = AIU[f"assess_{rid}"]
            kg.add((assess_iri, RDF.type, AIU["AIImpactAssessmentProcess"]))
            kg.add((proc_iri, AIU["assessedBy"], assess_iri))

print(f"RDF graph built: {len(kg)} triples across {len(pilot_df)} records")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Business-goal tagging (Claude Haiku LLM)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 4 — Business-goal tagging (Claude Haiku)")
print("=" * 70)

# ── Build goal catalog string and lookup set ──────────────────────────────────
def _goal_catalog():
    lines = []
    for g in GOALS:
        desc = g["description"][:150].rstrip()
        lines.append(f"- {g['id']}: {g['label']} — {desc}")
    return "\n".join(lines)

GOAL_CATALOG = _goal_catalog()
GOAL_ID_SET  = {g["id"] for g in GOALS}

import os as _os
_api_key = _os.environ.get("ANTHROPIC_API_KEY", "")
if not _api_key:
    raise EnvironmentError(
        "ANTHROPIC_API_KEY is not set. "
        "Run:  export ANTHROPIC_API_KEY=sk-ant-..."
    )
_client = anthropic.Anthropic(api_key=_api_key)

_SYSTEM = (
    "You are a business analyst tagging federal AI use cases with business goals. "
    "Reply ONLY with valid JSON in the exact format requested. "
    'If no goal fits well, return {"goals": []}.'
)

def tag_goals_llm(
    name: str, purpose: str, outputs: str, topic: str, stage: str
) -> list:
    """Return a list of matching goal IDs (0–5) via Claude Haiku."""
    prompt = (
        f"Use Case: {name}\n"
        f"Purpose/Benefits: {purpose[:600]}\n"
        f"AI Outputs: {outputs[:300]}\n"
        f"Topic Area: {topic}\n"
        f"Development Stage: {stage}\n\n"
        f"Business Goal Catalog (id: label — description):\n{GOAL_CATALOG}\n\n"
        'Select 0 to 5 goal IDs that genuinely match this use case.\n'
        'Respond with JSON only, no prose: {"goals": ["aiu:BG_X_Y", ...]}'
    )
    resp = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()
    try:
        data = json.loads(raw)
        return [g for g in data.get("goals", []) if g in GOAL_ID_SET][:5]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []

# ── Per-use-case tagging loop ─────────────────────────────────────────────────
goal_assignments = {}   # row_i -> [goal_id, ...]

print(f"\n{'#':>2}  {'Use Case Name':>35}  Goals  Top goal")
print("-" * 70)
for i in range(len(pilot_df)):
    r = pilot_df.iloc[i]
    ids = tag_goals_llm(
        name    = nstr(r[col('name')]),
        purpose = nstr(r[col('purpose')]),
        outputs = nstr(r[col('outputs')]),
        topic   = nstr(r[col('topic_area')]),
        stage   = nstr(r[col('dev_stage')]),
    )
    goal_assignments[i] = ids
    top = ids[0] if ids else "none"
    print(f"{i:>2}  {nstr(r[col('name')]):>35.35}  {len(ids):>5}  {top}")
    for gid in ids:
        kg.add((plan_iris[i], AIU["hasBusinessGoal"], AIU[gid.replace("aiu:", "")]))

print(f"\nTotal triples after goal tagging: {len(kg)}")


# ── Serialize ────────────────────────────────────────────────────────────────
kg.serialize(destination=str(OUT_PATH), format="turtle")

# ── Annotate BG_* IRIs with inline comments (review aid) ─────────────────────
_bg_labels: dict = {}
for _bg in ont.subjects(RDF.type, AIU["BusinessGoalConcept"]):
    _local = str(_bg).split("#")[-1]
    _lbl   = ont.value(_bg, SKOS.prefLabel)
    if _lbl:
        _bg_labels[_local] = str(_lbl)

_lines = OUT_PATH.read_text(encoding="utf-8").splitlines()
_annotated = []
for _line in _lines:
    _m = re.search(r'aiu:(BG_\w+)', _line)
    if _m:
        _line = _line.rstrip() + f"  # {_bg_labels.get(_m.group(1), _m.group(1))}"
    _annotated.append(_line)
OUT_PATH.write_text("\n".join(_annotated) + "\n", encoding="utf-8")

print(f"\nSaved: {OUT_PATH}  ({OUT_PATH.stat().st_size // 1024} KB)")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — SHACL validation
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 5 — SHACL validation")
print("=" * 70)

ont_g = Graph(); ont_g.parse(str(ONT_PATH), format="turtle")
data_g = Graph(); data_g.parse(str(OUT_PATH), format="turtle")

conforms, results_g, results_text = pyshacl.validate(
    data_g,
    shacl_graph=str(SHACL_PATH),
    ont_graph=ont_g,
    inference="none",
    allow_warnings=True,
    abort_on_first=False,
    meta_shacl=False,
    advanced=True,
)

# Parse results
viols, warns = [], []
for vr in results_g.subjects(RDF.type, SH["ValidationResult"]):
    sev   = results_g.value(vr, SH["resultSeverity"])
    msg   = results_g.value(vr, SH["resultMessage"])
    src   = results_g.value(vr, SH["sourceShape"])
    focus = results_g.value(vr, SH["focusNode"])
    path  = results_g.value(vr, SH["resultPath"])
    src_l   = str(src).split("#")[-1]   if src   else "?"
    focus_l = str(focus).split("#")[-1] if focus else "?"
    path_l  = str(path).split("#")[-1]  if path  else "(SPARQL)"
    entry = f"  [{src_l}] focus={focus_l}, path={path_l}: {str(msg)[:120]}"
    if sev == SH["Violation"]: viols.append((focus_l, entry))
    else:                       warns.append((focus_l, entry))

print(f"\nConforms: {conforms}  |  Violations: {len(viols)}  |  Warnings: {len(warns)}")

# Per-record summary
record_viols = {}
for focus_l, entry in viols:
    record_viols.setdefault(focus_l, []).append(entry)
for focus_l, entry in warns:
    pass  # skip warnings from per-record summary

if viols:
    print("\nViolations by record:")
    for rec, entries in sorted(record_viols.items()):
        print(f"  {rec}: {len(entries)} violation(s)")
        for e in entries[:3]:
            print(e)
        if len(entries) > 3:
            print(f"    ... {len(entries)-3} more")
else:
    print("  No violations — all records conform.")

if warns:
    print(f"\nWarnings (all {len(warns)}):")
    for _, e in warns[:5]:
        print(e)
    if len(warns) > 5:
        print(f"  ... {len(warns)-5} more (PROV pipeline warnings expected)")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Final report
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 6 — Final Report")
print("=" * 70)

# Goal assignment statistics
all_goal_counts = [len(goal_assignments[i]) for i in range(len(pilot_df))]
total = sum(all_goal_counts)
mean_goals = total / len(all_goal_counts) if all_goal_counts else 0.0
print(f"\nGoal assignment stats:")
print(f"  Mean goals/use case : {mean_goals:.2f}")
print(f"  Min goals           : {min(all_goal_counts)}")
print(f"  Max goals           : {max(all_goal_counts)}")

# Count how many use cases get each goal
goal_freq: dict = {}
for ids in goal_assignments.values():
    for gid in ids:
        goal_freq[gid] = goal_freq.get(gid, 0) + 1
print(f"\nMost frequently assigned goals:")
for gid, freq in sorted(goal_freq.items(), key=lambda x: -x[1])[:8]:
    glabel = next((g["label"] for g in GOALS if g["id"] == gid), gid)
    print(f"  {gid}: {freq}x — {glabel}")

print(f"\nFull goal table per use case:")
print(f"{'#':>2}  {'Name':>35}  {'Goals':>5}  {'Assigned Goal IDs'}")
print("-" * 100)
for i in range(len(pilot_df)):
    r = pilot_df.iloc[i]
    ids = goal_assignments[i]
    print(f"{i:>2}  {nstr(r[col('name')]):>35.35}  {len(ids):>5}  "
          f"{', '.join(g.replace('aiu:', '') for g in ids[:5])}")

_p = pilot_df
_full_mask = _p['_cai'].str.contains('none of the above', case=False, na=False)
_rgtb = _full_mask & (_p['_imp'].str.contains('rights', case=False, na=False) |
                      _p['_imp'].str.contains('both',   case=False, na=False))
_sftb = _full_mask & (_p['_imp'].str.contains('safety', case=False, na=False) |
                      _p['_imp'].str.contains('both',   case=False, na=False))
_hisp = _full_mask & (_p['_hisp'] == 'yes')
_pii  = _full_mask & (_p['_pii']  == 'yes')
print(f"""
SUMMARY
=======
Rows selected      : {len(pilot_df)} (10 full-record NoneOfAbove + 5 COTS)
  Full+Rights/Both : {_rgtb.sum()} (requirement: ≥3)
  Full+Safety/Both : {_sftb.sum()} (requirement: ≥3)
  Full+HISP        : {_hisp.sum()} (requirement: ≥3)
  Full+PII         : {_pii.sum()} (requirement: ≥3)
RDF output         : {OUT_PATH}  ({OUT_PATH.stat().st_size // 1024} KB, {len(data_g)} triples)
Goal tagging       : Claude Haiku (claude-haiku-4-5-20251001), max 5 goals/use case
SHACL              : conforms={conforms}, violations={len(viols)}, warnings={len(warns)}
""")
