# MetaGraph AIU

A knowledge graph project that converts the U.S. OMB **Federal AI Use Case Inventory** into a semantically structured, graph-queryable dataset — with a focus on understanding the **business goals** driving federal AI adoption.

## Why this project

The OMB inventory is published as a flat CSV. Its categorical fields use uncontrolled strings and its descriptive fields are free text. This makes cross-agency comparison, trend analysis, and governance assessment difficult at scale.

This project builds a semantic layer on top of that data:

- **Business goal extraction** — each use case is tagged with 0–5 goals from a curated 10-cluster, 39-sub-goal taxonomy using an LLM classification pipeline. These tags become typed edges in the knowledge graph and are the primary lens for understanding what agencies are actually trying to accomplish with AI.
- **Structured graph data** — all categorical fields (development stage, topic area, impact type, HISP service, demographic features, and more) are modeled as SKOS concept nodes with object-property edges, not string literals, enabling graph traversal and algorithm execution without string parsing.
- **Cross-year continuity** — provenance and entity-resolution predicates support comparing 2023 and 2024 inventories at the use case level.
- **Extensibility** — the BFO/CCO-aligned ontology and SKOS taxonomy are designed to absorb new inventory years, new goal categories, and new analytical questions without structural changes to existing data.

## Repository structure

```
metagraph_aiu/
└── 1_Ontology/          OWL ontology, SHACL shapes, business goal taxonomy,
                         field mapping, and design documentation
                         → see 1_Ontology/README.md for full details
```

Additional folders will be added as the project progresses (ETL pipeline, graph database exports, analytics notebooks).

## Status

| Component | Status |
|---|---|
| OWL ontology (`aiu_ontology_ver1.ttl`) | Draft v1 |
| SHACL shapes (`aiu_shapes.ttl`) | Draft v1 |
| Business goal taxonomy (39 sub-goals) | Draft v1 |
| ETL pilot (15-record proof of concept) | Complete |
| Full 2,133-record ETL run | Pending |
| 2023 inventory ingest | Pending |
| Property graph database load | Pending |
| Entity resolution (cross-year) | Pending |

## Quick links

- [Ontology layer](1_Ontology/README.md) — architecture, methodology, validation, and roadmap
- [Field mapping](1_Ontology/aiu_inventory_field_mapping.md) — all 67 OMB fields mapped to ontology predicates
- [Business goal taxonomy](1_Ontology/taxonomy_bizGoals.md) — 10 clusters, 39 sub-goals with NLP classification hints

## License

Public domain — [CC0 1.0 Universal](LICENSE.md).
