# AI Use Case Ontology (BFO-Aligned) — v2.0

## 1. Purpose and Scope

This document describes a Basic Formal Ontology (BFO)-aligned ontology for modeling U.S. Federal AI use cases, business goals, risks, and governance. It is intended as a reference you can share with technical and non-technical stakeholders to explain how the ontology is structured and why it was designed this way.

The ontology is designed to:
- Represent the 2023/2024 Federal AI Use Case Inventory data in a semantically rich way.
- Attach AI use cases to a reusable taxonomy of business goals.
- Capture risk, governance, and lifecycle information needed for compliance and portfolio analysis.
- Support import/export via JSON and analysis via knowledge-graph databases and graph algorithms.

## 2. Design Objectives

The ontology is guided by the following objectives:

1. **BFO alignment and reuse.** Reuse mature, BFO-based mid-level ontologies (CCO v2.0, IAO, OMRSE, IOF) rather than inventing new foundational categories.
2. **Direct support for the Federal AI Use Case Inventory.** Provide a clear mapping for all essential fields in the OMB data dictionary (67 fields, 5 sections).
3. **First-class business goals.** Treat business goals as explicit concepts in a SKOS-backed taxonomy so they can be tagged, aggregated, and analyzed.
4. **Graph-analytics readiness.** Make entities and relations explicit in a way that supports goal frequencies, co-occurrences, temporal trends, duplication analysis, and centrality/community algorithms.
5. **Extensibility and governance.** Allow the ontology to evolve (e.g., new goal categories, risk types, governance mechanisms) without breaking existing data.

## 3. Foundational Ontologies and Reuse Stack

### 3.1 Basic Formal Ontology (BFO 2020) and Relation Ontology (RO)

- **BFO 2020** (ISO/IEC 21838-2:2021) provides the upper-level distinctions between continuants (e.g., organizations, systems) and occurrents (e.g., processes, assessments), plus categories such as role, function, disposition, and temporal region.
- **RO** (and extended RO) provides generic relations like `part_of`, `has_part`, `participates_in`, `has_participant`, and process-time relations.

The BFO 2020 import IRI is `http://purl.obolibrary.org/obo/bfo/2020/bfo-core.owl`. All BFO class IRIs (e.g., `BFO_0000023` for role, `BFO_0000015` for process) are stable across BFO 2.0 and BFO 2020.

**BFO temporal classes used:** `BFO_0000203` (temporal instant — a single point in time, introduced in BFO 2020) is used as the superclass for `aiu:TimeInstant`. Do not use `BFO_0000148` (zero-dimensional temporal region, a set of instants) as a proxy for a single lifecycle date.

These are used to ensure the ontology follows well-understood patterns for roles, processes, and participation.

### 3.2 Information Artifact Ontology (IAO)

- **IAO** provides the core notion of **information content entity (ICE)**, including documents, datasets, data items, and plan specifications.
- We reuse IAO's `plan specification` and directive information content entity patterns to model **AI use case plans** and governance policies.

This allows us to distinguish between information about a use case (records, plans, assessments) and the use case processes themselves.

### 3.3 Common Core Ontologies (CCO v2.0)

- **CCO v2.0** (released November 6, 2024; import IRI: `https://www.commoncoreontologies.org/AllCoreOntology`) provides mid-level ontologies for agents, activities, and information.
- In January 2024, the DOD, ODNI, and CDAO formally adopted CCO and BFO as the baseline standards for formal federal ontologies. This makes CCO the natural choice for a federal AI governance ontology.
- We reuse key CCO v2.0 classes (all IRIs under `https://www.commoncoreontologies.org/`):
  - `ont00001180` (Organization) for agencies and bureaus.
  - `ont00000228` (Planned Act, formerly IntentionalAct) for AI use case processes and lifecycle activities. There is no `PlannedProcess` class in CCO; the correct class is **Planned Act** (`ont00000228`).
  - `ont00000965` (Directive Information Content Entity) for plans, policies, and business goals.
  - `ont00000476` (Objective) as the CCO superclass for `aiu:BusinessGoalConcept`.
  - `ont00000995` (Artifact) for AI systems.

