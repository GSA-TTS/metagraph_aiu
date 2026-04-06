# AIU Inventory Field Mapping
**Purpose:** Defines the authoritative mapping from OMB Federal AI Use Case Inventory fields to the `aiu:` ontology (`aiu_ontology_ver1.ttl`). Drives both RDF/JSON instance generation and SHACL shape authoring.

**Ontology prefix:** `https://example.org/ai-usecase-ontology#` (abbreviated `aiu:`)

---

## 1. The Gate Field

`10_commercial_ai` is required for every record. When its value is anything *other than* `"None of the Above"`, the record represents a COTS-only use case: fields `11_purpose_benefits` and `12_outputs` are still collected, but almost all Section 2–5 fields are skipped. This creates two record profiles:

| Profile | `10_commercial_ai` value | Sections populated |
|---|---|---|
| COTS record | Any of the 19 specific COTS types | §1 core fields only |
| Full record | `"None of the Above"` (`aiu:CAI_NoneOfTheAbove`) | All sections, subject to additional triggers |

SHACL implication: most Section 2–5 shapes need a `sh:condition` (SPARQL target) filtering on `aiu:hasCommercialAIType aiu:CAI_NoneOfTheAbove`.

---

## 2. Core Analytics Field Mapping

These fields are modeled in the ontology and directly drive graph analytics.

### 2.1 Section 1 — Identifiers and Classification (always required)

| Field | Subject class | Predicate | Range / Scheme (IRI pattern) | Req | Analytics role |
|---|---|---|---|---|---|
| `2_use_case_name` | `UseCaseRecord` | `aiu:useCaseName` | `xsd:string` | req | ID |
| `3_agency` / `3_abr` | `UseCaseRecord` | `aiu:hasAgency` | `aiu:Agency` (string → IRI lookup) | req | ORG, DEDUP |
| | `UseCaseRecord` | `prov:wasAttributedTo` | `aiu:Agency` (OWL restriction) | req | PROV |
| `4_bureau` | `UseCaseRecord` | `aiu:hasBureau` | `aiu:Bureau` (string → IRI lookup) | req | ORG, DEDUP |
| `8_topic_area` | `AIUseCaseProcess` | `aiu:hasTopicArea` | `aiu:TopicAreaScheme` → `aiu:TA_*` | req | PROFILE |
| `10_commercial_ai` | `UseCaseRecord` | `aiu:hasCommercialAIType` | `aiu:CommercialAITypeScheme` → `aiu:CAI_*` | req | PROFILE, GATE |
| `11_purpose_benefits` | `AIUseCasePlan` | `aiu:purposeBenefitsText` | `xsd:string` (NLP source — see §3) | req | GOAL |
| `12_outputs` | `AIUseCaseProcess` | `aiu:outputsText` | `xsd:string` (NLP secondary — see §3) | req | GOAL |
| `16_dev_stage` | `AIUseCaseProcess` | `aiu:hasDevelopmentStage` | `aiu:DevStageScheme` → `aiu:DS_*` | req | PROFILE, TEMPORAL |
| `17_impact_type` | `AIUseCaseProcess` | `aiu:hasImpactType` | `aiu:ImpactTypeScheme` → `aiu:IT_*` | req | RISK, PROFILE |

TopicArea IRI patterns: `aiu:TA_GovServices`, `aiu:TA_DiplomacyTrade`, `aiu:TA_EducationWorkforce`, `aiu:TA_EnergyEnvironment`, `aiu:TA_EmergencyMgmt`, `aiu:TA_HealthMedical`, `aiu:TA_LawJustice`, `aiu:TA_ScienceSpace`, `aiu:TA_Transportation`, `aiu:TA_MissionEnabling`

DevStage IRI patterns: `aiu:DS_Initiated`, `aiu:DS_AcqDev`, `aiu:DS_ImplAssess`, `aiu:DS_OpsMaint`, `aiu:DS_Retired`

ImpactType IRI patterns: `aiu:IT_Rights`, `aiu:IT_Safety`, `aiu:IT_Both`, `aiu:IT_Neither`

