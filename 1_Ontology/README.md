# AIU Ontology — Semantic Layer for the Federal AI Use Case Inventory

**Version:** 1.0 | **License:** CC0 1.0 | **Namespace:** `https://example.org/ai-usecase-ontology#` (`aiu:`)

---

## 1. Background and Motivation

The U.S. Office of Management and Budget (OMB) publishes an annual **Federal AI Use Case Inventory**, collecting submissions from all covered federal agencies. The 2023 and 2024 consolidated inventories contain approximately 2,133 use case records. The inventory is valuable as a compliance artifact but limited as an analytical resource. Its fields are predominantly free text or categorical strings. There is no shared vocabulary for what agencies are trying to accomplish, no graph structure connecting use cases to each other, and no mechanism for cross-year comparison at the semantic level.

This folder contains a **formal semantic layer** built to close those gaps. Its central purpose is to understand the **business aspects** of submitted AI use cases — what goals agencies are actually pursuing, which mission domains concentrate the most AI activity, and how risk and governance postures vary across goal types — while providing a foundation that can extend to new inventory years, new goal categories, and new analytical questions without structural disruption.


## 2. Architecture Overview

The semantic layer consists of three coordinated files:

```
taxonomy_bizGoals.md    ←  Human-readable taxonomy specification: 10 goal clusters,
                            39 sub-goals, NLP classification hints per cluster
aiu_ontology_ver1.ttl   ←  OWL ontology: all classes, properties, SKOS concept schemes,
                            and business goal taxonomy individuals
aiu_shapes.ttl          ←  SHACL shapes: data validation with conditional gate logic
                            (imports the ontology)
```

Supporting documents in this directory:

```
aiu_inventory_field_mapping.md          ←  Authoritative field → predicate mapping for
                                           all 67 OMB inventory fields
aiu_ontology_ver1.md                    ←  Narrative design documentation
aiu_validation_guide.md                 ←  Guide for the SHACL unit-test script
guide_Identifying Cross-Cutting Goals.md ←  Methodology for cross-cutting goal detection
```

### Ontology stack

The `aiu:` domain layer is built on top of mature, reused upper and mid-level ontologies rather than inventing new foundational categories:

```
BFO 2020  (ISO/IEC 21838-2:2021)          upper ontology — continuant/occurrent distinctions,
  │                                         roles, functions, temporal instants
  ├─ CCO v2.0  (DOD/ODNI/CDAO standard)   organizations, planned acts, artifacts,
  │                                         directives, objectives
  ├─ IAO                                   information content entities, documents,
  │                                         plan specifications, datasets
  ├─ PROV-O                                provenance — entity, agent, activity;
  │                                         mapped to BFO (Prudhomme et al. 2025)
  └─ SKOS                                  concept schemes for controlled vocabularies
       │                                    and the business goal taxonomy
       └─ aiu:  (this ontology)            federal AI use cases, business goals,
                                            risk roles, governance, lifecycle
```

CCO v2.0 is the natural mid-level choice: in January 2024, the U.S. Department of Defense, ODNI, and CDAO formally adopted CCO and BFO as baseline standards for formal federal ontologies.

---

## 3. Methodology

### 3.1 Core Modeling Pattern

Every inventory row is decomposed into four related entities:

| Entity | OWL class | Superclass | Role |
|---|---|---|---|
| `UseCaseRecord` | `aiu:UseCaseRecord` | `IAO:document`, `prov:Entity` | The inventory row itself — anchors agency, year, gate field |
| `AIUseCasePlan` | `aiu:AIUseCasePlan` | `IAO:plan specification`, `CCO:Directive ICE` | What the use case is designed to do; receives business goal tags |
| `AIUseCaseProcess` | `aiu:AIUseCaseProcess` | `CCO:Planned Act` | The real-world process in which an AI system is deployed |
| `InventorySnapshot` | `aiu:InventorySnapshot` | `IAO:document` | One node per inventory year; anchors records to named graphs |