CCO gives us a reusable backbone for "who does what, in which process, under which objectives and policies."

### 3.4 OMRSE and IOF/Engineering Ontologies

- **OMRSE** provides patterns for social roles and organizational structures; we reuse these for richer modeling of governance roles (e.g., system owner, SAOP, CAIO, oversight roles).
- **IOF** (`https://spec.industrialontologies.org/ontology/core/Core/`) and BFO-based engineering ontologies provide patterns for **artifacts** (AI systems), **functions** (what systems are designed to do), and lifecycle processes.

### 3.5 PROV-O Mapping and Risk Ontologies

- **PROV-O** provides a standard vocabulary for provenance (agents, entities, activities). The established BFO mapping is: `prov:Activity ≡ bfo:process` and `prov:Agent rdfs:subClassOf bfo:MaterialEntity`. OWL mapping files are at `github.com/BFO-Mappings/PROV-to-BFO` (Prudhomme et al., *Scientific Data*, 2025, doi:10.1038/s41597-025-04580-1). `aiu:UseCaseRecord` is declared `rdfs:subClassOf prov:Entity` to enable provenance tracking of inventory records. `<http://www.w3.org/ns/prov-o#>` is a formal `owl:imports` entry alongside BFO, RO, IAO, CCO, and SKOS, so PROV axioms are part of the reasoning space.
- For **AI risk**, we use the conceptual schema from the AIRO ontology (risk source → hazardous event → impact → control/mitigation) as a design pattern, implemented using BFO roles and CCO planned acts. Note: AIRO itself is built on the W3C Data Privacy Vocabulary (DPV) ecosystem, not BFO, and is not directly imported. The W3C DPVCG AI Extension (`https://www.w3id.org/dpv/ai#`) provides additional AI-specific risk vocabulary for regulatory alignment.

## 4. Core Modeling Choices

### 4.1 Use Case Record, Plan, Process, and Inventory Snapshot

We distinguish four related entities:

- **UseCaseRecord (`aiu:UseCaseRecord`)** — an `IAO:document` and `prov:Entity` corresponding to a row in the Federal AI Use Case Inventory for a specific year. OWL restrictions constrain it to be attributed to some `aiu:Agency` (`prov:wasAttributedTo`) and to carry a generation timestamp (`prov:generatedAtTime`).
- **AIUseCasePlan (`aiu:AIUseCasePlan`)** — an `IAO:plan specification` and `CCO:Directive Information Content Entity` (ont00000965) that prescribes what the AI-enabled process should do.
- **AIUseCaseProcess (`aiu:AIUseCaseProcess`)** — a `CCO:Planned Act` (ont00000228) representing the real-world process in which an AI system is deployed and operated.
- **InventorySnapshot (`aiu:InventorySnapshot`)** — an `IAO:document` representing the complete annual inventory (e.g., the 2023 or 2024 edition). Used to anchor `UseCaseRecord` instances to a named graph and support cross-year provenance.

Key relations:
- `aiu:UseCaseRecord aiu:describesPlan aiu:AIUseCasePlan`
- `aiu:UseCaseRecord aiu:describesProcess aiu:AIUseCaseProcess`
- `aiu:UseCaseRecord aiu:partOfInventory aiu:InventorySnapshot`
- `aiu:AIUseCasePlan aiu:hasPlannedProcess aiu:AIUseCaseProcess`

### 4.2 Business Goals and Taxonomy

The business-goal taxonomy is represented using a two-layer pattern that preserves OWL-DL compatibility:

- **OWL class layer:** `aiu:BusinessGoalConcept` is an OWL class (subclass of CCO Objective `ont00000476`) that represents the type "business goal." It is not a subclass of `skos:Concept`.
- **SKOS instance layer:** Each taxonomy node (10 goal clusters, ~39 sub-goals) is an `owl:NamedIndividual` that is simultaneously an instance of `skos:Concept` and of `aiu:BusinessGoalConcept`. This keeps OWL-DL compliant: individuals may be typed as members of both an OWL class and a SKOS class without the "Direct Mixing" anti-pattern (which arises only when the same resource is both an `owl:Class` and an `owl:NamedIndividual`).

```turtle
# Correct OWL-DL pattern — individual typed as both OWL class instance and SKOS Concept
aiu:BG_4_1 a skos:Concept, owl:NamedIndividual, aiu:BusinessGoalConcept ;
    skos:prefLabel "Process efficiency and waste reduction"@en ;
    skos:broader aiu:BG_4 ;
    skos:inScheme aiu:BusinessGoalTaxonomy .
```

The `aiu:BusinessGoalTaxonomy` is a `skos:ConceptScheme` (`owl:NamedIndividual`), with `skos:topConceptOf` on the 10 top-level cluster concepts and `skos:broader`/`skos:narrower` for the sub-goal hierarchy.

Use cases are linked to goals via:
- `aiu:AIUseCasePlan aiu:hasBusinessGoal aiu:BG_4_1` (ObjectProperty, range `aiu:BusinessGoalConcept`)

`skos:altLabel` entries (synonym/keyword cues for NLP classification) should be derived from the `lookup-fields` in `taxonomy_bizGoals.md` and added to each Concept.

This pattern:
- Supports multi-goal tagging per use case.
- Enables analytics like goal frequency, co-occurrence, and clustering.
- Respects the taxonomy hierarchy while remaining compatible with SPARQL and SKOS tooling.

SKOS (`<http://www.w3.org/2004/02/skos/core>`) is formally included in `owl:imports` so that reasoners process SKOS axioms (e.g., `skos:broader` transitivity) alongside the OWL class hierarchy.

### 4.3 Organizations, Agents, and Roles

Organizational context is modeled as follows:

- **Agency (`aiu:Agency`)** — subclass of CCO Organization (`ont00001180`), representing a federal department or independent agency.
- **Bureau (`aiu:Bureau`)** — subclass of CCO Organization (`ont00001180`), with `cco:part_of` relations to `Agency`.

Use case records carry organizational metadata:
- `aiu:UseCaseRecord aiu:hasAgency aiu:Agency`
- `aiu:UseCaseRecord aiu:hasBureau aiu:Bureau`

Roles are modeled as BFO roles (`BFO_0000023`):
- `aiu:SystemOwnerRole`, `aiu:DeveloperRole`, `aiu:OperatorRole`, `aiu:OversightRole`

These roles are related to processes via standard BFO/RO patterns (`inheres_in`, `realized_in`, `participates_in`).

### 4.4 AI Systems, Datasets, and Outputs

Technical components are represented as:

- **AISystem (`aiu:AISystem`)** — subclass of CCO Artifact (`ont00000995`).
- **AIFunction (`aiu:AIFunction`)** — subclass of `bfo:function` (`BFO_0000034`), borne by an `AISystem`.
- **Dataset (`aiu:Dataset`)** — subclass of `IAO:dataset`.
- **AIOutputArtifact (`aiu:AIOutputArtifact`)** — subclass of `IAO:data item`.

Representative relations:
- `aiu:AIUseCaseProcess aiu:usesAISystem aiu:AISystem`
- `aiu:AIUseCaseProcess aiu:hasInputDataset aiu:Dataset`
- `aiu:AIUseCaseProcess aiu:hasOutputArtifact aiu:AIOutputArtifact`

### 4.5 Risk, Impact, and Governance

Risks and governance are modeled using BFO roles and directive ICEs:

- **RiskRole (`aiu:RiskRole`)** — subclass of `bfo:role` (`BFO_0000023`).
  - Specializations: `aiu:RightsImpactRiskRole`, `aiu:SafetyImpactRiskRole`, `aiu:PIIRiskRole`.