CommercialAI IRI patterns: `aiu:CAI_DataEntry`, `aiu:CAI_ImageCatalog`, `aiu:CAI_Transcription`, `aiu:CAI_Scheduling`, `aiu:CAI_EmailCateg`, `aiu:CAI_SocialMedia`, `aiu:CAI_TimeTrack`, `aiu:CAI_LogAnalysis`, `aiu:CAI_Summarize`, `aiu:CAI_Search`, `aiu:CAI_DocDigitize`, `aiu:CAI_WritingAssist`, `aiu:CAI_Collab`, `aiu:CAI_Presentation`, `aiu:CAI_DataViz`, `aiu:CAI_NewsCurate`, `aiu:CAI_TravelRoute`, `aiu:CAI_TravelBook`, `aiu:CAI_FaceRecog`, `aiu:CAI_NoneOfTheAbove`

---

### 2.2 Section 2 — Use Case Summary (conditional on gate = NoneOfAbove)

| Field | Subject class | Predicate | Range / Scheme (IRI pattern) | Cond trigger | Analytics role |
|---|---|---|---|---|---|
| `18_date_initiated` | `AIUseCaseProcess` | `aiu:hasInitiationTime` | `aiu:TimeInstant` | gate + stage ∈ {Initiated…OpsMaint} | TEMPORAL |
| `19_date_acq_dev_began` | `AIUseCaseProcess` | `aiu:hasAcqDevTime` | `aiu:TimeInstant` | gate + stage ∈ {AcqDev…OpsMaint} | TEMPORAL |
| `20_date_implemented` | `AIUseCaseProcess` | `aiu:hasImplementationTime` | `aiu:TimeInstant` | gate + stage ∈ {ImplAssess, OpsMaint} | TEMPORAL |
| `21_date_retired` | `AIUseCaseProcess` | `aiu:hasRetirementTime` | `aiu:TimeInstant` | gate + stage = Retired | TEMPORAL |
| `22_dev_method` | `AIUseCaseProcess` | `aiu:hasDevelopmentMethod` | `aiu:DevMethodScheme` → `aiu:DM_*` | gate + stage ∈ {AcqDev…OpsMaint} | PROFILE |
| `25_hisp_name` | `AIUseCaseProcess` | `aiu:supportsHISP` | `aiu:HISPScheme` → `aiu:HISP_*` | gate + `24_hisp_support = Yes` | HISP |
| `29_contains_pii` | `AIUseCaseProcess` | `aiu:usesPII` | `xsd:boolean` | gate + stage ∈ {ImplAssess, OpsMaint} | RISK, EQUITY |
| `30_saop_review` | `AIUseCaseProcess` | `aiu:saopReviewed` | `xsd:boolean` | gate + stage ∈ {ImplAssess, OpsMaint} | GOVERN |

Note: `24_hisp_support` (Yes/No) is a gate for `25_hisp_name`; it has no direct predicate — the presence of an `aiu:supportsHISP` triple implies "Yes."

DevMethod IRI patterns: `aiu:DM_Contracting`, `aiu:DM_InHouse`, `aiu:DM_Both`

HISP IRI patterns: `aiu:HISP_BCA`, `aiu:HISP_BIA`, `aiu:HISP_BTFA`, `aiu:HISP_CMS`, `aiu:HISP_CDFI`, `aiu:HISP_CBP`, `aiu:HISP_DCSA`, `aiu:HISP_DO`, `aiu:HISP_EBSA`, `aiu:HISP_ETA`, `aiu:HISP_FarmSA`, `aiu:HISP_FEMA`, `aiu:HISP_FES`, `aiu:HISP_FSA`, `aiu:HISP_FWS`, `aiu:HISP_FNS`, `aiu:HISP_ForestS`, `aiu:HISP_HUD`, `aiu:HISP_IHS`, `aiu:HISP_IRS`, `aiu:HISP_ITA`, `aiu:HISP_NPS`, `aiu:HISP_NRCS`, `aiu:HISP_OSHA`, `aiu:HISP_OWCP`, `aiu:HISP_PEP`, `aiu:HISP_Recgov`, `aiu:HISP_RetS`, `aiu:HISP_RD`, `aiu:HISP_SBA`, `aiu:HISP_SSA`, `aiu:HISP_TSA`, `aiu:HISP_USAID`, `aiu:HISP_USCIS`, `aiu:HISP_Census`, `aiu:HISP_USPTO`, `aiu:HISP_VBA`, `aiu:HISP_VHA`

