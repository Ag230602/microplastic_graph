# Dashboard Screenshot Pack

This folder contains screenshots and a small capture page for explaining the one-paper minimal dashboard and the 10-paper scaled dashboard.

## Files

- `01_combined_provenance_and_10_paper_overview.png`
  - Best screenshot for manuscript/slides.
  - Shows the 1-paper minimal Evidence -> Observation -> Outcome provenance trace and the 10-paper scaled dashboard counts.

- `02_10_paper_dashboard_overview.png`
  - Direct screenshot from the 10-paper dashboard overview.
  - Shows the scaled prototype with counts including relationships, concepts, evidence nodes, and observations.

- `provenance_capture.html`
  - Source HTML used only to make the clean combined screenshot.

## 1-Paper Minimal Dashboard

The 1-paper minimal dashboard is based on one selected source review paper:

`Neurotoxicity Following Exposure to Micro and Nanoplastics`

Counts:

- 1 source review paper
- 16 graph nodes
- 20 relationships
- 2 Evidence nodes
- 2 Observation nodes
- 2/2 evidence-supported observations

The provenance example shown in the screenshot is:

`evidence_liver_metabolic_oxidative_markers -> observation_liver_metabolic_oxidative_response -> outcome_hepatic_metabolic_alteration`

Interpretation:

An exact liver metabolic/oxidative-stress evidence sentence supports a structured mouse liver observation. That observation then supports the conservative outcome label `hepatic metabolic alteration`. The outcome link is marked as animal evidence and conservative, preventing unsupported human clinical extrapolation.

## 10-Paper Dashboard

The 10-paper dashboard scales the minimal concept to 10 section-level source papers selected from `data_sections.json`.

Counts:

- 10 papers
- 188 entities
- 365 relationships
- 18 concept nodes
- 80 evidence nodes
- 80 observation nodes
- 80/80 evidence-supported observations

The 10-paper dashboard supports:

- paper-level evidence summaries
- concept matching
- evidence-gated question answering
- random-paper testing
- KG-vs-LLM answer comparison

## Suggested Caption

Dashboard screenshots illustrating evidence-gated provenance in the microplastics knowledge graph. The minimal one-paper graph traces an exact evidence sentence to a structured observation and then to a conservative outcome node. The 10-paper dashboard scales the same evidence-gated design across 10 section-level papers, producing 188 entities, 365 relationships, 80 evidence nodes, and 80 evidence-supported observations.