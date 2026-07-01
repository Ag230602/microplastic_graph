# Focused MPKG Experiment

This is a separate testing subset. It does not replace or modify the full evidence-aware graph.

## Purpose

Use a small set of evidence-backed claims to test extraction/query behavior with less risk of hallucination.

## Scope

- Selected Evidence nodes: 6
- Entities in subset: 53
- Relationships in subset: 97
- Evidence-supported observations: 8 / 8

## Node Counts

- Biomarker: 3
- ClinicalOutcome: 1
- EnvironmentalCompartment: 3
- Evidence: 6
- ExposurePathway: 3
- HostPopulation: 4
- Mechanism: 2
- Method: 2
- Observation: 8
- ParticleSizeClass: 5
- Polymer: 3
- Shape: 2
- Study: 6
- TissueOrgan: 5

## Relationship Counts

- about: 6
- activates: 2
- affects: 7
- contains: 3
- contributes_to: 1
- enters_via: 4
- evidenced_by: 3
- exhibits: 3
- experiences: 1
- exposes: 3
- has_polymer: 8
- has_shape: 2
- has_size_class: 7
- identified_by: 4
- investigates: 6
- measured_in: 3
- originates_from: 1
- provides: 6
- reports: 19
- supports: 8

## Selected Evidence

- `evidence_mouse_liver_accumulation`
- `evidence_mouse_brain_cytokines`
- `evidence_mouse_brain_caspase3`
- `evidence_earthworm_uptake`
- `evidence_zebra_mussel_accumulation`
- `evidence_celegans_effects`

## How To Use

Use `focused_mpkg_output_test.json` for conservative testing and `focused_mpkg_graph_test.json` for visualization experiments.
Keep the full graph (`../../mpkg_output_v2.json`) as the publication-scale artifact.