---

### 2.3 Section 3 — Data and Code (conditional on gate = NoneOfAbove)

| Field | Subject class | Predicate | Range / Scheme (IRI pattern) | Cond trigger | Analytics role |
|---|---|---|---|---|---|
| `33_agency_data` | `Dataset` | `aiu:agencyDataDescription` | `xsd:string` | gate + stage ∈ {AcqDev…OpsMaint} | PROFILE |
| `34_data_docs` | `AIUseCaseProcess` | `aiu:hasDataDocLevel` | `aiu:DataDocLevelScheme` → `aiu:DDL_*` | gate + stage ∈ {AcqDev…OpsMaint} | GOVERN |
| `35_demo_features` | `AIUseCaseProcess` | `aiu:usesDemographicFeature` | `aiu:DemoFeatureScheme` → `aiu:DF_*` | gate + stage ∈ {AcqDev…OpsMaint} | EQUITY |
| `37_custom_code` | `AIUseCaseProcess` | `aiu:customCodePresent` | `xsd:boolean` | gate + stage ∈ {ImplAssess, OpsMaint} | PROFILE |
| `38_code_access` | `AIUseCaseProcess` | `aiu:hasCodeAccess` | `aiu:CodeAccessScheme` → `aiu:CA_*` | gate + stage ∈ {ImplAssess, OpsMaint} | GOVERN |
| `39_code_link` | `AISystem` | `aiu:openSourceCodeURL` | `xsd:anyURI` | `38_code_access = public` | GOVERN |

DataDocLevel IRI patterns: `aiu:DDL_Missing`, `aiu:DDL_Partial`, `aiu:DDL_Complete`, `aiu:DDL_WidelyAvailable`

DemoFeature IRI patterns: `aiu:DF_Race`, `aiu:DF_Sex`, `aiu:DF_Age`, `aiu:DF_Religion`, `aiu:DF_SES`, `aiu:DF_Ability`, `aiu:DF_Residency`, `aiu:DF_Marital`, `aiu:DF_Income`, `aiu:DF_Employment`, `aiu:DF_Other`, `aiu:DF_None`

CodeAccess IRI patterns: `aiu:CA_PrivateSource`, `aiu:CA_PublicSource`, `aiu:CA_NoAccess`

---

### 2.4 Section 4 — Enablement and Infrastructure (conditional on gate = NoneOfAbove)

| Field | Subject class | Predicate | Range / Scheme (IRI pattern) | Cond trigger | Analytics role |
|---|---|---|---|---|---|
| `40_has_ato` | `AISystem` | `aiu:hasATO` | `xsd:boolean` | gate + stage ∈ {AcqDev…OpsMaint} | GOVERN |
| `41_system_name` | `AISystem` | `aiu:systemName` | `xsd:string` | `40_has_ato = Yes` | ID, DEDUP |
| `50_internal_review` | `AIUseCaseProcess` | `aiu:hasInternalReviewLevel` | `aiu:InternalReviewScheme` → `aiu:IR_*` | gate + stage ∈ {AcqDev…OpsMaint} | GOVERN |

InternalReview IRI patterns: `aiu:IR_NoDocs`, `aiu:IR_Limited`, `aiu:IR_Developed`, `aiu:IR_Published`

---

### 2.5 Section 5 — Risk Management (conditional on gate = NoneOfAbove AND impact ≠ Neither AND stage ∈ {ImplAssess, OpsMaint} AND extension_request = No)

