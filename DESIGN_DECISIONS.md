# MPKG Pipeline — Design Decisions & Prompt Compliance

Paper: *Neurotoxicity Following Exposure to Micro and Nanoplastics*  
Ontology: `entities_v1.json` + `relationships_v1.json`

## Current State

`mpkg_output_v2.json` is the source of truth for the evidence-aware graph:

- 115 entities
- 304 relationships
- 10 Study nodes
- 12 Evidence nodes
- 14 Observation nodes
- 14 HostPopulation nodes
- 8 TissueOrgan nodes

All 14 Observation nodes are directly supported by Evidence nodes.

## Key Design Decisions

### Evidence-Aware Provenance

Raw source statements are represented as `Evidence` nodes. These connect through:

`Study -> provides -> Evidence -> supports -> Observation`

This is the main novelty of the graph and allows each observation-level claim to be traced to an exact sentence.

### Primary Study Modeling

The review article remains a Study node, but key cited studies are also modeled as individual Study nodes: `[41]`, `[42]`, `[83,84]`, `[85]`, `[86]`, `[87]`, `[89]`, `[90]`, and `[92]`.

Primary study nodes provide Evidence, investigate HostPopulation nodes, and report observations/biomarkers/outcomes where supported by the review text.

### HostPopulation Modeling

HostPopulation is first-class because microplastic health evidence is population-dependent. The graph includes the requested Human, Mouse, Rat, Earthworm, C. elegans, Pregnant women, Children, and Older adults nodes. Sensitive human subgroups are included as stratification targets, with notes clarifying that the current review does not provide direct subgroup-specific outcome evidence.

### Observation vs Evidence

Evidence nodes store exact statements. Observation nodes store structured claims derived from those statements. This prevents raw quoted evidence from being conflated with interpreted graph claims.

### Explicit Reasoning Chain

The relationship schema and graph now support the requested chain:

`Study -> Evidence -> Observation -> Environmental Reservoir -> Agent -> Exposure Pathway -> Host Population -> Biological Mechanism -> Biomarker -> Clinical Outcome`

Local ontology labels use `EnvironmentalCompartment` for environmental reservoir and `Polymer` for agent.

### Benchmark Queries

The benchmark query layer is implemented in both Python and Cypher:

- `mpkg_query.py` runs directly over JSON and powers the dashboard.
- `mpkg_benchmark_queries.cypher` demonstrates the same questions in Neo4j.

The queries return evidence counts, supporting studies, and supporting sentences where available.

## Conservative Evidence Handling

- Direct human cardiovascular evidence is not invented. Q4 returns a limited-evidence gap result.
- Pregnant women, Children, and Older adults are not assigned unsupported outcomes or biomarkers.
- The graph keeps review-level conclusions low-confidence/limited where the review itself is cautious.

## Validation

Regeneration commands used:

```bash
python3 -m py_compile build_graph_v2.py mpkg_to_cypher.py build_dashboard.py mpkg_query.py build_standalone.py
python3 build_graph_v2.py
python3 mpkg_to_cypher.py
python3 build_dashboard.py
python3 build_standalone.py
python3 mpkg_query.py
```

Verified after update:

- no duplicate entity IDs
- no dangling relationships
- all Observation nodes have direct Evidence support
- benchmark query commands return valid JSON/output
