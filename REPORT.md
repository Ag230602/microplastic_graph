# Microplastics Knowledge Graph — Short Report

**Paper:** *Neurotoxicity Following Exposure to Micro and Nanoplastics*  
**Ontology:** `entities_v1.json` + `relationships_v1.json`

## What was built

The current v2 graph is an **evidence-aware environmental-health knowledge graph** that preserves the reasoning path:

`Study -> Evidence -> Observation -> Environmental Reservoir -> Agent -> Exposure Pathway -> Host Population -> Biological Mechanism -> Biomarker -> Clinical Outcome`

Current artifact: `mpkg_output_v2.json`

| Item | Count |
|---|---:|
| Entities | 115 |
| Relationships | 304 |
| Study nodes | 10 |
| Evidence nodes | 12 |
| Observation nodes | 14 |
| HostPopulation nodes | 14 |
| Tissue/Organ nodes | 8 |

## Checklist Coverage

- **HostPopulation added:** Human, Mouse, Rat, Earthworm, C. elegans, Pregnant women, Children, Older adults, plus additional aquatic/invertebrate hosts represented in the review.
- **Evidence added:** all 14 Observation nodes are now directly supported by Evidence nodes containing exact source statements.
- **Primary Study nodes added:** key references are modeled as individual Study nodes, including `[41]`, `[42]`, `[83,84]`, `[85]`, `[86]`, `[87]`, `[89]`, `[90]`, and `[92]`, alongside the review Study node.
- **Observation separated from Evidence:** Evidence nodes support Observation nodes; observations then connect to polymers, reservoirs, tissues, pathways, hosts, mechanisms, biomarkers, and outcomes.
- **Benchmark queries implemented:** `mpkg_query.py` and `mpkg_benchmark_queries.cypher` include all four requested queries with supporting evidence/study context.
- **Figure/chain updated:** the dashboard overview now shows the full evidence-aware chain.

## Benchmark Query Results

Run:

```bash
python3 mpkg_query.py
```

Current outputs include:

- **Q1:** polymers linked to oxidative stress with supporting Evidence nodes.
- **Q2:** affected tissues ranked by evidence count; gut, hemolymph, gills, brain, liver, digestive gland, kidney, and lung are represented.
- **Q3:** inflammatory biomarkers TNF-alpha and IL-6 with supporting Study `[41]` evidence.
- **Q4:** drinking-water microplastics to human cardiovascular outcomes returns **human evidence: limited**, with no direct cardiovascular outcome chain in this corpus.

## Graph Artifacts

- `mpkg_graph_v2.json` — viewer-ready graph data, 115 nodes / 304 edges.
- `mpkg_graph_v2.cypher` — Neo4j import script.
- `mpkg_benchmark_queries.cypher` — evidence-aware benchmark queries.
- `mpkg_dashboard.html` — all-in-one dashboard with overview, graph, benchmark queries, evidence weighting, ranking, and provenance.
- `mpkg_graph_v2_standalone.html` — standalone v2 graph viewer with data inlined.

## Remaining Caveats

- Pregnant women, Children, and Older adults are modeled as sensitive HostPopulation nodes for stratified synthesis, but this review does not provide direct subgroup-specific outcome evidence.
- Q4 intentionally demonstrates a gap: the graph contains drinking-water exposure context but no direct human cardiovascular outcome evidence chain for this corpus.
- Some review-level biomarker claims remain conservative because they come from summarized primary studies rather than full primary-paper extraction.
