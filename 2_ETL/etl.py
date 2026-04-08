#!/usr/bin/env python3
"""
etl.py — Federal AI Use Case Inventory ETL pipeline (production).

Improvements over etl_pilot.py:
  - --case parameter: tiny (15 rows), mid (25%), full (all rows)
  - Dual-LLM goal tagging: Claude Haiku + GPT-5.4-mini
  - Intersection resolution on disagreements; disagreements logged to JSONL
  - Auto-incrementing output filename for --case tiny

Steps:
  1. Load ontology, shapes, taxonomy
  2. Select rows per --case
  3. CSV -> RDF ETL
  4. Business-goal tagging (Sonnet + GPT; intersection on disagreement)
  5. SHACL validation
  6. Final report (with agreement statistics)

Usage:
  python3 2_ETL/etl.py --case tiny   # 15 representative rows (default)
  python3 2_ETL/etl.py --case mid    # 25%% of total rows
  python3 2_ETL/etl.py --case full   # all rows

Environment variables (required):
  ANTHROPIC_API_KEY  -- Sonnet tagging
  OPENAI_API_KEY     -- GPT-5.4-mini tagging
"""

import argparse
import json
import math
import os
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic
import openai
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import pyshacl
from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, XSD
from rdflib.namespace import SKOS

warnings.filterwarnings("ignore")

# ── Argument parsing ───────────────────────────────────────────────────────────
_parser = argparse.ArgumentParser(
    description="ETL pipeline: CSV -> RDF with dual-LLM business-goal tagging."
)
_parser.add_argument(
    "--case",
    choices=["tiny", "mid", "full"],
    default="tiny",
    help="Row selection: tiny=15 rows, mid=25%%, full=all  (default: tiny)",
)
_parser.add_argument(
    "--n",
    type=int,
    default=None,
    metavar="N",
    help="Exact number of rows to sample at random (random_state=42); "
    "overrides --case when provided.",
)
_args = _parser.parse_args()
CASE: str = _args.case
N_ROWS: int | None = _args.n

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent          # metagraph_aiu/2_ETL/
ONTOLOGY = _HERE.parent / "1_Ontology"           # metagraph_aiu/1_Ontology/
ONT_PATH = ONTOLOGY / "aiu_ontology_ver1.ttl"
SHACL_PATH = ONTOLOGY / "aiu_shapes.ttl"
TAX_PATH = ONTOLOGY / "taxonomy_bizGoals.md"
CSV_PATH = Path("/tmp/inventory_2024.csv")       # place source CSV here before run

_TS = datetime.now().strftime("%Y%m%d_%H%M%S")

if N_ROWS is not None:
    OUT_PATH = _HERE / f"run_n{N_ROWS}_{_TS}.ttl"
    DISAGREE_PATH = _HERE / f"disagreements_n{N_ROWS}_{_TS}.jsonl"
elif CASE == "tiny":
    _existing = sorted(_HERE.glob("pilot_*_15.ttl"))
    _next_n = len(_existing) + 1
    OUT_PATH = _HERE / f"pilot_{_next_n}_15.ttl"
    DISAGREE_PATH = _HERE / f"disagreements_{CASE}_{_TS}.jsonl"
elif CASE == "mid":
    OUT_PATH = _HERE / f"run_mid_{_TS}.ttl"
    DISAGREE_PATH = _HERE / f"disagreements_{CASE}_{_TS}.jsonl"
else:
    OUT_PATH = _HERE / f"full_2024_{_TS}.ttl"
    DISAGREE_PATH = _HERE / f"disagreements_{CASE}_{_TS}.jsonl"

# ── RDF namespaces ─────────────────────────────────────────────────────────────
AIU = Namespace("https://example.org/ai-usecase-ontology#")
PROV = Namespace("http://www.w3.org/ns/prov#")
SH = Namespace("http://www.w3.org/ns/shacl#")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Load ontology + shapes + taxonomy
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("STEP 1 — Loading ontology, shapes, taxonomy")
print("=" * 70)

ont = Graph()
ont.parse(str(ONT_PATH), format="turtle")
shacl = Graph()
shacl.parse(str(SHACL_PATH), format="turtle")
print(f"Ontology  : {len(ont)} triples")
print(f"Shapes    : {len(shacl)} triples")


# ── Build SKOS concept lookup tables from ontology ────────────────────────────
def concept_map(scheme_local: str) -> dict[str, Any]:
    """Return {normalised_label: URIRef} for a SKOS scheme."""
    scheme_iri = AIU[scheme_local]
    m: dict[str, Any] = {}
    for c in ont.subjects(SKOS.inScheme, scheme_iri):
        lbl = ont.value(c, SKOS.prefLabel)
        if lbl:
            key = str(lbl).lower().strip().rstrip(".")
            m[key] = c
    return m


CAI_MAP = concept_map("CommercialAITypeScheme")
TA_MAP = concept_map("TopicAreaScheme")
DS_MAP = concept_map("DevStageScheme")
IT_MAP = concept_map("ImpactTypeScheme")
DM_MAP = concept_map("DevMethodScheme")
CA_MAP = concept_map("CodeAccessScheme")
MM_MAP = concept_map("MonitoringMaturityScheme")
DDL_MAP = concept_map("DataDocLevelScheme")
TL_MAP = concept_map("TestingLevelScheme")
IR_MAP = concept_map("InternalReviewScheme")
HISP_MAP = concept_map("HISPScheme")
DF_MAP = concept_map("DemoFeatureScheme")

# DevStage: add aliases for non-standard CSV values
DS_ALIASES: dict[str, Any] = {
    "in production":                  AIU["DS_OpsMaint"],
    "in mission":                     AIU["DS_OpsMaint"],
    "planned":                        AIU["DS_Initiated"],
    "acquisition and/or development": AIU["DS_AcqDev"],
    "implementation and assessment":  AIU["DS_ImplAssess"],
    "operation and maintenance":      AIU["DS_OpsMaint"],
    "initiated":                      AIU["DS_Initiated"],
    "retired":                        AIU["DS_Retired"],
}
DS_MAP.update(DS_ALIASES)

# ImpactType: aliases
IT_ALIASES: dict[str, Any] = {
    "rights-impacting": AIU["IT_Rights"],
    "safety-impacting": AIU["IT_Safety"],
    "both":             AIU["IT_Both"],
    "neither":          AIU["IT_Neither"],
}
IT_MAP.update(IT_ALIASES)

# CodeAccess: CSV values use "Yes/No -" prefix not found in SKOS labels
CA_ALIASES: dict[str, Any] = {
    "yes \x96 agency has access to source code, but it is not public":
        AIU["CA_PrivateSource"],
    "yes \x96 source code is publicly available":
        AIU["CA_PublicSource"],
    "no \x96 agency does not have access to source code":
        AIU["CA_NoAccess"],
    "yes - agency has access to source code, but it is not public":
        AIU["CA_PrivateSource"],
    "yes - source code is publicly available":
        AIU["CA_PublicSource"],
    "no - agency does not have access to source code":
        AIU["CA_NoAccess"],
    "yes \u2013 agency has access to source code, but it is not public":
        AIU["CA_PrivateSource"],
    "yes \u2013 source code is publicly available":
        AIU["CA_PublicSource"],
    "no \u2013 agency does not have access to source code":
        AIU["CA_NoAccess"],
}
CA_MAP.update(CA_ALIASES)

