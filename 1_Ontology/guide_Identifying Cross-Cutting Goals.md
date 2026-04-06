<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Ok, please go ahead and produce the guide_identifyCrossCuttingGoals.md

```markdown
# Guide: Identifying Cross-Cutting Goals from Natural-Language Descriptions

## 0. Purpose and scope

This guide explains how to recognize **cross-cutting goals** expressed in natural language, primarily in software/IT requirements and related organizational or policy documents. Cross-cutting goals are goals that affect many other goals, features, or components, instead of being localized to a single function. [web:8][web:16][web:1]

---

## 1. Conceptual foundations

### 1.1 What is a cross-cutting goal?

In software engineering, cross-cutting concerns are requirements whose realization is scattered across multiple modules or tangled with other concerns, making them difficult to encapsulate in one place. [web:8][web:16][web:1] These typically arise from qualities (e.g., security, logging, performance) or policies that must be enforced consistently across a system. [web:8][web:17][web:18]

**Definition (text-level):**  
A cross-cutting goal is a prescriptive statement (goal/requirement) that constrains or systematically modifies the satisfaction of many other goals, features, or processes, rather than being realized by one localized functionality. [web:16][web:21]

Example:

- “Ensure all user actions are logged for audit purposes.”
  - Applies to every feature that handles user actions → cross-cutting.

### 1.2 Relationship to non-functional requirements and “issues”

Cross-cutting concerns are strongly related to non-functional requirements (quality attributes) such as security, reliability, and usability. [web:17][web:8] They also map to “cross-cutting issues” in policy and development contexts (e.g., gender equality, human rights, environment, anti-corruption) that must be integrated across all projects and programs. [web:7][web:26]

Key relationships:

- Many cross-cutting goals are quality or policy constraints derived from non-functional requirements or cross-cutting “issues.” [web:17][web:7]
- They typically apply system-wide or organization-wide, not just to a single feature or initiative. [web:18][web:26]

---

## 2. High-level identification strategy

### 2.1 Two views: linguistic and structural

You can recognize cross-cutting goals using two complementary views:

1. **Linguistic view (from text alone).**
   - Detect scope, quality/policy orientation, and domain-specific trigger terms in the goal sentence.
2. **Structural view (from a goal/requirements model).**
   - Detect scattering and centrality: a goal is cross-cutting if it is linked to many other goals, use cases, or components. [web:16][web:21][web:25]

Combining both views yields more reliable identification than either one alone.

### 2.2 A staged workflow

1. Extract candidate goal statements from text.
2. Apply linguistic heuristics to flag likely cross-cutting goals.
3. Build or update a simple goal/requirements model (graph).
4. Use structural indicators to confirm or downgrade candidates.
5. Validate with stakeholders and refine heuristics.

The rest of this guide details each step.

---

## 3. Step 1 – Extract candidate goals from natural language

### 3.1 Recognizing goal-like statements

First, identify sentences that correspond to goals or requirements:

- Modal verbs: “shall”, “must”, “should”, “will”, “is required to”.
- Imperatives: “Provide…”, “Ensure…”, “Support…”.
- Policy formulations: “It is a policy that…”, “All X are expected to…”.

Goal-oriented RE and recent work on LLM-based goal extraction treat a goal as a prescriptive statement of intent to be satisfied by the system or organization. [web:20][web:25] You can reuse patterns from requirements NLP and goal-model extraction methods: they parse sentences into actor–action–object structures and identify goals and soft goals (quality-oriented goals). [web:25][web:22]

### 3.2 Practical extraction checklist

For each document:

- Split into sentences.
- Keep sentences that:
  - Express an intended state or behavior to be achieved/maintained/avoided.
  - Refer to a system, product, organization, or project behavior.
- Mark these as “candidate goals” for further analysis.

---

## 4. Step 2 – Linguistic indicators of cross-cutting goals

This section gives concrete textual cues to identify likely cross-cutting goals directly from natural language.

### 4.1 Scope and universality cues

Cross-cutting goals often signal broad scope explicitly.

Common scope indicators:

- Quantifiers and collectivizing phrases:
  - “all users”, “all services”, “all components”, “all projects/programmes”.
  - “every request”, “each transaction”, “across the system”, “across all modules”.
- Temporal universality:
  - “at all times”, “always”, “under all conditions”, “throughout the lifecycle”.
- Organizational/system-level references:
  - “system-wide”, “organization-wide”, “applies to all building blocks”. [web:18]

Example (software/system):  
“The system must encrypt all data in transit and at rest for all services.”  
Example (policy/development):  
“All programmes must integrate human rights and gender equality considerations.” [web:26]

Heuristic H1:  
If a goal explicitly applies to “all” or “every” instance across multiple products, modules, users, projects, or time periods, treat it as a strong candidate cross-cutting goal.

### 4.2 Quality / non-functional orientation

Cross-cutting goals usually specify **how** things must be, rather than **what** concrete function is provided.

Common categories: [web:8][web:17][web:1]

- Security, privacy, access control.
- Logging, monitoring, observability, auditability. [web:11][web:1]
- Performance (latency, throughput), scalability, availability, reliability. [web:8][web:17]
- Usability, accessibility.
- Maintainability, modifiability, portability.

In development and policy contexts, cross-cutting issues include: human rights, gender equality, climate and environment, anti-corruption. [web:26][web:7]

Linguistic cues:

- Adjectives/adverbs: “secure”, “safe”, “reliable”, “compliant”, “efficiently”, “effectively”.
- Policy verbs: “comply with”, “respect”, “adhere to”, “align with [policy/standard]”.
- Explicit reference to standards or overarching frameworks: “GDPR”, “ISO 27001”, “accessibility standards”, “do no harm”. [web:7][web:18]

Heuristic H2:  
If the primary content of the goal is a quality attribute, policy, or constraint that is conceptually applicable to many different functions, treat it as a cross-cutting candidate.

### 4.3 Abstractness and system-level phrasing

Cross-cutting goals tend to be more abstract and system-level than concrete feature goals.

Patterns:

- “Ensure that [broad property holds].”
- “Provide mechanisms for [logging/monitoring/enforcement].”
- “Guarantee that [quality/policy] is maintained across [system/organization].”

Example:  
“Ensure that the system is resilient to infrastructure failures” is cross-cutting because it affects many components and operations, not just one feature. [web:8]

Heuristic H3:  
If a goal is phrased at a high level and can only be satisfied via multiple subordinate actions or components, treat it as cross-cutting unless evidence shows it is localized.

### 4.4 Domain-specific keyword patterns

You can maintain a **keyword lexicon** of typical cross-cutting domains for your context.

Example lexicon entries (software/IT): [web:8][web:1][web:17][web:18]

- Security/privacy: “security”, “authentication”, “authorization”, “encryption”, “confidentiality”, “integrity”, “access control”.
- Observability: “logging”, “tracing”, “monitoring”, “audit”, “telemetry”. [web:11][web:1]
- Reliability/resilience: “availability”, “fault tolerance”, “resilience”, “failover”, “backup”, “disaster recovery”.
- Compliance/governance: “compliance”, “policy”, “regulation”, “data protection”, “governance”.

Example lexicon entries (development/policy): [web:26][web:7]

- “human rights”, “women’s rights”, “gender equality”.
- “climate”, “environment”, “environmental impact”.
- “anti-corruption”, “integrity”, “do no harm”.

Heuristic H4:  
If a goal contains one or more lexicon terms and also passes H1–H3 (scope, quality, abstraction), classify it as likely cross-cutting.

---

## 5. Step 3 – Structural indicators via goal or requirements models

Textual cues are necessary but not sufficient. Structural analysis uses the relationships between goals to confirm cross-cutting status.

### 5.1 Build a simple goal/requirements graph

Using goal-oriented RE practices: [web:20][web:25][web:22]

- Nodes:
  - High-level goals, sub-goals, soft goals (quality goals), and tasks/use cases.
- Edges:
  - Refinement (AND/OR decomposition).
  - Contribution (helps/hurts quality goals).
  - Realization links to use cases, features, or components.

Recent work shows that such models can be generated semi-automatically from natural language using NLP and LLMs, producing KAOS/GRL-like goal structures. [web:25][web:22][web:20]

### 5.2 Structural properties of cross-cutting goals

In these models, cross-cutting goals exhibit:

- **High fan-out / degree.**  
  The goal is refined into, or constrains, many sub-goals or tasks scattered across diverse parts of the model. [web:16][web:21]
- **Presence across multiple feature clusters.**  
  The goal connects to distinct functional areas or subsystems rather than being confined to one cluster.
- **Soft-goal status with many contributions.**  
  Quality-related soft goals (e.g., “high security”) often receive contributions from many functional goals, indicating cross-cutting influence. [web:20][web:22]

Heuristic H5 (graph-based):  
If a goal node has high connectivity (e.g., contributes to or constrains ≥ N distinct functional goal clusters or components), treat it as cross-cutting even if textual signals are weak.

### 5.3 Traceability to many design elements

Aspect-oriented and crosscutting requirements research notes that cross-cutting concerns reveal themselves when mapping requirements to solution elements: a single concern maps to many classes, services, or modules. [web:16][web:21]

Practical step:

- Maintain a traceability matrix from goals to:
  - Components/services.
  - Interfaces/APIs.
  - Processes/teams.
- A goal with a high number of traces across different parts of the architecture is cross-cutting and should be made explicit. [web:16][web:18]

---

## 6. Step 4 – Decision rules and classification

### 6.1 Rule-based decision template

You can implement a lightweight, explainable classifier for cross-cutting goals:

1. **Screening rules (text only):**
   - If H1 (global scope) AND H2 (quality/policy) → label “Cross-cutting (text-level)”.
   - If H4 (keyword lexicon hit) AND (H1 OR H3) → label “Cross-cutting (text-level)”.
2. **Promotion/demotion rules (model-based):**
   - If text-level cross-cutting AND H5 (high structural connectivity) → label “Cross-cutting (confirmed)”.
   - If not text-level cross-cutting BUT H5 strong → label “Cross-cutting (structural)”.
3. **Negative rules:**
   - If a goal is clearly limited to one feature/component and lacks quality/policy orientation, label “Non-cross-cutting” even if it uses strong language (e.g., “must always” for one specific operation).

This mirrors the two-stage classification strategy used in document-level NLP for cross-cutting issues (screening, then categorical classification). [web:7][web:24]

### 6.2 Supervised ML alternative

Where you have labeled data, you can train an ML classifier:

- Features:
  - BoW/embeddings of the goal sentence.
  - Lexicon-based features (H4).
  - Scope indicators (H1).
  - Quality/policy indicators (H2).
  - Graph metrics (degree, centrality) from the goal model (H5). [web:25][web:22]
- Labels:
  - Cross-cutting vs. non-cross-cutting.
  - Optionally subcategories (e.g., security, logging, human rights, environment). [web:7][web:26]
- Use case:
  - Automate large-scale classification as in cross-cutting issue evaluations where ML models assign cross-cutting categories to thousands of documents. [web:7][web:24]

---

## 7. Step 5 – Practical checklist for practitioners

Use this compact checklist during requirements or policy analysis.

### 7.1 Text-level checklist

For each goal:

- Does it mention a known cross-cutting domain?
  - Security, privacy, logging, monitoring, observability, performance, reliability, compliance, environmental or social safeguards, human rights, gender equality, anti-corruption. [web:8][web:1][web:11][web:26][web:7]
- Does it apply to all or many entities?
  - “All users”, “all building blocks”, “every service”, “all programmes.” [web:18][web:26]
- Is it about a quality/policy constraint instead of a specific feature?
  - E.g., “ensure availability”, “comply with policy”, “integrate human rights.” [web:17][web:7]
- Is it phrased at an abstract, system/organization level?
  - E.g., “The platform shall be auditable”, “All development cooperation shall do no harm.” [web:7][web:18]

If “yes” to at least two of these questions, mark it as a cross-cutting candidate.

### 7.2 Model-level checklist

Once you have a simple goal/requirements model:

- Does the goal:
  - Constrain or refine many other goals across different feature clusters?
  - Have many incoming or outgoing trace links to components/services?
  - Appear as a soft goal with contributions from many functional tasks? [web:16][web:20][web:22]

If “yes” to any of these, treat the goal as cross-cutting and consider:

- Representing it explicitly (e.g., as a separate aspect, cross-cutting requirement section, or central policy document). [web:16][web:18]
- Centralizing its implementation or policy handling to avoid duplication and inconsistency. [web:1][web:23]

---

## 8. Illustrative examples

### 8.1 Software/system example

Goals:

1. “Allow customers to place online orders.”
2. “Allow customers to track their order status.”
3. “Log all user interactions with the system for auditing.”
4. “Ensure the system meets regulatory reporting requirements.”

Analysis:

- G3: “Log all user interactions…”  
  - Lexical: “log”, “all user interactions” → cross-cutting domain and global scope. [web:1][web:11]
  - Structural: applies to any feature involving user interactions → high fan-out.  
  → Cross-cutting goal.
- G4: “Ensure the system meets regulatory reporting requirements.”  
  - Quality/policy: compliance.  
  - Scope: whole system.  
  → Cross-cutting goal.

### 8.2 Development/policy example

Goals: [based on cross-cutting issues in Norwegian development cooperation] [web:26][web:7]

1. “Support local capacity-building for climate resilience.”
2. “Ensure all programmes integrate human rights and gender equality considerations.”
3. “Monitor anti-corruption measures in high-risk projects.”

Analysis:

- G2 references global scope (“all programmes”) and cross-cutting domains (human rights, gender equality) explicitly designated as cross-cutting issues. [web:26]
- G3 is cross-cutting within a subset of “high-risk projects” and may still be treated as cross-cutting for that portfolio segment. [web:26][web:7]

---

## 9. Integration into your process

To make this guide actionable in a real process:

- Incorporate the **text-level checklist** into requirements or policy review templates.
- Maintain a **living lexicon** of cross-cutting domains relevant to your organization and architecture. [web:17][web:1]
- Use or build simple **goal models** (possibly assisted by LLMs or goal-modeling tools) to expose cross-cutting structures. [web:25][web:22][web:20]
- Align cross-cutting goals with architectural mechanisms (aspects, shared libraries, platform services, or central policy frameworks) to avoid duplication and inconsistency. [web:16][web:14][web:23][web:18]

Would you like a short, language-agnostic tagging schema (labels and examples) that you can plug directly into an automated classifier or review tool?

```