- **RiskAssessmentDocument (`aiu:RiskAssessmentDocument`)** — an `IAO:document`.
- **AIImpactAssessmentProcess (`aiu:AIImpactAssessmentProcess`)** — a `CCO:Planned Act` (ont00000228) that produces `RiskAssessmentDocument` instances.
- **GovernancePolicy (`aiu:GovernancePolicy`)** — a `CCO:Directive Information Content Entity` (ont00000965).

Key relations:
- `aiu:AIUseCaseProcess aiu:hasRiskRole aiu:RiskRole`
- `aiu:AIUseCaseProcess aiu:assessedBy aiu:AIImpactAssessmentProcess`
- `aiu:AIImpactAssessmentProcess aiu:hasAssessmentOutput aiu:RiskAssessmentDocument`
- `aiu:AIUseCaseProcess aiu:governedBy aiu:GovernancePolicy`

### 4.6 Time and Provenance

Time and provenance are modeled to support year-over-year comparisons and auditability:

- **TimeInstant (`aiu:TimeInstant`)** — subclass of `BFO_0000203` (temporal instant, introduced in BFO 2020; a single point in time). The four lifecycle date properties (`hasInitiationTime`, `hasAcqDevTime`, `hasImplementationTime`, `hasRetirementTime`) each range over `TimeInstant`.
- **InventorySnapshot** carries `aiu:inventoryYear` (`xsd:gYear`) to identify the reporting year.
- **PROV-O alignment**: `UseCaseRecord` is declared `rdfs:subClassOf prov:Entity`. Two PROV properties are additionally constrained via OWL restrictions on `UseCaseRecord`: `prov:wasAttributedTo` (`someValuesFrom aiu:Agency`) and `prov:generatedAtTime` (`someValuesFrom xsd:dateTime`). Use of `prov:wasDerivedFrom` (linking to earlier records or source agency inventories) is recommended but not yet formally restricted.

Cross-year continuity is modeled via:
- `aiu:possibleDuplicateOf` — symmetric property for suspected duplicates (entity resolution candidates).
- `aiu:continuesFrom` — directed property for confirmed cross-year identity of the same use case.

### 4.7 Enumerated Inventory Fields as SKOS Vocabularies

The OMB data dictionary contains 15+ enumerated fields. Each is represented as a `skos:ConceptScheme` with `owl:NamedIndividual` `skos:Concept` members, enabling graph-based queries over categorical dimensions. Object properties (not `xsd:string` data properties) link use case instances to these controlled vocabulary terms.

| Scheme | Field | # Values |
|---|---|---|
| `aiu:TopicAreaScheme` | `8_topic_area` | 10 |
| `aiu:DevStageScheme` | `16_dev_stage` | 5 |
| `aiu:ImpactTypeScheme` | `17_impact_type` | 4 |
| `aiu:DevMethodScheme` | `22_dev_method` | 3 |
| `aiu:HISPScheme` | `25_hisp_name` | 38 (complete) |
| `aiu:DemoFeatureScheme` | `35_demo_features` | 12 |
| `aiu:CodeAccessScheme` | `38_code_access` | 3 |
| `aiu:MonitoringMaturityScheme` | `56_monitor_postdeploy` | 4 |
| `aiu:DataDocLevelScheme` | `34_data_docs` | 4 |
| `aiu:TestingLevelScheme` | `53_real_world_testing` | 5 |
| `aiu:InternalReviewScheme` | `50_internal_review` | 4 |
| `aiu:CommercialAITypeScheme` | `10_commercial_ai` | 20 (complete) |

## 5. Mapping to the Federal AI Use Case Inventory

The ontology is explicitly designed to support import of the 2023/2024 consolidated inventories and the OMB data dictionary (67 fields, 5 sections).

### 5.1 Identifiers and Description (Section 1 fields)