print(
    f"Concept maps built: CAI={len(CAI_MAP)}, TA={len(TA_MAP)}, "
    f"DS={len(DS_MAP)}, IT={len(IT_MAP)}"
)


# ── Parse taxonomy ─────────────────────────────────────────────────────────────
def parse_taxonomy(path: Path) -> list[dict[str, Any]]:
    """Parse taxonomy_bizGoals.md -> list of sub-goal dicts (line-by-line FSM)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    goals: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_lookup = False

    def flush() -> None:
        if current:
            goals.append(
                {
                    "id": current["id"],
                    "label": current["label"],
                    "description": " ".join(current["desc"][:6]),
                    "lookup_fields": current["lf"],
                    "seed_examples": current["seeds"],
                }
            )

    for raw in lines:
        # ── sub-goal heading: ### N.M label ──────────────────────────────────
        m = re.match(r"^###\s+(\d+\.\d+)\s+(.*)", raw)
        if m:
            flush()
            sub_id = f"aiu:BG_{m.group(1).replace('.', '_')}"
            current = {
                "id": sub_id,
                "label": m.group(2).strip(),
                "desc": [],
                "lf": [],
                "seeds": {},
            }
            in_lookup = False
            continue

        # ── cluster heading: ## N. label ─────────────────────────────────────
        if re.match(r"^##\s+\d+\.", raw):
            flush()
            current = None
            in_lookup = False
            continue

        if current is None:
            continue

        s = raw.strip()
        # ── lookup-fields section marker ──────────────────────────────────────
        if "**lookup-fields**" in s or s.startswith("**lookup-field"):
            in_lookup = True
            continue

        if not in_lookup:
            if s.startswith("-") or s.startswith("*"):
                current["desc"].append(s.lstrip("-* "))
        else:
            m2 = re.match(r"-\s+`([^`]+)`\s*[\u2013\-]\s*(.*)", s)
            if m2:
                fname = m2.group(1).strip()
                ex_text = m2.group(2).strip()
                current["lf"].append(fname)
                # Taxonomy uses typographic curly quotes (\u201c/\u201d);
                # normalise to ASCII before extracting quoted phrases.
                ex_norm = ex_text.replace("\u201c", '"').replace("\u201d", '"')
                found = re.findall(r'"([^"]+)"', ex_norm)
                if not found:
                    found = [
                        t.strip()
                        for t in ex_text.split(",")
                        if t.strip() and len(t.strip()) < 80
                    ]
                current["seeds"][fname] = found

    flush()
    return goals


GOALS = parse_taxonomy(TAX_PATH)
print(f"Parsed {len(GOALS)} sub-goals from taxonomy")


# ── Build goal catalog string and lookup set ──────────────────────────────────
# Goals in GOAL_BLACKLIST are excluded from LLM prompts and model responses.
# They are pre-assigned to every plan node in Step 3 (universally applicable).
GOAL_BLACKLIST: set[str] = {
    "aiu:BG_8_3",  # Automation and AI enablement — true by definition for all records
}

# Maps taxonomy lookup-field names to the prompt section label that contains
# the matching text. Fields absent from this dict are not in the prompt and
# are skipped when building signal lines.
_FIELD_TO_PROMPT: dict[str, str] = {
    "intended_purpose_and_expected_benefits": "Purpose/Benefits",
    "problem_to_be_solved":                  "Purpose/Benefits",
    "ai_system_outputs":                     "AI Outputs",
    "stage_of_development":                  "Development Stage",
    "lifecycle_stage":                       "Development Stage",
    "use_case_name":                         "Use Case",
}


def _goal_catalog() -> str:
    """Build a structured catalog block for each non-blacklisted goal.

    Each block contains:
      - Goal ID and label (header)
      - Full description (up to 1000 chars of joined bullets)
      - Per-prompt-field signal lines: quoted example phrases from the taxonomy
        lookup-fields section, mapped to the prompt section where they appear.
    Only signal lines with actual example phrases are emitted.
    """
    blocks = []
    for g in GOALS:
        if g["id"] in GOAL_BLACKLIST:
            continue

        desc = g["description"][:1000].rstrip()

        # Aggregate seed phrases by prompt section label, deduplicating.
        signals: dict[str, list[str]] = {}
        for field, examples in g["seed_examples"].items():
            prompt_label = _FIELD_TO_PROMPT.get(field)
            if not prompt_label or not examples:
                continue
            bucket = signals.setdefault(prompt_label, [])
            for ex in examples:
                if ex not in bucket:
                    bucket.append(ex)

        block_lines = [f"{g['id']}: {g['label']}"]
        block_lines.append(f"  Goal: {desc}")
        for prompt_label, examples in signals.items():
            quoted = ", ".join(f'"{e}"' for e in examples[:8])
            block_lines.append(f"  Look in {prompt_label} for: {quoted}")

        blocks.append("\n".join(block_lines))

    return "\n\n".join(blocks)


GOAL_CATALOG = _goal_catalog()
GOAL_ID_SET = {g["id"] for g in GOALS}  # includes blacklisted IDs (valid ontology IRIs)

# Cluster-level summary used in Step 1 of the cluster-first prompt.
# Each entry: cluster number, name, and a brief one-line scope description.
CLUSTER_SUMMARY = """\
1. Strategic Direction    — mission alignment, strategy, portfolio, business model
2. Market and Customer    — market understanding, customer acquisition, CX, retention
3. Product and Innovation — product development, R&D speed, quality, innovation
4. Operations             — process efficiency, supply chain, controls, scaling
5. Financial              — revenue, cost, risk, capital, reporting
6. Human Capital          — workforce, talent, learning, culture
7. Governance             — regulatory compliance, governance, ethics, transparency
8. Data and Technology    — data quality, infrastructure, cybersecurity, AI/ML ops
9. Service and Delivery   — service delivery, accessibility, citizen/stakeholder CX
10. Risk and Safety       — product safety, crisis management, resilience\
"""


# ══════════════════════════════════════════════════════════════════════════════
# API clients (validated before CSV loading)
# ══════════════════════════════════════════════════════════════════════════════
_anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not _anthropic_key:
    raise EnvironmentError(
        "ANTHROPIC_API_KEY is not set. Run:  export ANTHROPIC_API_KEY=sk-ant-..."
    )
_openai_key = os.environ.get("OPENAI_API_KEY", "")
if not _openai_key:
    raise EnvironmentError(
        "OPENAI_API_KEY is not set. Run:  export OPENAI_API_KEY=sk-..."
    )

_anthropic_client = anthropic.Anthropic(api_key=_anthropic_key)
_openai_client = openai.OpenAI(api_key=_openai_key)

_SYSTEM = (
    "You are a business analyst tagging federal AI use cases with business goals. "
    "Reply ONLY with valid JSON in the exact format requested. "
    'If no goal fits well, return {"goals": []}.'
)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Load CSV and select rows
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
_case_label = f"n={N_ROWS}" if N_ROWS is not None else f"case={CASE}"
print(f"STEP 2 — Loading CSV and selecting rows ({_case_label})")
print("=" * 70)

df_raw = pd.read_csv(CSV_PATH, encoding="latin-1")
c = df_raw.columns  # keep column objects; avoids smart-apostrophe encoding issues

# ── Column index aliases ───────────────────────────────────────────────────────
CI: dict[str, int] = {
    "name":         0,  "agency":     1,  "abr":        2,  "bureau":   3,
    "topic_area":   4,  "commercial": 6,  "purpose":    7,  "outputs":  8,
    "dev_stage":    9,  "impact":    10,  "date_init": 11,  "date_acq": 12,
    "date_impl":   13,  "date_ret":  14,  "dev_method": 15,
    "hisp_supp":   17,  "hisp_name": 18,
    "pii":         22,  "saop":      23,  "agency_data": 26,
    "data_docs":   27,  "demo_feat": 28,  "custom_code": 30,
    "code_access": 31,  "has_ato":   33,  "sys_name":   34,
    "int_review":  43,  "impact_assess": 45, "real_test": 46,
    "key_risks":   47,  "monitor":   49,  "auto_impact": 50,
    "appeal":      58,  "opt_out":   60,
}


def col(name: str) -> Any:
    return c[CI[name]]


# ── Normalised work DataFrame ──────────────────────────────────────────────────
def nstr(s: Any) -> str:
    return str(s).strip() if pd.notna(s) else ""


df = df_raw.copy()
df["_cai"] = df[col("commercial")].fillna("").str.strip().str.lower()
df["_imp"] = df[col("impact")].fillna("").str.strip().str.lower()
df["_hisp"] = df[col("hisp_supp")].fillna("").str.strip().str.lower()
df["_pii"] = df[col("pii")].fillna("").str.strip().str.lower()
df["_stage"] = df[col("dev_stage")].fillna("").str.strip().str.lower()
df["_ta"] = df[col("topic_area")].fillna("").str.strip().str.lower()
df["_agency"] = df[col("abr")].fillna("").str.strip()

IS_FULL = df["_cai"].str.contains("none of the above", case=False, na=False)

print(
    f"Total rows: {len(df)},  "
    f"Full-record (NoneOfAbove): {IS_FULL.sum()},  "
    f"COTS: {(~IS_FULL & df['_cai'].ne('')).sum()}"
)


# ── Row selection helpers ──────────────────────────────────────────────────────
def _add_rows(
    df_in: pd.DataFrame,
    mask: pd.Series,
    n: int,
    exclude: list[int] | None = None,
) -> list[int]:
    """Select up to n rows matching mask with agency/topic/stage diversity."""
    excl = set(exclude or [])
    pool = df_in[mask].copy()
    pool = pool[~pool.index.isin(excl)]
    pool["_sort_key"] = (
        pool["_agency"] + "|" + pool["_ta"] + "|" + pool["_stage"]
    )
    pool_sorted = pool.sort_values("_sort_key").drop_duplicates("_sort_key")
    rows = pool_sorted.head(n)
    if len(rows) < n:
        pool2 = pool[~pool.index.isin(rows.index)]
        rows = pd.concat([rows, pool2.head(n - len(rows))])
    return list(rows.head(n).index)


def select_tiny(df_in: pd.DataFrame) -> pd.DataFrame:
    """15-row slot selection guaranteeing coverage of SHACL gate conditions."""
    is_full = df_in["_cai"].str.contains(
        "none of the above", case=False, na=False
    )
    is_rights = df_in["_imp"].str.contains("rights", case=False, na=False)
    is_safety = df_in["_imp"].str.contains("safety", case=False, na=False)
    is_both = df_in["_imp"].str.contains(r"^both$", case=False, na=False)
    is_hisp = df_in["_hisp"] == "yes"
    is_pii = df_in["_pii"] == "yes"
    is_rgtb = is_full & (is_rights | is_both)
    is_sftb = is_full & (is_safety | is_both)

    excl: list[int] = []
    # Slot A: 2 rows Both+HISP+PII (satisfies rights, safety, HISP, PII simultaneously)
    slot_a = _add_rows(
        df_in, is_full & is_both & is_hisp & is_pii, 2, excl
    )
    excl += slot_a
    # Slot B: 1 row Rights/Both + PII
    slot_b = _add_rows(df_in, is_rgtb & is_pii, 1, excl)
    excl += slot_b
    # Slot C: 1 row Safety/Both + HISP
    slot_c = _add_rows(df_in, is_sftb & is_hisp, 1, excl)
    excl += slot_c
    # Slot D: 6 filler full records
    slot_d = _add_rows(df_in, is_full, 6, excl)
    excl += slot_d
    # Slot E: 5 COTS records
    slot_e = _add_rows(df_in, ~is_full & df_in["_cai"].ne(""), 5, excl)

    selected_idx = slot_a + slot_b + slot_c + slot_d + slot_e
    sel = df_in.loc[selected_idx].copy().reset_index(drop=False)
    sel.rename(columns={"index": "orig_idx"}, inplace=True)
    return sel


def select_mid(df_in: pd.DataFrame) -> pd.DataFrame:
    """25% stratified random sample (random_state=42 for reproducibility)."""
    n = math.ceil(len(df_in) * 0.25)
    sel = df_in.sample(n=n, random_state=42).copy()
    sel = sel.reset_index(drop=False)
    sel.rename(columns={"index": "orig_idx"}, inplace=True)
    return sel


def select_full(df_in: pd.DataFrame) -> pd.DataFrame:
    """All rows."""
    sel = df_in.copy().reset_index(drop=False)
    sel.rename(columns={"index": "orig_idx"}, inplace=True)
    return sel


def select_n(df_in: pd.DataFrame, n: int) -> pd.DataFrame:
    """Exact N rows sampled at random (random_state=42 for reproducibility)."""
    n = min(n, len(df_in))
    sel = df_in.sample(n=n, random_state=42).copy()
    sel = sel.reset_index(drop=False)
    sel.rename(columns={"index": "orig_idx"}, inplace=True)
    return sel


# ── Dispatch ───────────────────────────────────────────────────────────────────
if N_ROWS is not None:
    work_df = select_n(df, N_ROWS)
elif CASE == "tiny":
    work_df = select_tiny(df)
elif CASE == "mid":
    work_df = select_mid(df)
else:
    work_df = select_full(df)

print(f"\nSelected {len(work_df)} rows:")
print(
    f"{'#':>2}  {'Agency':>8}  {'CAI':>12}  {'Stage':>14}  "
    f"{'Impact':>16}  {'HISP':>4}  {'PII':>3}  Use Case Name"
)
print("-" * 110)
for _i, _row in work_df.iterrows():
    _cai_s = (
        "NoneOfAbove"
        if "none of the above" in str(_row[col("commercial")]).lower()
        else "COTS"
    )
    print(
        f"{_i:>2}  {str(_row[col('abr')]):>8}  {_cai_s:>12}  "
        f"{str(_row[col('dev_stage')]).strip()[:14]:>14}  "
        f"{str(_row[col('impact')]).strip()[:15]:>16}  "
        f"{str(_row[col('hisp_supp')]).strip()[:3]:>4}  "
        f"{str(_row[col('pii')]).strip()[:3]:>3}  "
        f"{str(_row[col('name')])[:35]}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — CSV -> RDF ETL
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 3 — CSV -> RDF ETL")
print("=" * 70)

kg = Graph()
kg.bind("aiu",  AIU)
kg.bind("rdf",  RDF)
kg.bind("rdfs", RDFS)
kg.bind("owl",  OWL)
kg.bind("xsd",  XSD)
kg.bind("skos", SKOS)
kg.bind("prov", PROV)

# ── Shared InventorySnapshot ───────────────────────────────────────────────────
INV_IRI = AIU["inv2024"]
kg.add((INV_IRI, RDF.type, AIU["InventorySnapshot"]))
kg.add((INV_IRI, AIU["inventoryYear"], Literal("2024", datatype=XSD.gYear)))


def slugify(s: Any, maxlen: int = 30) -> str:
    """Safe IRI fragment from an arbitrary string."""
    s = re.sub(r"[^\w\s-]", "", str(s).strip())
    s = re.sub(r"[\s-]+", "_", s)
    return s[:maxlen].strip("_") or "UNK"


def lookup(val: Any, mapping: dict[str, Any], fallback: Any = None) -> Any:
    """Case-insensitive map lookup with strip + period removal.

    Falls back to longest-prefix match for CSV cells that append explanatory
    text after the concept label (e.g. 'Documentation has been developed: ...').
    """
    key = str(val).strip().lower().rstrip(".")
    if key in mapping:
        return mapping[key]
    best = None
    best_len = 0
    for label, iri in mapping.items():
        if key.startswith(label) and len(label) > best_len:
            best, best_len = iri, len(label)
    return best if best else fallback


def to_bool(val: Any) -> Literal | None:
    v = str(val).strip().lower()
    if v in ("yes", "true", "1"):
        return Literal(True, datatype=XSD.boolean)
    if v in ("no", "false", "0"):
        return Literal(False, datatype=XSD.boolean)
    first = v.split()[0].rstrip(".-\u2013\u2014") if v.split() else ""
    if first == "yes":
        return Literal(True, datatype=XSD.boolean)
    if first == "no":
        return Literal(False, datatype=XSD.boolean)
    return None


def add_time_node(
    g: Graph, prop: Any, rec_iri: Any, date_str: Any, suffix: str
) -> None:
    if not date_str or pd.isna(date_str) or str(date_str).strip() in ("", "nan"):
        return
    ti = AIU[f"ti_{str(rec_iri).split('#')[-1]}_{suffix}"]
    g.add((ti, RDF.type, AIU["TimeInstant"]))
    g.add((rec_iri, prop, ti))


def split_multival(val: Any, mapping: dict[str, Any]) -> list[Any]:
    """Split comma/semicolon-separated multi-value field and map each part."""
    if not val or pd.isna(val):
        return []
    results = []
    for part in re.split(r"[,;]", str(val)):
        mapped = lookup(part, mapping)
        if mapped:
            results.append(mapped)
    return results


# ── Per-row ETL ────────────────────────────────────────────────────────────────
ucr_iris: dict[int, Any] = {}
plan_iris: dict[int, Any] = {}
proc_iris: dict[int, Any] = {}

for i, row in work_df.iterrows():
    abr = slugify(nstr(row[col("abr")]) or nstr(row[col("agency")])[:8], 10)
    rid = f"2024_{abr}_{i}"

    ucr_iri = AIU[f"ucr_{rid}"]
    plan_iri = AIU[f"plan_{rid}"]
    proc_iri = AIU[f"proc_{rid}"]
    ucr_iris[i] = ucr_iri
    plan_iris[i] = plan_iri
    proc_iris[i] = proc_iri

    # ── Agency + Bureau nodes ──────────────────────────────────────────────────
    agency_iri = AIU[f"agency_{slugify(nstr(row[col('abr')]), 20)}"]
    bureau_iri = AIU[f"bureau_{slugify(nstr(row[col('bureau')]), 25)}"]
    if (agency_iri, RDF.type, AIU["Agency"]) not in kg:
        kg.add((agency_iri, RDF.type, AIU["Agency"]))
        kg.add(
            (agency_iri, RDFS.label,
             Literal(nstr(row[col("agency")]), datatype=XSD.string))
        )
    if (bureau_iri, RDF.type, AIU["Bureau"]) not in kg:
        kg.add((bureau_iri, RDF.type, AIU["Bureau"]))
        kg.add(
            (bureau_iri, RDFS.label,
             Literal(nstr(row[col("bureau")]), datatype=XSD.string))
        )

    # ── UseCaseRecord ──────────────────────────────────────────────────────────
    kg.add((ucr_iri, RDF.type, AIU["UseCaseRecord"]))
    kg.add(
        (ucr_iri, AIU["useCaseName"],
         Literal(nstr(row[col("name")]), datatype=XSD.string))
    )
    kg.add((ucr_iri, AIU["hasAgency"], agency_iri))
    kg.add((ucr_iri, AIU["hasBureau"], bureau_iri))
    kg.add((ucr_iri, AIU["partOfInventory"], INV_IRI))
    kg.add((ucr_iri, AIU["describesPlan"], plan_iri))
    kg.add((ucr_iri, AIU["describesProcess"], proc_iri))

    cai_val = lookup(row[col("commercial")], CAI_MAP)
    if cai_val:
        kg.add((ucr_iri, AIU["hasCommercialAIType"], cai_val))
    else:
        cai_raw = str(row[col("commercial")]).lower()
        fallback = (
            AIU["CAI_NoneOfTheAbove"] if "none" in cai_raw else AIU["CAI_Search"]
        )
        kg.add((ucr_iri, AIU["hasCommercialAIType"], fallback))

    is_full = "none of the above" in str(row[col("commercial")]).lower()

    # ── AIUseCasePlan ──────────────────────────────────────────────────────────
    purpose_text = nstr(row[col("purpose")])
    outputs_text = nstr(row[col("outputs")])
    plan_text = (purpose_text + " " + outputs_text).strip() or "No description."
    kg.add((plan_iri, RDF.type, AIU["AIUseCasePlan"]))
    kg.add(
        (plan_iri, AIU["purposeBenefitsText"],
         Literal(plan_text, datatype=XSD.string))
    )

    # ── AIUseCaseProcess ───────────────────────────────────────────────────────
    kg.add((proc_iri, RDF.type, AIU["AIUseCaseProcess"]))
    kg.add(
        (proc_iri, AIU["outputsText"],
         Literal(outputs_text or "N/A", datatype=XSD.string))
    )

    ta_val = lookup(row[col("topic_area")], TA_MAP)
    kg.add(
        (proc_iri, AIU["hasTopicArea"],
         ta_val if ta_val else AIU["TA_MissionEnabling"])
    )

    ds_val = lookup(row[col("dev_stage")], DS_MAP)
    kg.add(
        (proc_iri, AIU["hasDevelopmentStage"],
         ds_val if ds_val else AIU["DS_Initiated"])
    )

    it_val = lookup(row[col("impact")], IT_MAP)
    kg.add(
        (proc_iri, AIU["hasImpactType"],
         it_val if it_val else AIU["IT_Neither"])
    )

    # ── Full-record-only fields ────────────────────────────────────────────────
    if is_full:
        add_time_node(
            kg, AIU["hasInitiationTime"], proc_iri, row[col("date_init")], "init"
        )
        add_time_node(
            kg, AIU["hasAcqDevTime"], proc_iri, row[col("date_acq")], "acq"
        )
        add_time_node(
            kg, AIU["hasImplementationTime"],
            proc_iri, row[col("date_impl")], "impl"
        )
        add_time_node(
            kg, AIU["hasRetirementTime"], proc_iri, row[col("date_ret")], "ret"
        )

        dm_val = lookup(row[col("dev_method")], DM_MAP)
        if dm_val:
            kg.add((proc_iri, AIU["hasDevelopmentMethod"], dm_val))

        if str(row[col("hisp_supp")]).strip().lower() == "yes":
            hisp_val = lookup(row[col("hisp_name")], HISP_MAP)
            if hisp_val:
                kg.add((proc_iri, AIU["supportsHISP"], hisp_val))

        pii_b = to_bool(row[col("pii")])
        saop_b = to_bool(row[col("saop")])
        if pii_b is not None:
            kg.add((proc_iri, AIU["usesPII"], pii_b))
        if saop_b is not None:
            kg.add((proc_iri, AIU["saopReviewed"], saop_b))

        ddl_val = lookup(row[col("data_docs")], DDL_MAP)
        if ddl_val:
            kg.add((proc_iri, AIU["hasDataDocLevel"], ddl_val))

        for df_val in split_multival(row[col("demo_feat")], DF_MAP):
            kg.add((proc_iri, AIU["usesDemographicFeature"], df_val))

        cc_b = to_bool(row[col("custom_code")])
        if cc_b is not None:
            kg.add((proc_iri, AIU["customCodePresent"], cc_b))

        ca_val = lookup(row[col("code_access")], CA_MAP)
        if ca_val:
            kg.add((proc_iri, AIU["hasCodeAccess"], ca_val))

        ir_val = lookup(row[col("int_review")], IR_MAP)
        if ir_val:
            kg.add((proc_iri, AIU["hasInternalReviewLevel"], ir_val))

        tl_val = lookup(row[col("real_test")], TL_MAP)
        if tl_val:
            kg.add((proc_iri, AIU["hasTestingLevel"], tl_val))

        mm_val = lookup(row[col("monitor")], MM_MAP)
        if mm_val:
            kg.add((proc_iri, AIU["hasMonitoringMaturity"], mm_val))

        ai_b = to_bool(row[col("auto_impact")])
        if ai_b is not None:
            kg.add((proc_iri, AIU["autonomousImpact"], ai_b))

        ap_b = to_bool(row[col("appeal")])
        if ap_b is not None:
            kg.add((proc_iri, AIU["hasAppealProcess"], ap_b))

        oo_b = to_bool(row[col("opt_out")])
        if oo_b is not None:
            kg.add((proc_iri, AIU["hasOptOut"], oo_b))

        imp_ass_raw = str(row[col("impact_assess")]).strip().lower()
        if imp_ass_raw == "yes":
            assess_iri = AIU[f"assess_{rid}"]
            kg.add((assess_iri, RDF.type, AIU["AIImpactAssessmentProcess"]))
            kg.add((proc_iri, AIU["assessedBy"], assess_iri))

print(f"RDF graph built: {len(kg)} triples across {len(work_df)} records")

# Pre-assign blacklisted goals (universally applicable; excluded from LLM prompts)
for _plan_iri in plan_iris.values():
    for _bg_id in GOAL_BLACKLIST:
        kg.add((_plan_iri, AIU["hasBusinessGoal"], AIU[_bg_id.replace("aiu:", "")]))
_preassigned_triples = len(plan_iris) * len(GOAL_BLACKLIST)
print(f"Pre-assigned {_preassigned_triples} goal triple(s) "
      f"({', '.join(GOAL_BLACKLIST)}) to all plan nodes")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Business-goal tagging (Haiku + GPT-5.4-mini; Opus referee)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 4 — Business-goal tagging (Sonnet + GPT-5.4-mini; intersection on disagreement)")
print("=" * 70)
_triples_before_tagging = len(kg)  # baseline: ETL triples + pre-assigned goals


def _build_goal_prompt(
    name: str, purpose: str, outputs: str, topic: str, stage: str
) -> str:
    return (
        f"Use Case: {name}\n"
        f"Purpose/Benefits: {purpose[:1200]}\n"
        f"AI Outputs: {outputs[:300]}\n"
        f"Topic Area: {topic}\n"
        f"Development Stage: {stage}\n\n"
        "Business Goal Catalog:\n"
        "(Each entry: goal id/label, description, then example phrases that "
        "illustrate what the goal looks like in practice.)\n"
        f"{GOAL_CATALOG}\n\n"
        "Select 1 to 3 goal IDs from the catalog above that best describe "
        "the business purpose of this use case. Use the goal descriptions and "
        "illustrative phrases to understand what each goal means, then judge "
        "which goals apply based on the use case as a whole. "
        "Be conservative: when uncertain whether a goal applies, exclude it. "
        "Precision matters more than recall — a shorter, confident list is "
        "better than a longer speculative one. "
        "Always return at least 1 goal — if no goal fits well, choose the "
        "single best match from the catalog.\n"
        'Respond with JSON only, no prose: {"goals": ["aiu:BG_X_Y", ...]}'
    )


def _parse_goals(raw: str) -> list[str]:
    """Extract goals from structured cluster-first response or plain JSON.

    Looks for a 'GOALS: {...}' line first (Option B format).
    Falls back to parsing the whole response as JSON (legacy format).
    """
    # Primary: find GOALS: marker; JSON may be on the same line or the next
    lines = raw.splitlines()
    for i, line in enumerate(lines):
        if line.strip().upper().startswith("GOALS:"):
            json_part = line.strip()[line.strip().index(":") + 1:].strip()
            # If nothing after the colon, check the next line
            if not json_part and i + 1 < len(lines):
                json_part = lines[i + 1].strip()
            json_part = re.sub(r"^```[a-z]*\n?", "", json_part).rstrip("`").strip()
            try:
                data = json.loads(json_part)
                return [
                    g for g in data.get("goals", [])
                    if g in GOAL_ID_SET and g not in GOAL_BLACKLIST
                ][:5]
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

    # Fallback: treat entire response as JSON
    cleaned = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()
    try:
        data = json.loads(cleaned)
        return [
            g for g in data.get("goals", [])
            if g in GOAL_ID_SET and g not in GOAL_BLACKLIST
        ][:5]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


@retry(
    retry=retry_if_exception_type((anthropic.APIConnectionError, anthropic.RateLimitError)),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
)
def _tag_sonnet(prompt: str) -> list[str]:
    """Call Claude Sonnet and return filtered goal list."""
    resp = _anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_goals(resp.content[0].text.strip())


@retry(
    retry=retry_if_exception_type((openai.APIConnectionError, openai.RateLimitError)),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
)
def _tag_gpt(prompt: str) -> list[str]:
    """Call GPT-5.4-mini via Responses API with high reasoning effort."""
    resp = _openai_client.responses.create(
        model="gpt-5.4-mini",
        reasoning={"effort": "high"},
        max_output_tokens=2048,
        instructions=_SYSTEM,
        input=prompt,
    )
    return _parse_goals(resp.output_text or "")


def _tag_opus_referee(
    prompt: str,
    sonnet_goals: list[str],
    gpt_goals: list[str],
) -> tuple[list[str], str]:
    """Claude Opus arbitrates between Sonnet and GPT results.

    Returns (winning_goals, chosen_model) where chosen_model is "A" (Sonnet)
    or "B" (GPT-5.4-mini).

    The winning_goals written here are exactly what gets persisted to the TTL.
    If Opus returns no whitelisted goal IDs, falls back to the chosen model's
    original result so the TTL record is never left without goals.
    """
    # Extract only the use case header (name/purpose/outputs/topic/stage) from
    # the full prompt — stop before the catalog begins. This prevents Opus from
    # inheriting and following the structured format instructions in the catalog
    # section, which caused it to produce THEMES/EVALUATION/GOALS blocks instead
    # of a plain JSON verdict.
    header = prompt.split("\nBusiness Goal Catalog")[0].split("\nGoal Clusters")[0].strip()

    # Include descriptions only for the goals under dispute so Opus can reason
    # about the specific distinction without reading the full 38-goal catalog.
    contested_ids = list(set(sonnet_goals) | set(gpt_goals))
    contested_desc = "\n\n".join(
        f"{g['id']}: {g['label']}\n  {g['description'][:300]}"
        for g in GOALS
        if g["id"] in contested_ids
    )

    ref_prompt = (
        "Two AI models disagree on the business goal classification for this "
        "federal AI use case.\n\n"
        f"{header}\n\n"
        "Descriptions of the contested goals:\n"
        f"{contested_desc}\n\n"
        f"Model A (Claude Sonnet) selected: {sonnet_goals}\n"
        f"Model B (GPT-5.4-mini) selected: {gpt_goals}\n\n"
        "Which set better represents the primary business purpose of this use case? "
        "You may choose A, B, or propose a merged set drawn only from the contested "
        "goals listed above.\n"
        'Respond with JSON only, no prose: '
        '{"goals": ["aiu:BG_X_Y", ...], "chosen": "A" or "B"}'
    )
    resp = _anthropic_client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=_SYSTEM,
        messages=[{"role": "user", "content": ref_prompt}],
    )
    raw = resp.content[0].text.strip()

    # Opus may follow the cluster-first structured format (CLUSTERS/EVALUATION/GOALS)
    # from the embedded original prompt, producing a multi-section response. The
    # authoritative verdict is on the last line containing both "goals" and "chosen".
    # Search lines in reverse order so we find the final JSON verdict first.
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

    # Fallback: try parsing the whole response as JSON (plain response case)
    if data is None:
        cleaned = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()
        try:
            data = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return sonnet_goals, "A (parse fallback)"

    goals = [
        g for g in data.get("goals", [])
        if g in GOAL_ID_SET and g not in GOAL_BLACKLIST
    ][:5]
    chosen = str(data.get("chosen", "?"))
    # If every Opus goal ID failed whitelist/blacklist filtering, fall back
    # to the chosen model's original result to guarantee non-empty TTL output.
    if not goals:
        goals = sonnet_goals if chosen.startswith("A") else gpt_goals
        chosen = chosen + " (goal fallback)"
    return goals, chosen


def _log_disagreement(use_case_name: str, result: dict[str, Any]) -> None:
    """Append one disagreement record (disagreement_pct > 30) to the JSONL log."""
    intersection = sorted(set(result["sonnet"]) & set(result["gpt"]))
    entry = {
        "use_case_name": use_case_name,
        "sonnet_goals": result["sonnet"],
        "gpt_goals": result["gpt"],
        "intersection_goals": intersection,
        "final_goals": result["goals"],
        "disagreement_pct": result["disagreement_pct"],
        "prompt": result["prompt"],
    }
    with DISAGREE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def tag_goals_dual(
    name: str, purpose: str, outputs: str, topic: str, stage: str
) -> dict[str, Any]:
    """Tag one use case with both Sonnet and GPT; resolve disagreement by intersection.

    Returns a dict with keys:
      goals           -- final goal list written to the TTL (intersection on
                         disagreement, or the agreed set; falls back to union
                         if intersection is empty)
      agreed          -- True if Sonnet and GPT matched exactly
      sonnet          -- Sonnet goal list
      gpt             -- GPT goal list
      disagreement_pct -- symmetric-diff / union * 100 (0.0 if agreed)
      prompt          -- the full prompt string sent to both models
    """
    prompt = _build_goal_prompt(name, purpose, outputs, topic, stage)
    sonnet_goals = _tag_sonnet(prompt)
    gpt_goals = _tag_gpt(prompt)

    s_set = set(sonnet_goals)
    g_set = set(gpt_goals)

    if s_set == g_set:
        return {
            "goals": sonnet_goals,
            "agreed": True,
            "sonnet": sonnet_goals,
            "gpt": gpt_goals,
            "disagreement_pct": 0.0,
            "prompt": prompt,
        }

    sym_diff = s_set.symmetric_difference(g_set)
    union = s_set | g_set
    disagreement_pct = len(sym_diff) / len(union) * 100 if union else 0.0

    # Resolve by intersection; fall back to union if intersection is empty
    intersection = s_set & g_set
    final_goals = sorted(intersection) if intersection else sorted(union)

    return {
        "goals": final_goals[:5],
        "agreed": False,
        "sonnet": sonnet_goals,
        "gpt": gpt_goals,
        "disagreement_pct": disagreement_pct,
        "prompt": prompt,
    }


# ── Per-use-case tagging loop ──────────────────────────────────────────────────
goal_results: dict[int, dict[str, Any]] = {}
total_disagreed = 0   # any Sonnet != GPT
logged_count = 0      # disagreement_pct > 30 (written to JSONL)

print(
    f"\n{'#':>2}  {'Use Case Name':>35}  "
    f"{'Goals':>5}  {'Dis%':>5}  {'TTL source':>12}  Top goal"
)
print("-" * 88)

for i in range(len(work_df)):
    r = work_df.iloc[i]
    result = tag_goals_dual(
        name=nstr(r[col("name")]),
        purpose=nstr(r[col("purpose")]),
        outputs=nstr(r[col("outputs")]),
        topic=nstr(r[col("topic_area")]),
        stage=nstr(r[col("dev_stage")]),
    )
    goal_results[i] = result
    # result["goals"] is the intersection on disagreement, or agreed Sonnet set.
    final_goals = result["goals"]
    agreed = result["agreed"]
    dis_pct = result["disagreement_pct"]

    if not agreed:
        total_disagreed += 1
        if dis_pct > 30:
            logged_count += 1
            _log_disagreement(nstr(r[col("name")]), result)

    # Determine TTL source label for the console summary
    if agreed:
        ttl_src = "Sonnet"
    else:
        intersection = set(result["sonnet"]) & set(result["gpt"])
        ttl_src = "Intersect" if intersection else "Union"

    top = final_goals[0] if final_goals else "none"
    print(
        f"{i:>2}  {nstr(r[col('name')]):>35.35}  "
        f"{len(final_goals):>5}  "
        f"{dis_pct:>4.0f}%  "
        f"{ttl_src:>12}  {top}"
    )

    # Write referee/agreed goals to graph — this is the single source of truth
    # for what ends up in the TTL file.
    for gid in final_goals:
        kg.add((plan_iris[i], AIU["hasBusinessGoal"], AIU[gid.replace("aiu:", "")]))

_llm_tagged_triples = len(kg) - _triples_before_tagging
print(f"\nTotal triples after goal tagging: {len(kg)}")
print(f"  Pre-assigned goal triples : {_preassigned_triples} "
      f"({', '.join(GOAL_BLACKLIST)})")
print(f"  LLM-tagged goal triples   : {_llm_tagged_triples}")
print(
    f"Agreement: {len(work_df) - total_disagreed}/{len(work_df)} agreed, "
    f"{total_disagreed} disagreed ({logged_count} logged at >30%)"
)
if logged_count:
    print(f"Disagreement log (>30%): {DISAGREE_PATH}")


# ── Serialize to Turtle ────────────────────────────────────────────────────────
kg.serialize(destination=str(OUT_PATH), format="turtle")

# Annotate BG_* IRIs with inline prefLabel comments (human-readability aid)
_bg_labels: dict[str, str] = {}
for _bg in ont.subjects(RDF.type, AIU["BusinessGoalConcept"]):
    _local = str(_bg).split("#")[-1]
    _lbl = ont.value(_bg, SKOS.prefLabel)
    if _lbl:
        _bg_labels[_local] = str(_lbl)

_lines = OUT_PATH.read_text(encoding="utf-8").splitlines()
_annotated = []
for _line in _lines:
    _m = re.search(r"aiu:(BG_\w+)", _line)
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

ont_g = Graph()
ont_g.parse(str(ONT_PATH), format="turtle")
data_g = Graph()
data_g.parse(str(OUT_PATH), format="turtle")

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

viols: list[tuple[str, str]] = []
warns: list[tuple[str, str]] = []
for vr in results_g.subjects(RDF.type, SH["ValidationResult"]):
    sev = results_g.value(vr, SH["resultSeverity"])
    msg = results_g.value(vr, SH["resultMessage"])
    src = results_g.value(vr, SH["sourceShape"])
    focus = results_g.value(vr, SH["focusNode"])
    path = results_g.value(vr, SH["resultPath"])
    src_l = str(src).split("#")[-1] if src else "?"
    focus_l = str(focus).split("#")[-1] if focus else "?"
    path_l = str(path).split("#")[-1] if path else "(SPARQL)"
    entry = f"  [{src_l}] focus={focus_l}, path={path_l}: {str(msg)[:120]}"
    if sev == SH["Violation"]:
        viols.append((focus_l, entry))
    else:
        warns.append((focus_l, entry))

print(
    f"\nConforms: {conforms}  |  Violations: {len(viols)}  |  "
    f"Warnings: {len(warns)}"
)

record_viols: dict[str, list[str]] = {}
for focus_l, entry in viols:
    record_viols.setdefault(focus_l, []).append(entry)

if viols:
    print("\nViolations by record:")
    for rec, entries in sorted(record_viols.items()):
        print(f"  {rec}: {len(entries)} violation(s)")
        for e in entries[:3]:
            print(e)
        if len(entries) > 3:
            print(f"    ... {len(entries) - 3} more")
else:
    print("  No violations -- all records conform.")

if warns:
    print(f"\nWarnings ({len(warns)} total):")
    for _, e in warns[:5]:
        print(e)
    if len(warns) > 5:
        print(f"  ... {len(warns) - 5} more (PROV pipeline warnings expected)")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Final report
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 6 — Final Report")
print("=" * 70)

# Goal assignment statistics
all_goal_counts = [len(goal_results[i]["goals"]) for i in range(len(work_df))]
total_goals = sum(all_goal_counts)
mean_goals = total_goals / len(all_goal_counts) if all_goal_counts else 0.0

print(f"\nGoal assignment stats:")
print(f"  Mean goals/use case : {mean_goals:.2f}")
print(f"  Min goals           : {min(all_goal_counts)}")
print(f"  Max goals           : {max(all_goal_counts)}")

goal_freq: dict[str, int] = {}
for res in goal_results.values():
    for gid in res["goals"]:
        goal_freq[gid] = goal_freq.get(gid, 0) + 1

print(f"\nMost frequently assigned goals:")
for gid, freq in sorted(goal_freq.items(), key=lambda x: -x[1])[:8]:
    glabel = next((g["label"] for g in GOALS if g["id"] == gid), gid)
    print(f"  {gid}: {freq}x -- {glabel}")

print(f"\nFull goal table per use case:")
print(f"{'#':>2}  {'Name':>35}  {'Goals':>5}  {'Agreed':>6}  Assigned Goal IDs")
print("-" * 100)
for i in range(len(work_df)):
    r = work_df.iloc[i]
    res = goal_results[i]
    ids = res["goals"]
    agreed_s = "yes" if res["agreed"] else "NO"
    print(
        f"{i:>2}  {nstr(r[col('name')]):>35.35}  {len(ids):>5}  "
        f"{agreed_s:>6}  "
        f"{', '.join(g.replace('aiu:', '') for g in ids[:5])}"
    )

# Dual-LLM agreement statistics
agreed_count = sum(1 for r in goal_results.values() if r["agreed"])
_dis_pcts = [
    r["disagreement_pct"] for r in goal_results.values() if not r["agreed"]
]
_avg_dis = sum(_dis_pcts) / len(_dis_pcts) if _dis_pcts else 0.0
_intersect_count = sum(
    1 for r in goal_results.values()
    if not r["agreed"] and bool(set(r["sonnet"]) & set(r["gpt"]))
)
_union_count = total_disagreed - _intersect_count

print(f"\nDual-LLM Agreement Statistics:")
print(f"  Agreed (Sonnet == GPT)  : {agreed_count}/{len(work_df)}")
print(f"  Disagreed               : {total_disagreed}/{len(work_df)}")
if total_disagreed:
    print(f"  Avg disagreement %      : {_avg_dis:.1f}%")
    print(f"  Resolved by intersection: {_intersect_count}")
    print(f"  Resolved by union       : {_union_count}")
    print(f"  Logged (>30% threshold) : {logged_count}")
if logged_count:
    print(f"  Disagreement log        : {DISAGREE_PATH}")

# Summary block
_p = work_df
_full_mask = _p["_cai"].str.contains("none of the above", case=False, na=False)
_rgtb = _full_mask & (
    _p["_imp"].str.contains("rights", case=False, na=False)
    | _p["_imp"].str.contains("both", case=False, na=False)
)
_sftb = _full_mask & (
    _p["_imp"].str.contains("safety", case=False, na=False)
    | _p["_imp"].str.contains("both", case=False, na=False)
)
_hisp = _full_mask & (_p["_hisp"] == "yes")
_pii = _full_mask & (_p["_pii"] == "yes")

print(
    f"""