Key relations:

```
UseCaseRecord  ──aiu:describesPlan──►   AIUseCasePlan
UseCaseRecord  ──aiu:describesProcess─► AIUseCaseProcess
UseCaseRecord  ──aiu:partOfInventory──► InventorySnapshot
AIUseCasePlan  ──aiu:hasPlannedProcess► AIUseCaseProcess
AIUseCasePlan  ──aiu:hasBusinessGoal──► BusinessGoalConcept  ← primary analytical edge
```

The separation of record, plan, and process is deliberate: it allows provenance (who reported what) to be tracked at the record level, goal intent to be attached to the plan, and operational/risk properties to be attached to the process.

### 3.2 Business Goals as the Central Analytical Lens

Business goals are the primary mechanism for extracting structured, graph-queryable knowledge from the free-text fields of the inventory. They transform unstructured agency submissions into a navigable property graph.

The pipeline works as follows:

1. **Source text:** `11_purpose_benefits` (primary) and `12_outputs` (secondary) are free-text fields submitted by agencies. They describe what the use case is for and what the AI system produces.
2. **Classification:** A LLM call assigns 0–5 `aiu:BG_*` goal IRIs per use case, guided by the full 39-goal catalog and agency context (topic area, development stage). The model bridges government/technical language to taxonomy labels without requiring shared tokens.
3. **Graph edges:** Each assignment becomes an `aiu:hasBusinessGoal` triple on the `AIUseCasePlan` node — a typed, traversable edge in the knowledge graph.
4. **Analytics:** These edges enable goal frequency counts, goal–goal co-occurrence networks, bipartite projections, community detection, and cross-year trend comparisons — none of which are possible from the raw CSV.

### 3.3 Business Goal Taxonomy

The taxonomy (`taxonomy_bizGoals.md`) is organized as a two-level hierarchy:

| Cluster | Label | Sub-goals |
|---|---|---|
| BG_1 | Strategic and Business Model Goals | 4 |
| BG_2 | Market, Customer, and Revenue Goals | 4 |
| BG_3 | People, Culture, and Organizational Goals | 4 |
| BG_4 | Operations, Process, and Efficiency Goals | 4 |
| BG_5 | Financial Management and Risk Goals | 4 |
| BG_6 | Technology and Innovation Goals | 4 |
| BG_7 | Regulatory, Legal, and Compliance Goals | 4 |
| BG_8 | Data, Analytics, and AI Goals | 4 |
| BG_9 | Ecosystem and Partnership Goals | 3 |
| BG_10 | Safety, Security, and Resilience Goals | 4 |

**10 clusters, 39 sub-goals.** Each sub-goal in `taxonomy_bizGoals.md` includes a description, characteristic phrases, and a `lookup-fields` section that maps to specific inventory field names — the NLP classification hints used to construct the LLM prompt.

In the ontology, the taxonomy uses a **dual OWL+SKOS pattern** that preserves OWL-DL compatibility:

```turtle
# OWL class layer: BusinessGoalConcept ⊑ CCO:Objective
aiu:BusinessGoalConcept a owl:Class ;
    rdfs:subClassOf cco:ont00000476 .   # CCO Objective

# SKOS instance layer: each sub-goal is simultaneously an
# owl:NamedIndividual, a skos:Concept, and an aiu:BusinessGoalConcept
aiu:BG_4_1 a skos:Concept, owl:NamedIndividual, aiu:BusinessGoalConcept ;
    skos:prefLabel "Process efficiency and waste reduction"@en ;
    skos:broader aiu:BG_4 ;
    skos:inScheme aiu:BusinessGoalTaxonomy .
```

This pattern supports multi-goal tagging, taxonomy traversal via `skos:broader`/`skos:narrower`, and SPARQL queries without the OWL "Direct Mixing" anti-pattern.

### 3.4 Enumerated Fields as SKOS ConceptSchemes