| Field | Subject class | Predicate | Range / Scheme (IRI pattern) | Analytics role |
|---|---|---|---|---|
| `52_impact_assessment` | `AIUseCaseProcess` | `aiu:assessedBy` | `aiu:AIImpactAssessmentProcess` (node created if value = "Yes" or "Planned") | RISK, GOVERN |
| `53_real_world_testing` | `AIUseCaseProcess` | `aiu:hasTestingLevel` | `aiu:TestingLevelScheme` → `aiu:TL_*` | RISK, GOVERN |
| `54_key_risks` | `RiskAssessmentDocument` | `aiu:keyRisksText` | `xsd:string` | RISK |
| `56_monitor_postdeploy` | `AIUseCaseProcess` | `aiu:hasMonitoringMaturity` | `aiu:MonitoringMaturityScheme` → `aiu:MM_*` | RISK, GOVERN |
| `57_autonomous_impact` | `AIUseCaseProcess` | `aiu:autonomousImpact` | `xsd:boolean` | RISK |
| `65_appeal_process` | `AIUseCaseProcess` | `aiu:hasAppealProcess` | `xsd:boolean` | GOVERN |
| `67_opt_out` | `AIUseCaseProcess` | `aiu:hasOptOut` | `xsd:boolean` | GOVERN |

TestingLevel IRI patterns: `aiu:TL_None`, `aiu:TL_Benchmark`, `aiu:TL_PerfOps`, `aiu:TL_ImpactOps`, `aiu:TL_Waived`

MonitoringMaturity IRI patterns: `aiu:MM_None`, `aiu:MM_Manual`, `aiu:MM_Automated`, `aiu:MM_MLOps`

---

## 3. Derived / Computed Mappings (not in data dictionary)

These are graph triples that are inferred or produced by the data pipeline, not read directly from inventory fields.

| Derived from | Subject class | Predicate | Range / Note |
|---|---|---|---|
| NLP on `11_purpose_benefits` + `12_outputs` | `AIUseCasePlan` | `aiu:hasBusinessGoal` | `aiu:BusinessGoalTaxonomy` → `aiu:BG_*` — primary analytical edge |
| Row-to-plan linkage | `UseCaseRecord` | `aiu:describesPlan` | `aiu:AIUseCasePlan` |
| Row-to-process linkage | `UseCaseRecord` | `aiu:describesProcess` | `aiu:AIUseCaseProcess` |
| Annual inventory year | `UseCaseRecord` | `aiu:partOfInventory` | `aiu:InventorySnapshot` (one per year) |
| Annual inventory year | `InventorySnapshot` | `aiu:inventoryYear` | `xsd:gYear` (e.g., `"2024"^^xsd:gYear`) |
| OWL restriction | `UseCaseRecord` | `prov:wasAttributedTo` | `aiu:Agency` — links record to its agency for provenance |
| OWL restriction | `UseCaseRecord` | `prov:generatedAtTime` | `xsd:dateTime` — timestamp of inventory year snapshot |
| Entity resolution pipeline | `UseCaseRecord` | `aiu:possibleDuplicateOf` | `aiu:UseCaseRecord` — symmetric; populated by NLP/graph dedup |
| Cross-year identity confirmation | `UseCaseRecord` | `aiu:continuesFrom` | `aiu:UseCaseRecord` — directed; links 2024 record to 2023 predecessor |

Business goal IRI pattern: `aiu:BG_1` … `aiu:BG_10` (top-level clusters), `aiu:BG_1_1` … `aiu:BG_10_4` (sub-goals, 39 total). See `taxonomy_bizGoals.md` for NLP classification hints per cluster.

---

## 4. Unmodeled Fields (Gap Table)

The following fields exist in the data dictionary but are not yet mapped to an ontology property. Included for completeness — useful when extending the ontology or SHACL coverage.

