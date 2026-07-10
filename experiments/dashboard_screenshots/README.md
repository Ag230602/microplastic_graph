# Dashboard Figures And Manuscript Notes

This folder contains dashboard figure files and manuscript-style text describing the knowledge graph (KG) build, the minimal 1-paper dashboard, the 10-paper dashboard, and the provenance-tracing result.

## Figure Files

- `01_minimal_evidence_observation_outcome_provenance.svg`
  - Figure for the 1-paper minimal dashboard.
  - Shows `Evidence -> Observation -> Outcome` provenance tracing.
  - Example chain: `evidence_liver_metabolic_oxidative_markers -> observation_liver_metabolic_oxidative_response -> outcome_hepatic_metabolic_alteration`.

- `02_ten_paper_dashboard_overview.svg`
  - Figure for the 10-paper dashboard.
  - Shows scale-up counts and dashboard workflow.
  - Workflow: `Paper -> Evidence -> Observation -> Concept -> Question Answering -> KG-vs-LLM comparison`.

## Overall Build Summary

The project was designed to test whether environmental health evidence about microplastics and nanoplastics could be represented in an evidence-gated knowledge graph rather than summarized only as free text. The central design goal was provenance preservation: each scientific claim should be traceable back to an evidence sentence, source paper, and structured graph path.

The initial full dashboard was built from one selected review paper, *Neurotoxicity Following Exposure to Micro and Nanoplastics*. That paper was selected from a larger local corpus containing title/abstract and section-level records. The graph extraction was constrained by two ontology files, `entities_v1.json` and `relationships_v1.json`, which defined the allowed entity classes and relationship types. These ontology files were not extracted from the paper; they served as schema constraints for the graph-building process.

The one-paper workflow used a staged process: extraction, critique, and refinement. The extraction stage generated an initial graph from the selected paper content. The critique stage evaluated the graph for unsupported entities, missing entities, unsupported relationships, ontology violations, and evidence gaps. The refinement stage produced an evidence-aware v2 graph. The full v2 graph contained 115 entities and 304 relationships. For the final dashboard presentation, six helper Association nodes and their connected edges were hidden to simplify the visual scientific view, yielding 109 displayed nodes and 284 displayed relationships.

After the one-paper graph was established, a minimal evidence-gated slice was created to provide a hand-checkable anti-hallucination test case. This minimal graph contains 16 nodes and 20 relationships. It focuses on one animal-evidence chain from the mouse oral-gavage polystyrene microplastic study summarized in the review. This minimal dashboard is the clearest demonstration of evidence-to-observation-to-outcome provenance tracing.

A separate 10-paper prototype was then created to scale the same evidence-gated concept across a broader source set. The 10-paper dashboard uses section-level records from ten micro/nanoplastic-related papers and builds a deterministic evidence/concept graph for testing question answering, random-paper concept overlap, and KG-vs-LLM comparison. This scaled prototype contains 188 entities, 365 relationships, 18 concept nodes, 80 evidence nodes, and 80 observation nodes.

## Methods-Style Text

### Data Sources

The local corpus contained title/abstract records and section-level records for microplastic and nanoplastic literature. For the initial controlled prototype, one review paper, *Neurotoxicity Following Exposure to Micro and Nanoplastics*, was used as the source document. The source content included the paper title, abstract, and extracted section text. For the scaled prototype, ten section-level source records related to microplastics, nanoplastics, human health, neurotoxicity, blood-brain barrier transport, reproductive health, and placental effects were selected.

### Ontology-Constrained Graph Construction

Graph construction was constrained by a predefined ontology. The entity schema defined allowed node types such as Study, Evidence, Observation, Biomarker, Mechanism, HostPopulation, Tissue/Organ, ExposurePathway, EnvironmentalCompartment, ClinicalOutcome, and Association. The relationship schema defined allowed edge types and helped prevent arbitrary relationship generation. The graph-building process separated evidence sentences from structured observations so that raw source text and interpreted claims were not conflated.

### Evidence Model

The graph used an evidence-aware structure in which exact source statements were represented as Evidence nodes. These Evidence nodes supported Observation nodes. Observations then connected to tissues, agents, exposure pathways, mechanisms, biomarkers, and outcome nodes. This structure allowed the dashboard to display provenance paths such as `Evidence -> Observation -> Outcome` and to distinguish direct evidence from downstream interpretation.

### Minimal Evidence-Gated Dashboard