Fifteen categorical inventory fields are modeled as SKOS `ConceptScheme` individuals with `owl:NamedIndividual` concept members. Use cases link to these via object properties — not string literals — making them first-class graph nodes.

| Scheme | Inventory field | IRI prefix | # values |
|---|---|---|---|
| `CommercialAITypeScheme` | `10_commercial_ai` | `aiu:CAI_*` | 20 |
| `TopicAreaScheme` | `8_topic_area` | `aiu:TA_*` | 10 |
| `DevStageScheme` | `16_dev_stage` | `aiu:DS_*` | 5 |
| `ImpactTypeScheme` | `17_impact_type` | `aiu:IT_*` | 4 |
| `DevMethodScheme` | `22_dev_method` | `aiu:DM_*` | 3 |
| `HISPScheme` | `25_hisp_name` | `aiu:HISP_*` | 38 |
| `DemoFeatureScheme` | `35_demo_features` | `aiu:DF_*` | 12 |
| `CodeAccessScheme` | `38_code_access` | `aiu:CA_*` | 3 |
| `DataDocLevelScheme` | `34_data_docs` | `aiu:DDL_*` | 4 |
| `InternalReviewScheme` | `50_internal_review` | `aiu:IR_*` | 4 |
| `TestingLevelScheme` | `53_real_world_testing` | `aiu:TL_*` | 5 |
| `MonitoringMaturityScheme` | `56_monitor_postdeploy` | `aiu:MM_*` | 4 |

This enables graph queries like "which development stages are most associated with rights-impacting use cases?" without any string matching or post-hoc parsing.

### 3.5 SHACL Validation Design

Validation uses three shape tiers with conditional gate logic implemented via SPARQL targets (`sh:SPARQLTarget`):

```
CoreShape           ── fires for ALL records
  │   (name, agency, stage, impact type, plan/process links)
  │
  ├── FullRecordProcessShape   ── fires only when commercial_ai = "None of the Above"
  │     (§2–4 conditional fields, date properties, data docs, code access, etc.)
  │
  └── RiskRecordShape          ── fires only when full record AND impact ≠ Neither
        │   AND stage ∈ {ImplAssess, OpsMaint}
        │   (testing level, monitoring maturity, autonomous impact)
        │
        └── RightsRecordShape  ── fires only when impact ∈ {Rights, Both}
              (appeal process, opt-out — rights-specific requirements)
```

The gate field `10_commercial_ai` is what distinguishes COTS records (one of 19 commercial tool types) from full records (`CAI_NoneOfTheAbove`). COTS records only need to satisfy `CoreShape`; all §2–5 conditional shapes are silent for them.

All SHACL shapes use `advanced=True` (required for `sh:SPARQLTarget`) and `inference="none"` (because BFO/CCO/IAO are not locally available for OWL reasoning). Pass the ontology as `ont_graph` to supply class and property metadata without triggering import resolution.

A five-test synthetic validation suite (`aiu_validation.py`) verifies gate logic after any edit to either TTL file:

| Test | Scenario | Expected |
|---|---|---|
| A | COTS-only record | `conforms=True`, 0 violations |
| B | Full record, Neither/Initiated | `conforms=False`, 1 violation (date required) |
| C | Rights/ImplAssess, all fields present | `conforms=True`, 0 violations |
| D | Rights/ImplAssess, all fields missing | `conforms=False`, 17 violations |
| E | Safety/ImplAssess, no rights fields | `conforms=True`, 0 violations |

### 3.6 Graph Analytics Design

The ontology is structured to support a range of graph-analytic questions without additional preprocessing:

