# ETL Results — `etl.py --case tiny` (pilot_3_15)

Run date: 2026-04-07
Script: `etl.py` (Claude Sonnet + GPT-5.4-mini Responses API + Opus referee)
Source: `inventory_2024.csv` (15 rows selected from 2,133 total)
Output: `pilot_3_15.ttl` (30 KB, 400 triples)
Disagreement log: `disagreements_tiny_20260407_215632.jsonl`

---

## Selected Records

| # | Agency | Type | Stage | Impact | HISP | PII | Use Case Name |
|---|---|---|---|---|---|---|---|
| 0 | Department of Veterans Affairs | Full | Operation and Maintenance | Both | Yes | Yes | Automated Decision Support |
| 1 | Department of Veterans Affairs | Full | Acquisition and/or Development | Both | Yes | Yes | Sybil - Lung Cancer Prediction Model by MIT |
| 2 | Department of Homeland Security | Full | Implementation and Assessment | Rights-Impacting | No | Yes | Babel |
| 3 | Department of Homeland Security | Full | Acquisition and/or Development | Both | Yes |  | Automated Target Recognition (ATR) Developments for Standard Screening |
| 4 | Consumer Financial Protection Bureau | Full | Initiated | Neither |  |  | Document Review Tool |
| 5 | Consumer Financial Protection Bureau | Full | Initiated | Neither |  |  | Complaint Summarization |
| 6 | Commodity Futures Trading Commission | Full | Retired | Both | No | No | Spoofing Detection AI/ML Project |
| 7 | Commodity Futures Trading Commission | Full | Acquisition and/or Development | Neither | No | Yes | Stress Testing Scenarios with Deep Learning |
| 8 | Commodity Futures Trading Commission | Full | Initiated | Neither | No | Yes | MPD Entity Risk Modeling |
| 9 | Commodity Futures Trading Commission | Full | Operation and Maintenance | Neither | No | No | Anomaly Detection for Data Quality |
| 10 | Department of Homeland Security | COTS | Operation and Maintenance | Neither |  |  | Commercial Generative AI for Text Generation (AI Chatbot) |
| 11 | Department of Commerce | COTS | Acquisition and/or Development | Neither | No | No | Generative AI Tools Pilot - Global Markets |
| 12 | Department of Commerce | COTS | Implementation and Assessment | Neither | Yes | No | Global Business Navigator Chatbot |
| 13 | Department of Commerce | COTS | Operation and Maintenance | Neither | No | No | Grammarly |
| 14 | Department of Commerce | COTS | Acquisition and/or Development | Neither | No |  | FAQ for SMaRT |

**Slot coverage (full records):**
- Full+Rights/Both: 5 (requirement: ≥3) ✓
- Full+Safety/Both: 4 (requirement: ≥3) ✓
- Full+HISP: 3 (requirement: ≥3) ✓
- Full+PII: 5 (requirement: ≥3) ✓

---

## RDF Output Summary

| Metric | Value |
|---|---|
| Total triples | 400 |
| Pre-assigned goal triples (aiu:BG_8_3) | 15 |
| LLM-tagged goal triples | 37 |
| Output file size | 30 KB |
| Nodes: UseCaseRecord | 15 |
| Nodes: AIUseCasePlan | 15 |
| Nodes: AIUseCaseProcess | 15 |

---

## Business-Goal Tagging Results

