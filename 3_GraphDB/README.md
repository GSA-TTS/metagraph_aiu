# 3_GraphDB — Graph Database Loading

This folder will contain scripts and configuration for loading the RDF output from `2_ETL/` into a property graph database for algorithm execution.

**Planned steps:**

1. Convert `pilot_1_15.ttl` (and the full inventory TTL once produced) from RDF to a property graph using Neosemantics (`n10s`) for Neo4j or `rdflib-neo4j` for managed deployments
2. Define node labels and relationship types from OWL classes and object properties
3. Load `aiu:BusinessGoalConcept`, `aiu:AIUseCasePlan`, `aiu:Agency`, `aiu:AIUseCaseProcess`, and SKOS concept nodes
4. Verify graph integrity — node counts, relationship counts, orphan check
5. Create indexes on high-cardinality properties (`useCaseName`, `inventoryYear`, `hasImpactType`) for query performance

**Prerequisites (not yet configured):** Neo4j or compatible property graph database; Neosemantics plugin or `rdflib-neo4j`.

See [`../2_ETL/README.md`](../2_ETL/README.md) for the RDF outputs that feed this step.
