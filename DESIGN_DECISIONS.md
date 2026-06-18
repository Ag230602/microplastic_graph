# MPKG Pipeline — Design Decisions & Prompt Compliance

Paper: *Neurotoxicity Following Exposure to Micro and Nanoplastics*
Ontology: `entities_v1.json` + `relationships_v1.json`

## Pipeline artifacts
| Stage | Prompt | Output |
|---|---|---|
| 1. Extraction | KG Extraction (GPT-5.5) | `mpkg_output_v1.json` (64 entities, 105 relationships) |
| 2. Critique | Critique (Claude Opus) | `mpkg_critique_v1.json` (10-category audit) |
| 3. Revision | Revision (GPT-5.5) | `mpkg_output_v2.json` (64 entities, 119 relationships) |

Interactive viewers: `mpkg_graph.html` (v1), `mpkg_graph_v2.html` (v2), `mpkg_critique_graph.html` (critique).

## Prompt-compliance summary
- **Extraction:** Output is valid `{entities, relationships}`; only ontology types used; Observation vs. Association kept distinct; quantities preserved exactly (e.g., 0.2 / 1.0 / 1.4 mg/g).
- **Critique:** Exact 10-key schema; compared against both the paper and the ontology; conservative (missing preferred over unsupported).
- **Revision:** Strict `{entities, relationships}` JSON; ontology-compliant additions only; ontology violations and quantitative errors corrected.

## Documented design decisions

### R-1 — Three article-supported entities not carried into v2 (intentional)
Removed in revision: `size_0_1_to_5_um` (0.1–5 µm), `size_40_nm` (40 nm), `shape_spherical` (spherical).

- These sizes/shape **are** mentioned in the article (C. elegans: spherical polystyrene, 0.1–5 µm, 1 mg/L; rat: 40 nm polystyrene, 1–10 mg/kg/day).
- However, both studies report only **interpreted Associations** (movement/survival/lifespan effects; a null behavior/weight finding) and **no measured Observation**.
- In the ontology, `has_size_class`, `has_shape`, and `has_polymer` originate **only from `Observation`** nodes. With no Observation for these two studies, there is no ontology-valid edge to attach the entities.
- Including them would leave permanently disconnected nodes (a critique finding for v1). They were therefore dropped to keep the graph fully connected and ontology-clean.

**Trade-off / alternative:** A stricter reading of the Revision rule "preserve all valid entities" would re-add these three and create two new exposure-concentration `Observation` nodes (C. elegans 1 mg/L; rat 1–10 mg/kg/day) to anchor them. This is available on request; current v2 favors a connected, edge-justified graph.

### R-2 — Correctly removed (not supported)
- `size_50_nm`, `size_0_11_um`: not present in the provided article text (0.11 µm appears to be a misread of the 0.1 µm shrimp particle).
- `size_1_0_um`: exact duplicate of `size_1_um`.

### R-3 — Quantitative/ontology corrections applied in v2
- `Observation.unit` misuse ("presence reported" / "reported direction") → `categorical`, with descriptive text moved to `notes`.
- Earthworm polymer corrected from generic polyethylene to **low-density polyethylene (LDPE)** per the article.
- 20 µm plateau value `0.8 mg/g`: unit is inferred from the same study's 5 µm reporting basis; this is disclosed in the node `notes`.

## Validation
`mpkg_output_v2.json`: 64 entities, 119 relationships, no duplicate IDs, no dangling references, no orphan entities, all relationship types ontology-approved.