| Inventory field | Ontology mapping |
|---|---|
| `2_use_case_name` | `UseCaseRecord.aiu:useCaseName` (data property) |
| `3_agency` / `3_abr` | `UseCaseRecord aiu:hasAgency Agency` |
| `4_bureau` | `UseCaseRecord aiu:hasBureau Bureau` |
| `8_topic_area` | `AIUseCaseProcess aiu:hasTopicArea TopicAreaScheme concept` |
| `10_commercial_ai` | `UseCaseRecord aiu:hasCommercialAIType CommercialAITypeScheme concept` |
| `11_purpose_benefits` | `AIUseCasePlan.aiu:purposeBenefitsText` (text for goal classification) |
| `12_outputs` | `AIUseCaseProcess.aiu:outputsText` (text for goal classification) |
| `16_dev_stage` | `AIUseCaseProcess aiu:hasDevelopmentStage DevStageScheme concept` |
| `17_impact_type` | `AIUseCaseProcess aiu:hasImpactType ImpactTypeScheme concept` |

### 5.2 Use Case Summary (Section 2 fields)

| Inventory field | Ontology mapping |
|---|---|
| `18_date_initiated` | `AIUseCaseProcess aiu:hasInitiationTime TimeInstant` |
| `19_date_acq_dev_began` | `AIUseCaseProcess aiu:hasAcqDevTime TimeInstant` |
| `20_date_implemented` | `AIUseCaseProcess aiu:hasImplementationTime TimeInstant` |
| `21_date_retired` | `AIUseCaseProcess aiu:hasRetirementTime TimeInstant` |
| `22_dev_method` | `AIUseCaseProcess aiu:hasDevelopmentMethod DevMethodScheme concept` |
| `24_hisp_support` / `25_hisp_name` | `AIUseCaseProcess aiu:supportsHISP HISPScheme concept` |
| `29_contains_pii` | `AIUseCaseProcess.aiu:usesPII` (boolean) + `PIIRiskRole` |
| `30_saop_review` | `AIUseCaseProcess.aiu:saopReviewed` (boolean) |

### 5.3 Data and Code (Section 3 fields)

| Inventory field | Ontology mapping |
|---|---|
| `33_agency_data` | `Dataset.aiu:agencyDataDescription` (text) |
| `34_data_docs` | `AIUseCaseProcess aiu:hasDataDocLevel DataDocLevelScheme concept` |
| `35_demo_features` | `AIUseCaseProcess aiu:usesDemographicFeature DemoFeatureScheme concept` |
| `37_custom_code` | `AIUseCaseProcess.aiu:customCodePresent` (boolean) |
| `38_code_access` | `AIUseCaseProcess aiu:hasCodeAccess CodeAccessScheme concept` |
| `39_code_link` | `AISystem.aiu:openSourceCodeURL` (URI) |

### 5.4 Enablement and Infrastructure (Section 4 fields)

| Inventory field | Ontology mapping |
|---|---|
| `40_has_ato` | `AISystem.aiu:hasATO` (boolean) |
| `41_system_name` | `AISystem.aiu:systemName` (string) |
| `50_internal_review` | `AIUseCaseProcess aiu:hasInternalReviewLevel InternalReviewScheme concept` |

### 5.5 Risk Management (Section 5 fields)

| Inventory field | Ontology mapping |
|---|---|
| `52_impact_assessment` | `AIUseCaseProcess aiu:assessedBy AIImpactAssessmentProcess` |
| `53_real_world_testing` | `AIUseCaseProcess aiu:hasTestingLevel TestingLevelScheme concept` |
| `54_key_risks` | `RiskAssessmentDocument.aiu:keyRisksText` (text) |
| `56_monitor_postdeploy` | `AIUseCaseProcess aiu:hasMonitoringMaturity MonitoringMaturityScheme concept` |
| `57_autonomous_impact` | `AIUseCaseProcess.aiu:autonomousImpact` (boolean) |
| `65_appeal_process` | `AIUseCaseProcess.aiu:hasAppealProcess` (boolean) |
| `67_opt_out` | `AIUseCaseProcess.aiu:hasOptOut` (boolean) |