| Sample Analytic Questions | Graph pattern |
|---|---|
| Goal frequency per year | `AIUseCasePlan ──hasBusinessGoal──► BG_* ◄──partOfInventory── InventorySnapshot` |
| Goal co-occurrence | Project bipartite (Plan ↔ Goal) onto goal–goal edges |
| Impactful goal clusters | Join goals with `hasImpactType`, `usesPII`, `hasRiskRole` |
| Equity dimension | Join goals with `usesDemographicFeature`, `hasAppealProcess`, `hasOptOut` |
| Topic-goal heatmap | Cross-tab `hasTopicArea` × `hasBusinessGoal` |
| Duplication candidates | `aiu:possibleDuplicateOf` edges (symmetric; populated by entity resolution) |
| Cross-year continuity | `aiu:continuesFrom` edges (directed; 2024 → 2023 predecessor) |
| Temporal lifecycle | `hasInitiationTime`, `hasAcqDevTime`, `hasImplementationTime` per `InventorySnapshot` |

---

## 4. Files in This Directory

| File | Format | Role | Status |
|---|---|---|---|
| `aiu_ontology_ver1.ttl` | Turtle (OWL) | Classes, properties, all SKOS ConceptSchemes, 49 `BusinessGoalConcept` individuals | Stable v1 |
| `aiu_shapes.ttl` | Turtle (SHACL) | Data validation shapes with SPARQL gate logic | Stable v1 |
| `taxonomy_bizGoals.md` | Markdown | Human-readable taxonomy: 10 clusters, 39 sub-goals, NLP classification hints | Stable v1 |
| `aiu_inventory_field_mapping.md` | Markdown | Authoritative field → predicate mapping for all 67 OMB fields; gap table | Stable v1 |
| `aiu_ontology_ver1.md` | Markdown | Narrative design documentation: modeling choices, reuse rationale, SPARQL examples | Stable v1 |
| `aiu_validation_guide.md` | Markdown | Guide for the SHACL unit-test script; expected output; failure interpretation | Stable v1 |
| `guide_Identifying Cross-Cutting Goals.md` | Markdown | Methodology for identifying cross-cutting goals in NL descriptions | Reference |

---

## 5. Field Coverage Summary

The OMB data dictionary defines **67 fields across 5 sections**. Current mapping status:

| Section | Total fields | Mapped | Partially mapped | Not yet mapped |
|---|---|---|---|---|
| §1 Identifiers & Classification | 10 | 9 | 0 | 1 |
| §2 Use Case Summary | 14 | 8 | 1 | 5 |
| §3 Data and Code | 9 | 6 | 0 | 3 |
| §4 Enablement & Infrastructure | 12 | 3 | 0 | 9 |
| §5 Risk Management | 13 | 7 | 0 | 6 |
| **Derived / computed** | — | 8 | — | — |
| **Total** | **67** | **41** | **1** | **24** |

The three highest-priority unmapped fields (analytically significant for compliance and equity):

| Field | Content | Priority |
|---|---|---|
| `55_independent_eval` | Independent evaluation status (5 levels incl. CAIO waiver) | High |
| `59_ai_notice` | AI notice mechanism to affected individuals (8 options) | High |
| `61_adverse_impact` | Whether adverse impact assessment was conducted (rights cases) | High |

See `aiu_inventory_field_mapping.md` §4 for the complete gap table with priorities.

---

## 6. Validation Quick Start

```bash
pip install rdflib pyshacl anthropic pandas
```

To validate a data file against the shapes:

```python
import pyshacl
from rdflib import Graph

ont_g = Graph()
ont_g.parse("aiu_ontology_ver1.ttl", format="turtle")

data_g = Graph()
data_g.parse("your_data.ttl", format="turtle")

conforms, results_g, results_text = pyshacl.validate(
    data_g,
    shacl_graph="aiu_shapes.ttl",
    ont_graph=ont_g,
    inference="none",      # BFO/CCO/IAO not locally available; disable OWL inference
    allow_warnings=True,   # PROV-O warnings do not block conforms=True
    abort_on_first=False,
    advanced=True,         # required for sh:SPARQLTarget gate logic
)

print(conforms)
print(results_text)
```

