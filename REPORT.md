# Microplastics Knowledge Graph — Short Report

**Paper:** *Neurotoxicity Following Exposure to Micro and Nanoplastics*
**Ontology:** `entities_v1.json` + `relationships_v1.json`

## What was built (3-step pipeline)
| Step | File | Contents |
|---|---|---|
| 1. Extraction | `mpkg_output_v1.json` | Knowledge graph built from the paper — **64 entities, 105 relationships** |
| 2. Critique | `mpkg_critique_v1.json` | Audit of v1 against paper + ontology (10 categories) |
| 3. Revision | `mpkg_output_v2.json` | Corrected graph — **64 entities, 119 relationships** |

**What's inside the output JSON** (`{entities, relationships}`):
- **Entities (v2):** 1 Study, 4 Polymers, 1 Shape, 8 size classes, 6 Methods, 12 Biomarkers,
  5 Mechanisms, 3 Clinical Outcomes, 2 Tissue/Organs, 3 Exposure Pathways, 13 Observations, 6 Associations.
- **Relationships:** study→observations/associations, observation→method/polymer/size,
  mechanism→biomarker/tissue, biomarker→tissue/study, etc.
- v2 adds what the critique found missing: **tissue/organ** nodes (brain, liver),
  **exposure pathways** (oral, inhalation, nasal), and an **apoptosis** mechanism;
  it also fixes unit errors and corrects the earthworm polymer (→ LDPE).

**Note on Shape:** the `Shape` entity is treated under the **environmental-study** context
(it characterizes the particles observed in the environmental/biological exposure studies),
consistent with the ontology's `sample_role: environment_study`.

## Graph links (live on GitHub Pages)
- **Menu:** https://Ag230602.github.io/microplastic_graph/
- **Original (v1):** https://Ag230602.github.io/microplastic_graph/mpkg_graph.html
- **Revised (v2):** https://Ag230602.github.io/microplastic_graph/mpkg_graph_v2.html
- **Critique:** https://Ag230602.github.io/microplastic_graph/mpkg_critique_graph.html

**Why created:** to *visually inspect the graph structure* — confirm nodes/edges are correct,
spot orphan/duplicate nodes, and compare v1 vs. the revised v2 at a glance.

## Why the critique graph has no "Study" node (v1 and v2 do)
- **v1 graph** and **v2 graph** are knowledge graphs of the paper — both are centered on the
  single review **Study** node (`study_neurotoxicity_following_exposure_review`).
- The **critique graph** is *not* a knowledge graph; it visualizes the audit report's structure
  (`Critique → Category → Finding/Recommendation`: 1 root, 10 categories, 33 findings,
  9 recommendations). It therefore has no Study node by design.

## Discrepancies to handle later
1. **R-1:** 3 article-mentioned items (`0.1–5 µm`, `40 nm`, `spherical`) were dropped from v2
   because their studies report only Associations (no Observation to attach size/shape).
   *Optional later fix:* add exposure-concentration Observations to keep them connected.
2. **Truncated sections:** some biomarkers (SOD, catalase, MDA, GST) cite references from paper
   sections not in our excerpt — directions need verification against the full text.
3. **Inferred unit:** the 20 µm value `0.8 mg/g` — unit assumed from the same study; confirm.
4. **Single review Study node:** all findings hang off one review node; primary studies
   ([41], [42], [85]…) are kept only as citations, so per-study provenance is limited.
