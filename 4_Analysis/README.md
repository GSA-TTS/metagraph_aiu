# 4_Analysis — Graph Analytics

This folder will contain notebooks and scripts for running graph analytics and producing findings on the federal AI use case knowledge graph loaded in `3_GraphDB/`.

**Planned steps:**

1. **Business goal frequency and trends** — count `hasBusinessGoal` edges per goal per inventory year; identify the most and least pursued goals across agencies
2. **Goal co-occurrence network** — project the bipartite (AIUseCasePlan ↔ BusinessGoalConcept) graph onto a goal–goal co-occurrence network; run community detection to find goal bundles
3. **Impactful goals** — cross-tabulate business goals with impact type (`IT_Rights`, `IT_Safety`, `IT_Both`), PII use, HISP support, and demographic feature use to identify which goals concentrate high-stakes deployments
4. **Agency and topic-area profiles** — rank agencies and mission domains by goal diversity, risk posture, and development stage distribution
5. **Entity resolution and cross-year continuity** — populate `aiu:possibleDuplicateOf` edges using name similarity and goal neighborhood overlap; confirm cross-year identity via `aiu:continuesFrom`
6. **Centrality and clustering** — run PageRank or betweenness centrality on the goal co-occurrence graph; identify hub goals and peripheral goals

**Prerequisites (not yet implemented):** graph database loaded (`3_GraphDB/`); graph algorithm library (e.g., Neo4j GDS, NetworkX, or GraphTool).

See [`../1_Ontology/README.md`](../1_Ontology/README.md) §3.6 for the full list of analytics affordances designed into the ontology.