<span style="display:none">[^1][^10][^11][^12][^13][^14][^15][^2][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.geeksforgeeks.org/system-design/cross-cutting-concerns-in-distributed-system/

[^2]: https://www.sciencedirect.com/topics/computer-science/crosscutting-concern

[^3]: https://www.milanjovanovic.tech/blog/balancing-cross-cutting-concerns-in-clean-architecture

[^4]: https://oncodedesign.com/blog/crosscutting-concerns/

[^5]: https://specs.govstack.global/overview/1.0.2/security-requirements/5-cross-cutting-requirements

[^6]: https://www.norad.no/globalassets/filer/evaluering/norad_ev-rapport_evaluation_of_cross-cutting_issues.pdf

[^7]: https://arxiv.org/html/2509.01048v1

[^8]: https://dl.acm.org/doi/10.1145/976270.976272

[^9]: https://www.norad.no/globalassets/filer/evaluering/natural-language-processing-in-evaluation.pdf

[^10]: https://conf.researchr.org/details/models-2024/models-2024-sam-conference/13/A-Comparative-Study-of-Large-Language-Models-for-Goal-Model-Extraction

[^11]: https://www.linkedin.com/posts/milan-jovanovic_how-do-you-solve-cross-cutting-concerns-in-activity-7196841866821074945-YfFh

[^12]: https://www.iodparc.com/blog/resource/methods-report-natural-language-processing-in-evaluation-reflections-lessons-learned-and-further-analysis/

[^13]: https://ceur-ws.org/Vol-3672/NLP4RE-paper1.pdf

[^14]: https://jessemcdowell.ca/2024/05/Cross-Cutting-Concerns/

[^15]: https://www.norad.no/en/publications/2024/evaluation-of-cross-cutting-issues-in-norwegian-development-cooperation/