| Field | Type | Content | Priority |
|---|---|---|---|
| `23_contract_piids` | string | Contract PIID identifiers for contracting-based dev | Low |
| `24_hisp_support` | Yes/No | Gate for `25_hisp_name`; implicit in supportsHISP presence | — |
| `26_public_service` | enum | Public-facing vs. not public-facing for HISP services | Medium |
| `27_public_info` | Yes/No | Whether use case disseminates information to the public | Medium |
| `28_iqa_compliance` | string | IQA compliance description (free text) | Low |
| `31_data_catalog` | Yes/No | Whether agency data catalog was used for dataset discovery | Low |
| `42_dev_tools_wait` | enum | Wait time for computing/developer tools (3 levels) | Low |
| `43_infra_provisioned` | Yes/No | Whether IT infrastructure provisioned via centralized process | Low |
| `45_compute_request` | Yes/No | Whether identifiable process exists to request compute resources | Low |
| `47_timely_resources` | Yes/No | Whether resource provisioning communications were timely | Low |
| `49_existing_reuse` | enum | Level of code/platform reuse from existing agency AI (4 levels) | Medium |
| `51_extension_request` | Yes/No | Whether agency requested compliance extension under M-24-10 | Medium |
| `55_independent_eval` | enum | Independent evaluation status (5 levels incl. CAIO waiver) | High |
| `59_ai_notice` | enum | AI notice mechanism to affected individuals (8 options) | High |
| `61_adverse_impact` | Yes/No | Whether adverse impact assessment was conducted (rights cases) | High |
| `62_disparity_mitigation` | string | Disparity mitigation description (free text) | Medium |
| `63_stakeholder_consult` | enum | Stakeholder consultation method (7 options) | Medium |
| `66_no_appeal_reason` | string | Explanation for absence of appeal process (free text) | Low |

Fields with priority High are analytically significant (compliance status, equity assessment, AI transparency) and are strong candidates for the next ontology revision.

---

## 5. SHACL Shape Implications

| Shape target | Key properties to constrain | Notes |
|---|---|---|
| `aiu:UseCaseRecordShape` | `aiu:useCaseName` (min 1), `aiu:hasAgency` (min 1), `aiu:hasBureau` (min 1), `aiu:hasCommercialAIType` (min 1, max 1, `sh:in` CommercialAIScheme), `aiu:describesPlan` (min 1), `aiu:describesProcess` (min 1), `aiu:partOfInventory` (min 1) | Gate field needs `sh:in` constraint on 20 allowed IRIs |
| `aiu:AIUseCasePlanShape` | `aiu:purposeBenefitsText` (min 1), `aiu:hasBusinessGoal` (min 0 — populated post-NLP) | `hasBusinessGoal` range: `sh:class aiu:BusinessGoalConcept` |
| `aiu:AIUseCaseProcessShape` | `aiu:hasTopicArea` (min 1, sh:in TA scheme), `aiu:hasDevelopmentStage` (min 1, sh:in DS scheme), `aiu:hasImpactType` (min 1, sh:in IT scheme) | Core shape; conditional props use SPARQL `sh:condition` on gate |
| `aiu:FullRecordProcessShape` (conditional) | All §2–4 object properties; `aiu:usesPII`, `aiu:saopReviewed`, `aiu:customCodePresent`, `aiu:hasDataDocLevel`, `aiu:hasDevelopmentMethod`, `aiu:hasCodeAccess`, `aiu:hasInternalReviewLevel` | Applies only when `aiu:hasCommercialAIType aiu:CAI_NoneOfTheAbove` |
| `aiu:RiskRecordProcessShape` (conditional) | `aiu:hasTestingLevel`, `aiu:hasMonitoringMaturity`, `aiu:autonomousImpact`, `aiu:hasAppealProcess`, `aiu:hasOptOut` | Applies only when impact ≠ `aiu:IT_Neither` AND stage ∈ {ImplAssess, OpsMaint} |
| `aiu:AISystemShape` | `aiu:hasATO`, `aiu:systemName` (conditional), `aiu:openSourceCodeURL` (conditional) | |
| `aiu:InventorySnapshotShape` | `aiu:inventoryYear` (min 1, max 1, `xsd:gYear`) | One node per year; used as named-graph anchor |