`inference="none"` is mandatory. The ontology declares `owl:imports` for BFO, CCO, IAO, and PROV-O, none of which are locally resolvable. Attempting OWL inference will raise import-resolution errors.

---

## 7. Namespaces and Key IRIs

| Prefix | IRI | Role |
|---|---|---|
| `aiu:` | `https://example.org/ai-usecase-ontology#` | Domain ontology |
| `bfo:` | `http://purl.obolibrary.org/obo/` | BFO 2020 upper ontology |
| `cco:` | `https://www.commoncoreontologies.org/` | CCO v2.0 mid-level |
| `iao:` | `http://purl.obolibrary.org/obo/IAO_` | Information Artifact Ontology |
| `prov:` | `http://www.w3.org/ns/prov#` | PROV-O provenance |
| `skos:` | `http://www.w3.org/2004/02/skos/core#` | SKOS taxonomy |
| `xsd:` | `http://www.w3.org/2001/XMLSchema#` | Datatypes |

---

## 8. Known Gaps and Roadmap

The ontology and ETL pipeline are at a validated pilot stage. The following gaps are known and tracked, organized by type and priority.

### 8.1 Unmapped Inventory Fields

**High priority** — these fields are directly relevant to compliance reporting and equity analysis. Their absence limits the graph's utility for governance questions:

| Field | Content | Impact if missing |
|---|---|---|
| `55_independent_eval` | Independent evaluation status (5 levels incl. CAIO waiver) | Cannot assess compliance posture per use case |
| `59_ai_notice` | AI notice mechanism to individuals (8 options) | Cannot analyze transparency practices for rights-impacting cases |
| `61_adverse_impact` | Whether adverse impact assessment was conducted | Cannot distinguish rights-impacting cases that completed equity review |

**Medium priority** — useful for richer mission and equity analytics:

| Field | Content |
|---|---|
| `26_public_service` | Public-facing vs. internal service (relevant for HISP use cases) |
| `27_public_info` | Whether use case disseminates information to the public |
| `49_existing_reuse` | Level of code/platform reuse from existing agency AI (4 levels) |
| `51_extension_request` | Whether agency requested compliance extension under M-24-10 |
| `62_disparity_mitigation` | Disparity mitigation description (free text) |
| `63_stakeholder_consult` | Stakeholder consultation method (7 options) |

**Low priority** — operational metadata; useful but not analytically blocking:

`23_contract_piids`, `28_iqa_compliance`, `31_data_catalog`, `42_dev_tools_wait`, `43_infra_provisioned`, `45_compute_request`, `47_timely_resources`, `66_no_appeal_reason`

### 8.2 ETL Pipeline Gaps

**Full-scale run not yet executed.** The ETL has been validated on a 15-record pilot (413 triples, 18 SHACL violations all confirmed as genuine data gaps). The full 2,133-record run and the complete SHACL validation pass are pending. Recommended approach: batch in chunks of ~200 rows, accumulate into one graph, validate once with pySHACL.

**2025 inventory not yet ingested.** Cross-year trend analysis requires at least 2 reporting years to be loaded into the same graph or into year-labeled named graphs.

**PROV-O fields not yet populated.** The OWL restrictions on `UseCaseRecord` require `prov:wasAttributedTo` (linking to `aiu:Agency`) and `prov:generatedAtTime` (inventory snapshot timestamp). These are currently declared as `sh:Warning` in SHACL (not violations) because they depend on a provenance enrichment pass that has not yet been run. Once populated, the corresponding shapes should be promoted to `sh:Violation` severity.

### 8.3 Ontology and Shapes Gaps

**OWL inference disabled by design.** BFO 2020, CCO v2.0, IAO, and PROV-O are declared as `owl:imports` but are not locally cached. pySHACL validation must run with `inference="none"`. This means OWL class hierarchy reasoning (e.g., inferring that an `aiu:Agency` is a `cco:ont00001180`) is not active at validation time. Locally caching the imported ontologies and enabling `inference="rdfs"` or `"owlrl"` would strengthen the validation but requires resolving import IRIs.

