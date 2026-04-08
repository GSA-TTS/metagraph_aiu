# ETL Results — `etl.py --case tiny` (pilot_2_15)

Run date: 2026-04-07
Script: `etl.py` (Claude Sonnet + GPT-5.4-mini Responses API + Opus referee)
Source: `inventory_2024.csv` (15 rows selected from 2,133 total)
Output: `pilot_2_15.ttl` (29 KB, 385 triples)
Disagreement log: `disagreements_tiny_20260407_212259.jsonl`

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
| Total triples | 385 |
| Pre-assigned goal triples (aiu:BG_8_3) | 15 |
| LLM-tagged goal triples | 22 |
| Output file size | 29 KB |
| Nodes: UseCaseRecord | 15 |
| Nodes: AIUseCasePlan | 15 |
| Nodes: AIUseCaseProcess | 15 |

---

## Business-Goal Tagging Results

| # | Use Case Name | Goals | Dis% | TTL Source | Agreed | Assigned Goal IDs |
|---|---|---|---|---|---|---|
| 0 | Automated Decision Support | 2 | 100% | A | NO | BG_4_1, BG_4_4 |
| 1 | Sybil - Lung Cancer Prediction Model by MIT | 1 | 100% | A | NO | BG_2_2 |
| 2 | Babel | 0 | 100% | B (goal fallback) | NO |  |
| 3 | Automated Target Recognition (ATR) Developments for Standard Screening | 2 | 100% | A | NO | BG_10_1, BG_2_4 |
| 4 | Document Review Tool | 1 | 100% | A | NO | BG_7_4 |
| 5 | Complaint Summarization | 2 | 100% | A | NO | BG_4_1, BG_4_4 |
| 6 | Spoofing Detection AI/ML Project | 2 | 100% | A | NO | BG_7_1, BG_7_4 |
| 7 | Stress Testing Scenarios with Deep Learning | 2 | 100% | A | NO | BG_5_4, BG_9_1 |
| 8 | MPD Entity Risk Modeling | 2 | 100% | A | NO | BG_5_4, BG_9_1 |
| 9 | Anomaly Detection for Data Quality | 1 | 100% | A | NO | BG_8_1 |
| 10 | Commercial Generative AI for Text Generation (AI Chatbot) | 1 | 100% | A | NO | BG_4_1 |
| 11 | Generative AI Tools Pilot - Global Markets | 2 | 100% | A | NO | BG_1_2, BG_2_2 |
| 12 | Global Business Navigator Chatbot | 1 | 100% | A | NO | BG_2_4 |
| 13 | Grammarly | 1 | 100% | A | NO | BG_3_2 |
| 14 | FAQ for SMaRT | 2 | 100% | A | NO | BG_2_4, BG_3_2 |

**Goal assignment statistics:**
- Mean goals per use case (LLM-tagged, excl. blacklisted): 1.47
- Min: 0, Max: 2

### Top Goals by Frequency

| Goal ID | Label | Count |
|---|---|---|
| aiu:BG_4_1 | Process efficiency and waste reduction | 3/15 |
| aiu:BG_2_4 | Customer experience, satisfaction, and retention | 3/15 |
| aiu:BG_4_4 | Scaling operations without degrading quality or CX | 2/15 |
| aiu:BG_2_2 | Market understanding, demand estimation, and segmentation | 2/15 |
| aiu:BG_7_4 | Ethics, fraud, and whistleblowing | 2/15 |
| aiu:BG_5_4 | Leverage, market risk, and financial risk management | 2/15 |
| aiu:BG_9_1 | Macroeconomic resilience | 2/15 |
| aiu:BG_3_2 | Quality, reliability, and consistency | 2/15 |
| aiu:BG_10_1 | Product safety, data protection, and incident prevention | 1/15 |
| aiu:BG_7_1 | Regulatory and legal compliance | 1/15 |

### Dual-LLM Agreement Statistics

| Metric | Value |
|---|---|
| Agreed (Sonnet == GPT exact match) | 0/15 (0%) |
| Disagreements | 15/15 |
| Average disagreement % | 100.0% |
| Opus chose Sonnet (A) | 14 |
| Opus chose GPT (B) | 1 |
| Logged (>30% threshold) | 15 |

---

## SHACL Validation Results

**Conforms: False | Violations: 25 | Warnings: 0**

| Record | Violations | Primary cause |
|---|---|---|
| proc_2024_CFPB_4 | 1 | [FullRecordProcessShape] focus=proc_2024_CFPB_4, path=(SPARQL): Full records that are not at the Ret |
| proc_2024_CFPB_5 | 1 | [FullRecordProcessShape] focus=proc_2024_CFPB_5, path=(SPARQL): Full records that are not at the Ret |
| proc_2024_CFTC_7 | 3 | [FullRecordProcessShape] focus=proc_2024_CFTC_7, path=(SPARQL): Full records at AcqDev, ImplAssess,  |
| proc_2024_CFTC_9 | 1 | [FullRecordProcessShape] focus=proc_2024_CFTC_9, path=(SPARQL): Full records at AcqDev, ImplAssess,  |
| proc_2024_DHS_2 | 10 | [FullRecordProcessShape] focus=proc_2024_DHS_2, path=(SPARQL): Full records at AcqDev, ImplAssess, o |
| proc_2024_DHS_3 | 1 | [FullRecordProcessShape] focus=proc_2024_DHS_3, path=(SPARQL): Full records at AcqDev, ImplAssess, o |
| proc_2024_VA_0 | 7 | [FullRecordProcessShape] focus=proc_2024_VA_0, path=(SPARQL): Full records at AcqDev, ImplAssess, or |
| proc_2024_VA_1 | 1 | [FullRecordProcessShape] focus=proc_2024_VA_1, path=(SPARQL): Full records at AcqDev, ImplAssess, or |