SUMMARY
=======
Case               : {CASE}
Rows selected      : {len(work_df)}
  Full+Rights/Both : {_rgtb.sum()}
  Full+Safety/Both : {_sftb.sum()}
  Full+HISP        : {_hisp.sum()}
  Full+PII         : {_pii.sum()}
RDF output         : {OUT_PATH}  ({OUT_PATH.stat().st_size // 1024} KB, {len(data_g)} triples)
Goal tagging       : Claude Sonnet + GPT-5.4-mini (intersection on disagreement)
  Agreed           : {agreed_count}/{len(work_df)}
  Disagreed        : {total_disagreed}/{len(work_df)} (intersection written to TTL)
  Resolved/intersect: {_intersect_count}
  Resolved/union   : {_union_count}
  Logged (>30%)    : {logged_count}{f" -> {DISAGREE_PATH.name}" if logged_count else ""}
SHACL              : conforms={conforms}, violations={len(viols)}, warnings={len(warns)}
"""
)

# ══════════════════════════════════════════════════════════════════════════════
# Write results markdown file
# ══════════════════════════════════════════════════════════════════════════════
_stem = OUT_PATH.stem   # e.g. "pilot_5_15" or "run_mid_20260407_123456"
RESULTS_MD_PATH = _HERE / f"etl_{_stem}_results.md"

_lf_preassigned = len(plan_iris) * len(GOAL_BLACKLIST)
_lf_llm = sum(len(r["goals"]) for r in goal_results.values())

_md_rows_header = (
    "| # | Agency | Type | Stage | Impact | HISP | PII | Use Case Name |\n"
    "|---|---|---|---|---|---|---|---|\n"
)
_md_rows = ""
for _i in range(len(work_df)):
    _r = work_df.iloc[_i]
    _cai_s = "COTS" if not str(_r["_cai"]).lower().startswith("none") else "Full"
    _md_rows += (
        f"| {_i} | {nstr(_r[col('agency')])} | {_cai_s} | "
        f"{nstr(_r[col('dev_stage')])[:30]} | {nstr(_r[col('impact')])} | "
        f"{nstr(_r[col('hisp_supp')])} | {nstr(_r[col('pii')])} | "
        f"{nstr(_r[col('name')])} |\n"
    )

_md_goals_header = (
    "| # | Use Case Name | Goals | Dis% | TTL Source | Agreed | Assigned Goal IDs |\n"
    "|---|---|---|---|---|---|---|\n"
)
_md_goals = ""
for _i in range(len(work_df)):
    _r = work_df.iloc[_i]
    _res = goal_results[_i]
    _ids = ", ".join(g.replace("aiu:", "") for g in _res["goals"])
    _agreed_s = "yes" if _res["agreed"] else "NO"
    _dis_s = f"{_res['disagreement_pct']:.0f}%" if not _res["agreed"] else "0%"
    _has_intersect = bool(set(_res["sonnet"]) & set(_res["gpt"]))
    _src = "Sonnet" if _res["agreed"] else ("Intersect" if _has_intersect else "Union")
    _md_goals += (
        f"| {_i} | {nstr(_r[col('name')])} | {len(_res['goals'])} | "
        f"{_dis_s} | {_src} | {_agreed_s} | {_ids} |\n"
    )

_md_freq = "| Goal ID | Label | Count |\n|---|---|---|\n"
for _gid, _freq in sorted(goal_freq.items(), key=lambda x: -x[1])[:10]:
    _glabel = next((g["label"] for g in GOALS if g["id"] == _gid), _gid)
    _md_freq += f"| {_gid} | {_glabel} | {_freq}/{len(work_df)} |\n"

_md_viols = ""
for _rec, _entries in sorted(record_viols.items()):
    _md_viols += f"| {_rec} | {len(_entries)} | {_entries[0].strip()[:100]} |\n"

_md = f"""# ETL Results — `etl.py --case {CASE}` ({_stem})

Run date: {datetime.now().strftime('%Y-%m-%d')}
Script: `etl.py` (Claude Sonnet + GPT-5.4-mini Responses API; intersection on disagreement)
Source: `inventory_2024.csv` ({len(work_df)} rows selected from 2,133 total)
Output: `{OUT_PATH.name}` ({OUT_PATH.stat().st_size // 1024} KB, {len(data_g)} triples)
Disagreement log: `{DISAGREE_PATH.name if logged_count else "none"}`

---

## Selected Records

{_md_rows_header}{_md_rows}
**Slot coverage (full records):**
- Full+Rights/Both: {_rgtb.sum()} (requirement: ≥3) {'✓' if _rgtb.sum() >= 3 else '✗'}
- Full+Safety/Both: {_sftb.sum()} (requirement: ≥3) {'✓' if _sftb.sum() >= 3 else '✗'}
- Full+HISP: {_hisp.sum()} (requirement: ≥3) {'✓' if _hisp.sum() >= 3 else '✗'}
- Full+PII: {_pii.sum()} (requirement: ≥3) {'✓' if _pii.sum() >= 3 else '✗'}

---

## RDF Output Summary

| Metric | Value |
|---|---|
| Total triples | {len(data_g)} |
| Pre-assigned goal triples ({', '.join(GOAL_BLACKLIST)}) | {_lf_preassigned} |
| LLM-tagged goal triples | {_lf_llm} |
| Output file size | {OUT_PATH.stat().st_size // 1024} KB |
| Nodes: UseCaseRecord | {len(work_df)} |
| Nodes: AIUseCasePlan | {len(work_df)} |
| Nodes: AIUseCaseProcess | {len(work_df)} |

---

## Business-Goal Tagging Results

{_md_goals_header}{_md_goals}
**Goal assignment statistics:**
- Mean goals per use case (LLM-tagged, excl. blacklisted): {mean_goals:.2f}
- Min: {min(all_goal_counts)}, Max: {max(all_goal_counts)}

### Top Goals by Frequency

{_md_freq}
### Dual-LLM Agreement Statistics

| Metric | Value |
|---|---|
| Agreed (Sonnet == GPT exact match) | {agreed_count}/{len(work_df)} ({100*agreed_count//len(work_df)}%) |
| Disagreements | {total_disagreed}/{len(work_df)} |
| Average disagreement % | {_avg_dis:.1f}% |
| Resolved by intersection | {_intersect_count} |
| Resolved by union (empty intersect) | {_union_count} |
| Logged (>30% threshold) | {logged_count} |

---

## SHACL Validation Results

**Conforms: {conforms} | Violations: {len(viols)} | Warnings: {len(warns)}**

| Record | Violations | Primary cause |
|---|---|---|
{_md_viols if _md_viols else "| — | 0 | All records conform |\n"}
"""

RESULTS_MD_PATH.write_text(_md, encoding="utf-8")
print(f"Results markdown : {RESULTS_MD_PATH}")