The minimal dashboard was created as a small, manually inspectable graph slice. It includes one source review paper, one cited mouse study chain, two Evidence nodes, two Observation nodes, and one conservative outcome node. The graph contains 16 total nodes and 20 relationships. The selected evidence focuses on oral gavage exposure to polystyrene microplastics in mice, particle presence in mouse tissues, and liver metabolic and oxidative-stress marker changes. The minimal dashboard intentionally labels the resulting outcome as animal evidence and avoids interpreting it as direct human clinical evidence.

### 10-Paper Dashboard

The 10-paper dashboard extends the evidence-gated approach to ten section-level source records. It creates Paper, Evidence, Observation, and Concept nodes and links them through stored evidence sentences and matched scientific concepts. The resulting graph contains 188 entities and 365 relationships, including 80 Evidence nodes and 80 Observation nodes. The dashboard includes tabs for source papers, concepts, evidence, question answering, random-paper testing, and KG-vs-LLM comparison.

### Question Answering And LLM Comparison

The dashboard supports deterministic KG-based question answering. User questions are mapped to graph concepts, and answers are generated only when matching evidence exists in the graph. If no evidence is found, the dashboard returns a gap statement rather than inventing an answer. The 10-paper dashboard also includes a comparison workflow in which a user can paste or locally generate an LLM answer and compare it against the KG-supported answer. The comparison flags concepts that appear in the LLM answer but are not supported by the matched KG evidence.

## Results-Style Text

### One-Paper Full Dashboard Result

The one-paper v2 graph contained 115 entities and 304 relationships before presentation filtering. It included 10 Study nodes, 12 Evidence nodes, 14 Observation nodes, 14 HostPopulation nodes, and 8 Tissue/Organ nodes. All Observation nodes were directly supported by Evidence nodes. For the dashboard display, helper Association nodes were hidden, producing a cleaner graph view with 109 displayed nodes and 284 displayed relationships.

### Minimal Dashboard Result

The minimal dashboard produced a 16-node, 20-relationship evidence-gated graph. It demonstrated that a small graph could preserve provenance from an exact evidence sentence to a structured observation and then to a conservative outcome. The graph included two Evidence nodes and two Observation nodes, with 2/2 observations supported by direct evidence.

The provenance screenshot `01_minimal_evidence_observation_outcome_provenance.svg` shows the key path:

`evidence_liver_metabolic_oxidative_markers -> observation_liver_metabolic_oxidative_response -> outcome_hepatic_metabolic_alteration`

This path begins with an exact evidence sentence describing dose-dependent liver metabolic changes and oxidative-stress marker changes in mice. The evidence supports the structured observation "Mouse liver metabolic and oxidative-stress response." That observation then supports the conservative outcome node "Hepatic metabolic alteration." The relationship from Evidence to Observation has confidence 0.95 and is labeled direct evidence. The relationship from Observation to Outcome has confidence 0.75 and is labeled animal evidence/conservative outcome.

### 10-Paper Dashboard Result

The 10-paper dashboard scaled the evidence-gated structure to ten section-level records. The resulting graph contained 188 entities and 365 relationships. It included 18 concept nodes, 80 evidence nodes, and 80 observation nodes, with 80/80 observations supported by evidence. The overview screenshot `02_ten_paper_dashboard_overview.svg` summarizes these counts and the scaled workflow.

The 10-paper dashboard demonstrated that the evidence-gated workflow could be extended beyond a single paper while preserving explicit evidence nodes and observation nodes. Instead of emphasizing a single outcome path, the 10-paper version focuses on concept-level retrieval, question answering, random-paper testing, and comparison between KG-supported answers and external LLM-generated answers.

## Direct Response To Screenshot Request

Request: "Can you please provide me with one screenshot of the dashboard showing evidence --> observation --> outcome provenance tracing?"

Provided screenshot: `01_minimal_evidence_observation_outcome_provenance.svg`

This screenshot directly shows the requested provenance chain:

`Evidence -> Observation -> Outcome`

Specific traced chain:

`evidence_liver_metabolic_oxidative_markers -> observation_liver_metabolic_oxidative_response -> outcome_hepatic_metabolic_alteration`

Suggested figure caption:

"Evidence-gated dashboard screenshot showing provenance tracing from an exact evidence sentence to a structured observation and then to a conservative outcome node. The example links liver metabolic and oxidative-stress marker evidence from a mouse oral-gavage polystyrene microplastic study to the observation 'Mouse liver metabolic and oxidative-stress response' and the outcome label 'Hepatic metabolic alteration.' Confidence and evidence-strength metadata are displayed for each provenance link, preventing animal evidence from being overstated as direct human clinical evidence."