**`aiu:TimeInstant` has no literal constraints.** The four date properties (`hasInitiationTime`, `hasAcqDevTime`, `hasImplementationTime`, `hasRetirementTime`) range over `aiu:TimeInstant` nodes, but the ETL currently stores dates as bare string literals on those nodes rather than `xsd:date` typed values. A dedicated `TimeInstantShape` with a `sh:datatype xsd:date` constraint and a SPARQL guard for the appropriate stage is needed before temporal analytics can be computed reliably.

**`skos:altLabel` synonyms not yet populated.** The ontology design documentation (`aiu_ontology_ver1.md` §4.2) calls for `skos:altLabel` entries on `BusinessGoalConcept` individuals, derived from the `lookup-fields` sections in `taxonomy_bizGoals.md`. These synonym cues would improve LLM prompt quality and enable keyword-based fallback classification. They have not yet been added to the TTL.

**Governance role instances not yet created.** The ontology defines `aiu:SystemOwnerRole`, `aiu:DeveloperRole`, `aiu:OperatorRole`, and `aiu:OversightRole` as BFO role classes. No instance data has been created for these roles yet; the relevant inventory fields (`system_owner`, `SAOP`, `bureau`) are captured as literals or agency nodes rather than as role bearer triples.

### 8.4 Analytics and Graph Database Gaps

**No property graph database loaded.** The analytic affordances described in §3.6 are designed into the ontology structure but have not yet been executed. The conversion from RDF to a property graph (via Neosemantics or rdflib-neo4j), the loading into a graph database, and the execution of community detection, centrality, and co-occurrence algorithms are all pending.

**Entity resolution pipeline not implemented.** The `aiu:possibleDuplicateOf` (symmetric) and `aiu:continuesFrom` (directed) predicates are defined and ready. The entity resolution pipeline — comparing use case name similarity, agency, topic area, and goal neighborhood across 2023 and 2024 — has not been built. This is a prerequisite for meaningful cross-year trend analysis at the use case level.

**Goal taxonomy coverage for federal-mission-specific domains.** The 39-sub-goal taxonomy was designed around standard business management goals and maps well to the federal AI use case population. However, mission-specific domains — defense, intelligence, law enforcement, emergency management — may benefit from additional sub-goals or cluster extensions. The taxonomy is extensible by design: new `owl:NamedIndividual` SKOS Concepts under existing `skos:broader` relations do not require structural changes to existing data.

### 8.5 Prioritized Roadmap

**Near-term (next milestone):**
- Run full 2,133-record ETL; accumulate triples; run SHACL validation pass; report violation breakdown by agency and stage
- Ingest 2023 inventory under a separate `InventorySnapshot` node
- Populate PROV-O fields (`prov:wasAttributedTo`, `prov:generatedAtTime`) and promote shapes to `sh:Violation`

**Medium-term:**
- Add high-priority unmapped fields: `55_independent_eval`, `59_ai_notice`, `61_adverse_impact`, `51_extension_request`
- Add `skos:altLabel` synonyms to all 39 `BusinessGoalConcept` individuals
- Implement `aiu:TimeInstant` date parsing with `xsd:date` typed literals
- Build entity resolution pipeline; populate `aiu:possibleDuplicateOf` and `aiu:continuesFrom` triples

**Longer-term:**
- Load into property graph database; execute community detection, centrality, and co-occurrence analyses
- Cache BFO/CCO/IAO/PROV-O locally; enable `inference="rdfs"` for stronger SHACL validation
- Extend taxonomy with federal-mission-specific sub-goals based on pilot analytics findings
- Add medium-priority unmapped fields (`26`, `27`, `49`, `62`, `63`) and governance role instances

---

## 9. License

This project is in the worldwide public domain. See [LICENSE.md](../LICENSE.md) for details.

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