## 6. Graph-Analytics Affordances

The ontology is structured to support a range of graph-analytic questions:

1. **Per-year goal trends.** Using `aiu:partOfInventory` (linking records to `InventorySnapshot`) and `aiu:hasBusinessGoal`, compute the most/least common goals per inventory year.
2. **Impactful goals.** Combining goal tags with risk roles, impact type concepts, PII markers, and assessment presence identifies which goals are most associated with high-impact use cases.
3. **Goal dependencies and bundles.** Projecting the bipartite graph (AIUseCasePlan ↔ BusinessGoalConcept) onto a goal–goal co-occurrence network supports community detection and clustering analyses.
4. **Goal coverage per use case.** Counting direct `hasBusinessGoal` links and 1–2-hop goal neighborhoods reveals which use cases cover the broadest goal sets.
5. **Categorical analytics.** The SKOS ConceptScheme nodes (TopicArea, DevStage, ImpactType, etc.) are first-class graph nodes, enabling queries like "which development stages are most associated with rights-impacting use cases?" without string matching.
6. **Duplication analysis.** Rich neighborhoods (goals, agencies, topic areas, risk roles, systems) provide graph features for entity-resolution pipelines; `aiu:possibleDuplicateOf` records suspected duplicates and `aiu:continuesFrom` records confirmed cross-year continuity.
7. **Temporal snapshot queries.** Records are linked to `InventorySnapshot` instances that anchor them to named graphs (one per inventory year). Standard SPARQL `GRAPH` queries isolate or compare year-specific subgraphs.

**OWL-to-property-graph conversion.** To import the ontology and data into a property graph database for graph algorithm execution, use **Neosemantics (n10s)** for on-premises Neo4j deployments or **rdflib-neo4j** for cloud/managed deployments. Both tools map `owl:Class` nodes to node labels and `owl:ObjectProperty` assertions to typed relationships.

## 7. Validation and SHACL

Formal data validation uses SHACL shapes in a **separate file** (`shapes.ttl`) that imports the ontology:

- Three-file architecture: `vocab.ttl` (vocabulary), `ontology.ttl` (OWL axioms), `shapes.ttl` (SHACL validation).
- Use **Astrea** (`github.com/oeg-upm/astrea`) to auto-generate an initial SHACL skeleton from the OWL axioms, then manually add required-property constraints, controlled-vocabulary range constraints (ensuring SKOS Concept values come from the correct ConceptScheme), and cardinality rules.
- Validate data using pySHACL (Python) or Apache Jena SHACL.

No BFO-specific SHACL shapes exist in the public OBO Foundry ecosystem, so shapes must be hand-crafted after Astrea generation.

## 8. Extensibility and Governance of the Ontology

The ontology is intended as a stable but extensible semantic layer:

- **Versioning and stability.** The `BusinessGoalTaxonomy` ConceptScheme provides stable IRIs for business goals, allowing trend analysis across years even as textual descriptions evolve.
- **Extending the taxonomy.** New goal concepts or clusters can be added as `owl:NamedIndividual` SKOS Concepts under existing `skos:broader`/`skos:narrower` relations without changing core classes.
- **Adding enumerated vocabularies.** New SKOS ConceptSchemes for additional inventory fields can be added without structural changes to existing classes.
- **Adding domains and risk types.** Additional mission domains, risk categories, or governance mechanisms can be introduced as new subclasses of existing patterns.
- **Alignment with future guidance.** BFO alignment and CCO reuse enable incorporation of new federal AI guidance and risk standards without structural disruption.

Overall, this ontology provides a principled, reusable foundation for integrating the Federal AI Use Case Inventory with the business-goal taxonomy, enabling both descriptive reporting and sophisticated graph analytics over time.