| # | Use Case Name | Goals | Dis% | TTL Source | Agreed | Assigned Goal IDs |
|---|---|---|---|---|---|---|
| 0 | Automated Decision Support | 3 | 0% | Sonnet | yes | BG_4_1, BG_4_4, BG_3_2 |
| 1 | Sybil - Lung Cancer Prediction Model by MIT | 2 | 100% | A | NO | BG_4_1, BG_10_1 |
| 2 | Babel | 2 | 100% | A | NO | BG_7_1, BG_4_1 |
| 3 | Automated Target Recognition (ATR) Developments for Standard Screening | 3 | 100% | A | NO | BG_4_1, BG_10_1, BG_2_4 |
| 4 | Document Review Tool | 3 | 50% | A | NO | BG_4_1, BG_7_4, BG_7_1 |
| 5 | Complaint Summarization | 2 | 50% | B | NO | BG_4_1, BG_4_4 |
| 6 | Spoofing Detection AI/ML Project | 3 | 0% | Sonnet | yes | BG_7_4, BG_10_2, BG_7_1 |
| 7 | Stress Testing Scenarios with Deep Learning | 3 | 0% | Sonnet | yes | BG_5_4, BG_9_1, BG_1_4 |
| 8 | MPD Entity Risk Modeling | 3 | 80% | A | NO | BG_5_4, BG_7_1, BG_3_3 |
| 9 | Anomaly Detection for Data Quality | 3 | 0% | Sonnet | yes | BG_8_1, BG_3_2, BG_4_3 |
| 10 | Commercial Generative AI for Text Generation (AI Chatbot) | 1 | 100% | A | NO | BG_4_1 |
| 11 | Generative AI Tools Pilot - Global Markets | 2 | 100% | A | NO | BG_4_1, BG_2_2 |
| 12 | Global Business Navigator Chatbot | 2 | 100% | A | NO | BG_2_4, BG_4_1 |
| 13 | Grammarly | 2 | 100% | A | NO | BG_3_2, BG_4_1 |
| 14 | FAQ for SMaRT | 3 | 50% | B | NO | BG_2_4, BG_3_2, BG_4_4 |

**Goal assignment statistics:**
- Mean goals per use case (LLM-tagged, excl. blacklisted): 2.47
- Min: 1, Max: 3

### Top Goals by Frequency

| Goal ID | Label | Count |
|---|---|---|
| aiu:BG_4_1 | Process efficiency and waste reduction | 10/15 |
| aiu:BG_3_2 | Quality, reliability, and consistency | 4/15 |
| aiu:BG_7_1 | Regulatory and legal compliance | 4/15 |
| aiu:BG_4_4 | Scaling operations without degrading quality or CX | 3/15 |
| aiu:BG_2_4 | Customer experience, satisfaction, and retention | 3/15 |
| aiu:BG_10_1 | Product safety, data protection, and incident prevention | 2/15 |
| aiu:BG_7_4 | Ethics, fraud, and whistleblowing | 2/15 |
| aiu:BG_5_4 | Leverage, market risk, and financial risk management | 2/15 |
| aiu:BG_10_2 | Ethical conduct, compliance, and leadership integrity | 1/15 |
| aiu:BG_9_1 | Macroeconomic resilience | 1/15 |

### Dual-LLM Agreement Statistics

| Metric | Value |
|---|---|
| Agreed (Sonnet == GPT exact match) | 4/15 (26%) |
| Disagreements | 11/15 |
| Average disagreement % | 84.5% |
| Opus chose Sonnet (A) | 9 |
| Opus chose GPT (B) | 2 |
| Logged (>30% threshold) | 11 |

---

## SHACL Validation Results

**Conforms: False | Violations: 25 | Warnings: 0**

| Record | Violations | Primary cause |
|---|---|---|
| proc_2024_CFPB_4 | 1 | [FullRecordProcessShape] focus=proc_2024_CFPB_4, path=(SPARQL): Full records that are not at the Ret |
| proc_2024_CFPB_5 | 1 | [FullRecordProcessShape] focus=proc_2024_CFPB_5, path=(SPARQL): Full records that are not at the Ret |
| proc_2024_CFTC_7 | 3 | [FullRecordProcessShape] focus=proc_2024_CFTC_7, path=(SPARQL): Full records at AcqDev, ImplAssess,  |
| proc_2024_CFTC_9 | 1 | [FullRecordProcessShape] focus=proc_2024_CFTC_9, path=(SPARQL): Full records at AcqDev, ImplAssess,  |
| proc_2024_DHS_2 | 10 | [ne955d7829bc2451eb911257477c68560b153] focus=proc_2024_DHS_2, path=assessedBy: Rights/safety-impact |
| proc_2024_DHS_3 | 1 | [FullRecordProcessShape] focus=proc_2024_DHS_3, path=(SPARQL): Full records at AcqDev, ImplAssess, o |
| proc_2024_VA_0 | 7 | [ne955d7829bc2451eb911257477c68560b153] focus=proc_2024_VA_0, path=assessedBy: Rights/safety-impacti |
| proc_2024_VA_1 | 1 | [FullRecordProcessShape] focus=proc_2024_VA_1, path=(SPARQL): Full records at AcqDev, ImplAssess, or |

