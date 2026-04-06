# ETL Pilot 1 — Results (2024 Inventory, 15 Records)

**Script:** `etl_pilot.py`  
**Output RDF:** `pilot_1_15.ttl`  
**Inventory:** 2024 Federal AI Use Case Inventory (OMB consolidated)  
**Run date:** 2025-04  
**See also:** `etl_pilot_guide.md` for methodology, row selection logic, and replication instructions

---

## Selected Records

| # | Agency | Stage | Impact | Use Case |
|---|--------|-------|--------|----------|
| 0 | DHS | Initiated | Rights | USCIS Translation Service |
| 1 | DHS | AcqDev | Rights | Advanced Analytics for X-ray Images |
| 2 | DHS | AcqDev | Safety | Advance RPM Maintenance Operating Reporter (ARMOR) |
| 3 | DOE | OpsMaint | Safety | Data Analytics and Machine Learning |
| 4 | CFTC | Retired | Both | Spoofing Detection AI/ML Project |
| 5 | DHS | OpsMaint | Both | ERNIE |
| 6 | DHS | AcqDev | Neither | TSA Contact Center Virtual Assistant |
| 7 | DHS | OpsMaint | Neither | Individual Assistance & Public Assistance |
| 8 | CFTC | AcqDev | Neither | Stress Testing Scenarios with Deep Learning |
| 9 | CFPB | Initiated | Neither | Document Review Tool |
| 10 | DHS | OpsMaint | Neither | Commercial Generative AI for Text Generation *(COTS)* |
| 11 | DOC | AcqDev | Neither | Generative AI Tools Pilot *(COTS)* |
| 12 | DOC | ImplAssess | Neither | Global Business Navigator Chatbot *(COTS)* |
| 13 | DOC | OpsMaint | Neither | Grammarly *(COTS)* |
| 14 | DOC | AcqDev | Neither | FAQ for SMaRT *(COTS)* |

---

## RDF Output

- **413 triples** total (353 ETL + 60 `hasBusinessGoal`)
- 15 `UseCaseRecord`, 15 `AIUseCasePlan`, 15 `AIUseCaseProcess` nodes
- Serialised to `pilot_1_15.ttl` (~31 KB, Turtle format)
- Business goal IRIs annotated with inline `# prefLabel` comments for readability

---

## SHACL Validation Results

**conforms = False | violations = 18 | warnings = 0**

All 5 COTS records conform perfectly (gate logic correctly suppresses full-record shapes).

| Record | Violations | Root cause |
|--------|-----------|------------|
| CFPB_9 (Document Review Tool) | 1 | `hasInitiationTime` missing — agency left `date_initiated` blank |
| CFTC_8 (Stress Testing) | 3 | `hasDataDocLevel`, `hasInternalReviewLevel`, `usesDemographicFeature` all blank |
| DHS_1 (X-ray Images) | 1 | `usesDemographicFeature` blank |
| DHS_2 (ARMOR) | 4 | `hasDataDocLevel`, `hasInternalReviewLevel`, `usesDemographicFeature`, `hasDevelopmentMethod` all blank |
| DHS_5 (ERNIE) | 7 | `hasAppealProcess` + `hasOptOut` null (Both-impact, OpsMaint); `hasImplementationTime` null; + 4 full-record fields blank |
| DHS_6 (TSA Contact Center) | 1 | `usesDemographicFeature` blank |
| DHS_7 (Individual Assistance) | 1 | `usesDemographicFeature` blank |

**All violations are genuine inventory data gaps — agencies did not submit required fields.** The ETL correctly mapped every value that was present. No violations are ETL artifacts.

The most pervasive gap is `usesDemographicFeature` (col 28): 6 of 10 full records at AcqDev/ImplAssess/OpsMaint stage left this field blank, which the shapes flag as a mandatory field for that stage tier.

---

## Business-Goal Tagging Results

**Method:** Claude Haiku (`claude-haiku-4-5-20251001`) — one API call per use case. Prompt supplies the use case name, purpose/benefits (≤600 chars), AI outputs (≤300 chars), topic area, development stage, and the full 39-goal catalog (id + label + first 150 chars of description). Model returns JSON `{"goals": ["aiu:BG_X_Y", ...]}`. IDs are whitelist-filtered against `GOAL_ID_SET`; capped at 5 per record.

| # | Use Case | # Goals | Assigned |
|---|----------|---------|---------|
| 0 | USCIS Translation Service | 5 | BG_2_4, BG_3_2, BG_4_1, BG_8_3, BG_10_1 |
| 1 | Advanced Analytics for X-ray Images | 3 | BG_4_1, BG_8_3, BG_10_1 |
| 2 | ARMOR | 5 | BG_4_1, BG_4_2, BG_5_2, BG_8_3, BG_10_1 |
| 3 | Data Analytics and Machine Learning | 3 | BG_4_1, BG_8_3, BG_10_1 |
| 4 | Spoofing Detection AI/ML Project | 4 | BG_7_1, BG_7_4, BG_8_3, BG_10_2 |
| 5 | ERNIE | 4 | BG_4_1, BG_8_3, BG_10_1, BG_7_1 |
| 6 | TSA Contact Center Virtual Assistant | 5 | BG_2_4, BG_3_2, BG_4_1, BG_4_4, BG_8_3 |
| 7 | Individual Assistance & Public Assistance | 4 | BG_1_4, BG_2_2, BG_4_1, BG_8_1 |
| 8 | Stress Testing Scenarios | 4 | BG_1_4, BG_5_4, BG_8_3, BG_9_1 |
| 9 | Document Review Tool | 3 | BG_4_1, BG_4_3, BG_8_3 |
| 10 | Commercial Generative AI *(COTS)* | 3 | BG_4_1, BG_6_1, BG_8_3 |
| 11 | Generative AI Tools Pilot *(COTS)* | 4 | BG_2_2, BG_4_1, BG_5_3, BG_8_3 |
| 12 | Global Business Navigator Chatbot *(COTS)* | 4 | BG_2_4, BG_3_2, BG_8_3, BG_9_2 |
| 13 | Grammarly *(COTS)* | 5 | BG_3_2, BG_3_3, BG_4_1, BG_6_1, BG_8_3 |
| 14 | FAQ for SMaRT *(COTS)* | 4 | BG_2_4, BG_3_2, BG_4_1, BG_8_3 |

**Statistics:** Mean 4.0 goals/use case; **15/15 records (100%)** received ≥1 goal; 60 `hasBusinessGoal` triples total.

Most frequently assigned: `BG_8_3` Automation and AI enablement (14/15), `BG_4_1` Process efficiency and waste reduction (12/15) — both consistent with the federal AI use case population.

### Tagging Quality Assessment

LLM classification eliminates the vocabulary gap that limited TF-IDF to 40% coverage. Haiku correctly bridges government/technical language ("anomaly detection at land border ports", "radiation portal monitors") to taxonomy goal labels without requiring shared tokens.

Assignments are semantically sound across record types:
- Spoofing Detection → BG_7_1 (Regulatory compliance) + BG_10_2 (Fraud prevention) ✓
- Stress Testing → BG_1_4 (Strategic planning under uncertainty) + BG_5_4 (Financial risk) ✓
- USCIS Translation → BG_2_4 (Customer experience) + BG_10_1 (Safety/data protection) ✓

**Production cost estimate:** 2133 rows × ~1200 tokens/call ≈ 2.6M tokens → ~$0.35 at Haiku pricing. For scale, batch 3–5 use cases per call and wrap with `tenacity` retry for rate-limit resilience.
