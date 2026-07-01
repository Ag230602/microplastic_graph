# Minimal Evidence-Gated KG Experiment

This is the smallest anti-hallucination test graph and a seed slice for a future automated evidence-gated system.

It is separate from the full graph and the focused 53-node graph.

## Counts

- Entities: 16
- Relationships: 20
- Evidence nodes: 2
- Observation nodes: 2
- Evidence-supported observations: 2 / 2

## Why this is smaller

The current seed slice keeps a small animal-evidence chain from the mouse oral-gavage polystyrene study so the system can be checked by hand before scaling:

`Publication -> Study -> Evidence -> Observation -> Reservoir -> Agent -> Exposure Pathway -> Host -> Tissue -> Mechanism -> Biomarker -> Outcome`

The selected evidence is about:

1. Polystyrene particle presence in mouse gut, liver, and kidneys.
2. Liver metabolic and oxidative-stress marker changes.

## Evidence Gate Result

The graph must answer conservatively:

> Current evidence is based on animal evidence. Human evidence is insufficient.

No PMID or DOI is invented. These fields are marked as unavailable because they are not present in the provided source excerpt.

In the long run, the same structure is intended to support larger human, animal, and in-vitro evidence layers with more studies, more outcomes, conflicting findings, and richer automated review generation.

## Dashboard Pages

`minimal_dashboard.html` is a functional prototype dashboard with:

- Overview: explains environmental health, ontology, knowledge graph, and evidence-gated AI.
- Agent: explains which AI-agent modules are functional in this prototype and which are not yet full backend/LLM systems.
- Ontology: shows every node and relationship with definitions, evidence sentences, supporting publication fields, PMID/DOI status, and confidence.
- Graph: displays a hands-on graph with search, node-type filtering, layout modes, relationship-tier filtering, evidence-strength filtering, color-coded nodes, curved edge labels, and click-to-inspect node evidence/provenance details.
- Evidence: shows the evidence table and Evidence -> Observation support links.
- Question Answering: includes example-question buttons, a deterministic in-browser mini-agent, step-by-step ontology mapping, evidence retrieval, evidence gating, final answer, and research gap output.
- Review: presents a visual automated-review workspace with evidence synthesis cards, confidence snapshot, review-generation pipeline, automation slots for future contradictory-study handling, and manuscript-ready summary text.

## Clinical Outcome Hierarchy

Clinical outcomes are represented by medical specialty rather than as a flat list. The minimal graph instantiates one Gastroenterology/Hepatology outcome, while `minimal_kg.json` stores the broader hierarchy for Neurology, Cardiology, Pulmonology, Gastroenterology, Endocrinology, Reproductive Health, Immunology, Oncology, Nephrology, Dermatology, and General Systemic Outcomes.

The dashboard includes an Outcomes page with:

- medical specialty hierarchy
- instantiated outcome details
- organ system
- disease category
- ICD-11/SNOMED CT/UMLS mapping status
- associated biomarkers
- associated mechanisms
- evidence strength
- confidence score

## Graph Improvement Checklist

The Overview page now documents the requested graph improvements:

- clinical outcomes organized by specialty
- overview page with example workflow
- ontology page explaining nodes, relationships, and evidence
- supporting citation/evidence metadata on every relationship
- specific scientific relationship names instead of generic association edges
- Tier 1 structural and Tier 2 scientific relationship grouping
- evidence strength and confidence values
- explicit conflict/gap handling
- improved graph visualization and filtering
- no unnecessary Association nodes in the minimal graph

## Why the Agent Is a Prototype

The dashboard does not call an external LLM. This is intentional for anti-hallucination testing. The mini-agent only reads `minimal_kg.json` and returns evidence stored in the graph. A full AI agent would need backend services for literature retrieval, ontology normalization, semantic search, evidence weighting across study designs, and model inference.
