#!/usr/bin/env python3
"""Build a 10-paper evidence-gated KG and standalone dashboard.

This is a deterministic prototype generator. It does not call an external LLM;
instead it creates the 10-paper source bundle, prompt artifacts for a future LLM
run, and a compact evidence-linked concept graph from available section text.
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA_SECTIONS = ROOT / "data" / "data_sections.json"
DATA_ABSTRACTS = ROOT / "data" / "data_title+abstract.json"

OUT_KG = HERE / "ten_paper_kg.json"
OUT_DASHBOARD = HERE / "ten_paper_dashboard.html"
OUT_README = HERE / "README.md"
OUT_SOURCE_BUNDLE = HERE / "ten_paper_source_bundle.json"
OUT_EXTRACTION_PROMPT = HERE / "ten_paper_extraction_prompt.txt"
OUT_CRITIQUE_PROMPT = HERE / "ten_paper_critique_prompt.txt"
OUT_REFINEMENT_PROMPT = HERE / "ten_paper_refinement_prompt.txt"


CONCEPTS = [
    {
        "id": "concept_microplastics",
        "name": "Microplastics",
        "category": "Agent",
        "keywords": ["microplastic", "microplastics", "mp ", "mps"],
    },
    {
        "id": "concept_nanoplastics",
        "name": "Nanoplastics",
        "category": "Agent",
        "keywords": ["nanoplastic", "nanoplastics", "np ", "nps", "mnp", "mnps"],
    },
    {
        "id": "concept_polystyrene",
        "name": "Polystyrene",
        "category": "Polymer",
        "keywords": ["polystyrene", "ps-mp", "ps-mps", "ps-np", "ps-nps", "ps particles"],
    },
    {
        "id": "concept_polyethylene",
        "name": "Polyethylene",
        "category": "Polymer",
        "keywords": ["polyethylene", " pe ", "ldpe", "hdpe"],
    },
    {
        "id": "concept_polypropylene",
        "name": "Polypropylene",
        "category": "Polymer",
        "keywords": ["polypropylene", " pp "],
    },
    {
        "id": "concept_pvc",
        "name": "Polyvinyl chloride",
        "category": "Polymer",
        "keywords": ["polyvinyl chloride", " pvc "],
    },
    {
        "id": "concept_brain",
        "name": "Brain / CNS",
        "category": "Tissue",
        "keywords": ["brain", "central nervous system", "cns", "cerebrospinal", "neural", "neuronal"],
    },
    {
        "id": "concept_bbb",
        "name": "Blood-brain barrier",
        "category": "Mechanism",
        "keywords": ["blood-brain barrier", "blood brain barrier", "bbb"],
    },
    {
        "id": "concept_oxidative_stress",
        "name": "Oxidative stress",
        "category": "Mechanism",
        "keywords": ["oxidative stress", "reactive oxygen", "ros", "superoxide", "antioxidant"],
    },
    {
        "id": "concept_inflammation",
        "name": "Inflammation",
        "category": "Mechanism",
        "keywords": ["inflammation", "inflammatory", "cytokine", "il-6", "il-8", "tnf"],
    },
    {
        "id": "concept_apoptosis",
        "name": "Apoptosis / cell death",
        "category": "Mechanism",
        "keywords": ["apoptosis", "cell death", "caspase", "necroptosis"],
    },
    {
        "id": "concept_neurotoxicity",
        "name": "Neurotoxicity",
        "category": "Outcome",
        "keywords": ["neurotoxicity", "neurotoxic", "neurodevelopment", "neurobehavior", "neurological"],
    },
    {
        "id": "concept_behavior",
        "name": "Behavioral change",
        "category": "Outcome",
        "keywords": ["behavior", "behaviour", "cognitive", "memory", "locomotor", "swimming"],
    },
    {
        "id": "concept_liver",
        "name": "Liver / hepatic effects",
        "category": "Tissue",
        "keywords": ["liver", "hepatic", "hepat"],
    },
    {
        "id": "concept_gut",
        "name": "Gut / intestinal effects",
        "category": "Tissue",
        "keywords": ["gut", "intestinal", "intestine", "gastrointestinal", "microbiota", "microbiome"],
    },
    {
        "id": "concept_placenta",
        "name": "Placenta / pregnancy",
        "category": "Tissue/Population",
        "keywords": ["placenta", "placental", "pregnancy", "fetal", "fetus", "gestation", "breast milk"],
    },
    {
        "id": "concept_fertility",
        "name": "Fertility / reproductive effects",
        "category": "Outcome",
        "keywords": ["fertility", "reproductive", "sperm", "ovary", "testis", "offspring"],
    },
    {
        "id": "concept_human",
        "name": "Human evidence",
        "category": "Host",
        "keywords": ["human", "patients", "subjects", "women", "children", "postpartum"],
    },
    {
        "id": "concept_mouse",
        "name": "Mouse / mammal evidence",
        "category": "Host",
        "keywords": ["mouse", "mice", "murine", "rat", "rats", "mammal"],
    },
    {
        "id": "concept_fish",
        "name": "Fish / aquatic evidence",
        "category": "Host",
        "keywords": ["fish", "zebrafish", "seabass", "aquatic"],
    },
]


EXCLUDED_TITLE_TERMS = [
    "greenness",
    "allergic rhinitis",
    "thallium",
    "microglial autophagy",
    "peyer",
    "stormwater",
]


def slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return value[:70] or "item"


def sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", clean)
    return [p.strip() for p in parts if len(p.strip()) > 35]


def record_text(record: dict) -> str:
    values = []
    for key, value in record.items():
        if isinstance(value, str):
            values.append(value)
    return "\n".join(values)


def title_of(record: dict) -> str:
    return record.get("Title") or record.get("title") or "Untitled source"


def abstract_of(record: dict) -> str:
    return record.get("Abstract") or record.get("abstract") or ""


def is_candidate(record: dict) -> bool:
    title = title_of(record).lower()
    text = (title + " " + abstract_of(record)).lower()
    if any(term in title for term in EXCLUDED_TITLE_TERMS):
        return False
    return "microplastic" in text or "nanoplastic" in text or "mnp" in text


def choose_papers(records: list[dict], limit: int = 10) -> list[dict]:
    selected = []
    seen = set()
    for record in records:
        title = title_of(record)
        key = title.lower()
        if key in seen or not is_candidate(record):
            continue
        seen.add(key)
        selected.append(record)
        if len(selected) == limit:
            break
    return selected


def evidence_type_for(text: str) -> str:
    lower = text.lower()
    if any(term in lower for term in ["human", "patients", "subjects", "women", "postpartum", "placental explants"]):
        return "human/in-vitro" if "explant" in lower or "cell" in lower else "human"
    if any(term in lower for term in ["mouse", "mice", "rat", "rats", "zebrafish", "fish"]):
        return "animal"
    if any(term in lower for term in ["cell", "organoid", "in vitro"]):
        return "in-vitro"
    if "review" in lower:
        return "review"
    return "mixed/unspecified"


def confidence_for(evidence_type: str, sentence: str) -> float:
    if evidence_type == "human":
        return 0.86
    if evidence_type == "animal":
        return 0.78
    if evidence_type == "human/in-vitro":
        return 0.74
    if evidence_type == "in-vitro":
        return 0.7
    if evidence_type == "review":
        return 0.64
    return 0.58


def concept_hits(text: str) -> list[dict]:
    lower = " " + text.lower() + " "
    hits = []
    for concept in CONCEPTS:
        count = 0
        for keyword in concept["keywords"]:
            count += lower.count(keyword.lower())
        if count:
            item = dict(concept)
            item["count"] = count
            hits.append(item)
    return sorted(hits, key=lambda x: (-x["count"], x["name"]))


def supporting_sentence(paper_sentences: list[str], concept: dict) -> str:
    for sentence in paper_sentences:
        lower = " " + sentence.lower() + " "
        if any(keyword.lower() in lower for keyword in concept["keywords"]):
            return sentence[:600]
    return ""


def build_graph(papers: list[dict]) -> dict:
    entities = []
    relationships = []
    concept_ids = set()
    evidence_count = 0
    observation_count = 0
    selected_sources = []
    paper_concepts = defaultdict(list)

    for index, paper in enumerate(papers, 1):
        title = title_of(paper)
        text = record_text(paper)
        paper_id = f"paper_{index:02d}_{slug(title)}"
        paper_sentences = sentences(text)
        hits = concept_hits(text)
        top_hits = hits[:8]
        evidence_type = evidence_type_for(text)
        selected_sources.append({
            "id": paper_id,
            "title": title,
            "abstract": abstract_of(paper)[:1200],
            "section_count": len([k for k in paper.keys() if k not in ("Title", "Abstract")]),
            "character_count": len(text),
            "evidence_type": evidence_type,
            "matched_concepts": [hit["name"] for hit in top_hits],
        })
        entities.append({
            "id": paper_id,
            "type": "Paper",
            "name": title,
            "definition": "Section-level source paper used in the 10-paper evidence-gated prototype.",
            "evidence_type": evidence_type,
            "section_count": len([k for k in paper.keys() if k not in ("Title", "Abstract")]),
            "character_count": len(text),
            "abstract": abstract_of(paper)[:1200],
        })

        for concept in top_hits:
            concept_ids.add(concept["id"])
            paper_concepts[paper_id].append(concept["id"])
            sentence = supporting_sentence(paper_sentences, concept)
            confidence = confidence_for(evidence_type, sentence)
            evidence_count += 1
            evidence_id = f"evidence_{index:02d}_{evidence_count:03d}_{concept['id'].replace('concept_', '')}"
            observation_count += 1
            observation_id = f"observation_{index:02d}_{observation_count:03d}_{concept['id'].replace('concept_', '')}"
            entities.append({
                "id": evidence_id,
                "type": "Evidence",
                "name": f"Evidence for {concept['name']} in Paper {index}",
                "paper_id": paper_id,
                "paper_title": title,
                "concept_id": concept["id"],
                "concept_name": concept["name"],
                "evidence_sentence": sentence,
                "evidence_type": evidence_type,
                "confidence": round(confidence, 2),
            })
            entities.append({
                "id": observation_id,
                "type": "Observation",
                "name": f"{title[:70]}: {concept['name']}",
                "paper_id": paper_id,
                "concept_id": concept["id"],
                "concept_name": concept["name"],
                "definition": f"Structured observation that this source discusses {concept['name']}.",
                "evidence_type": evidence_type,
                "confidence": round(max(confidence - 0.04, 0.5), 2),
            })
            relationships.extend([
                {
                    "id": f"rel_paper_evidence_{evidence_count:03d}",
                    "relationship_name": "provides",
                    "source_node": paper_id,
                    "target_node": evidence_id,
                    "evidence_sentence": sentence,
                    "confidence": round(confidence, 2),
                    "relationship_strength": evidence_type,
                },
                {
                    "id": f"rel_evidence_observation_{evidence_count:03d}",
                    "relationship_name": "supports",
                    "source_node": evidence_id,
                    "target_node": observation_id,
                    "evidence_sentence": sentence,
                    "confidence": round(confidence, 2),
                    "relationship_strength": evidence_type,
                },
                {
                    "id": f"rel_observation_concept_{evidence_count:03d}",
                    "relationship_name": "about_concept",
                    "source_node": observation_id,
                    "target_node": concept["id"],
                    "evidence_sentence": sentence,
                    "confidence": round(max(confidence - 0.04, 0.5), 2),
                    "relationship_strength": evidence_type,
                },
                {
                    "id": f"rel_paper_concept_{evidence_count:03d}",
                    "relationship_name": "mentions_concept",
                    "source_node": paper_id,
                    "target_node": concept["id"],
                    "evidence_sentence": sentence,
                    "confidence": round(max(confidence - 0.08, 0.5), 2),
                    "relationship_strength": evidence_type,
                },
            ])

    for concept in CONCEPTS:
        if concept["id"] in concept_ids:
            entities.append({
                "id": concept["id"],
                "type": "Concept",
                "name": concept["name"],
                "category": concept["category"],
                "keywords": concept["keywords"],
                "definition": f"Controlled concept matched across the 10-paper source set: {concept['name']}.",
            })

    shared_rel_index = 0
    paper_items = list(paper_concepts.items())
    for left_index, (left_paper, left_concepts) in enumerate(paper_items):
        for right_paper, right_concepts in paper_items[left_index + 1:]:
            shared = sorted(set(left_concepts) & set(right_concepts))
            if len(shared) < 3:
                continue
            shared_rel_index += 1
            relationships.append({
                "id": f"rel_shared_concepts_{shared_rel_index:03d}",
                "relationship_name": "shares_concepts_with",
                "source_node": left_paper,
                "target_node": right_paper,
                "shared_concepts": shared,
                "evidence_sentence": f"Shared matched concepts: {', '.join(shared)}",
                "confidence": 0.72,
                "relationship_strength": "cross-paper concept overlap",
            })

    type_counts = Counter(entity["type"] for entity in entities)
    evidence_nodes = type_counts.get("Evidence", 0)
    observation_nodes = type_counts.get("Observation", 0)
    return {
        "experiment": "10-paper evidence-gated environmental health KG",
        "purpose": "Scale the minimal evidence-gated dashboard concept from one source paper to 10 section-level source papers with deterministic concept matching, question testing, and KG-vs-LLM answer comparison.",
        "source_files": ["../../data/data_sections.json", "../../data/data_title+abstract.json"],
        "selection_rule": "First 10 unique micro/nanoplastic-relevant section records, excluding obvious non-microplastic or duplicate records.",
        "counts": {
            "papers": len(papers),
            "entities": len(entities),
            "relationships": len(relationships),
            "concept_nodes": type_counts.get("Concept", 0),
            "evidence_nodes": evidence_nodes,
            "observation_nodes": observation_nodes,
            "evidence_supported_observations": f"{observation_nodes}/{observation_nodes}",
        },
        "selected_sources": selected_sources,
        "entities": entities,
        "relationships": relationships,
        "qa_policy": {
            "answer_rule": "Only answer with concepts and evidence sentences found in ten_paper_kg.json.",
            "gap_rule": "If no concept/evidence match is found, return a gap/refusal rather than guessing.",
            "comparison_rule": "LLM answers are compared against KG-supported concepts and evidence; unsupported terms are flagged for review.",
        },
    }


def source_bundle(papers: list[dict], graph: dict) -> list[dict]:
    bundle = []
    ids = [source["id"] for source in graph["selected_sources"]]
    for paper_id, paper in zip(ids, papers):
        bundle.append({
            "paper_id": paper_id,
            "title": title_of(paper),
            "abstract": abstract_of(paper),
            "sections": {key: value for key, value in paper.items() if key not in ("Title", "Abstract")},
        })
    return bundle


def write_prompts(graph: dict, papers: list[dict]) -> None:
    source_lines = []
    for source in graph["selected_sources"]:
        source_lines.append(f"- {source['id']}: {source['title']}")
    source_payload = json.dumps(source_bundle(papers, graph), indent=2, ensure_ascii=True)

    extraction = f"""You are a scientific knowledge graph extraction system for a 10-paper Microplastics Knowledge Graph.

Task: extract ontology-compliant entities and relationships from the 10 selected source papers listed below.

Rules:
1. Use only evidence explicitly supported by the supplied title, abstract, and section text.
2. Separate Evidence nodes from Observation nodes.
3. Do not generalize animal or in-vitro findings to direct human clinical conclusions.
4. Preserve provenance by attaching the source paper title and exact evidence sentence.
5. Return strict JSON with top-level keys: entities, relationships, counts, selected_sources.

Selected 10-paper source set:
{chr(10).join(source_lines)}

SOURCE PAPER CONTENT
{source_payload}

Expected evidence chain:
Paper -> Evidence -> Observation -> Concept -> Mechanism/Biomarker/Outcome/Gap
"""

    critique = f"""You are a Knowledge Graph Auditor for the 10-paper Microplastics KG.

Audit the extracted graph against the 10 selected source papers.

Check:
1. unsupported entities
2. unsupported relationships
3. missing evidence sentences
4. overclaims from animal/in-vitro evidence to human health
5. duplicate concepts
6. missing research gaps
7. weak or missing provenance

Return JSON with: critical_errors, unsupported_entities, unsupported_relationships, missing_entities, missing_relationships, evidence_gaps, recommendations.

Selected source set:
{chr(10).join(source_lines)}

Source content is stored in ten_paper_source_bundle.json and mirrored in the extraction prompt.
"""

    refinement = f"""You are refining a 10-paper evidence-gated Microplastics KG after critique.

Goals:
1. keep only supported entities and relationships
2. preserve exact evidence sentences
3. mark evidence type as human, animal, in-vitro, review, or mixed/unspecified
4. create conservative research-gap statements
5. ensure the dashboard can support question answering and KG-vs-LLM answer comparison

Return strict JSON only.
"""

    OUT_EXTRACTION_PROMPT.write_text(extraction, encoding="utf-8")
    OUT_CRITIQUE_PROMPT.write_text(critique, encoding="utf-8")
    OUT_REFINEMENT_PROMPT.write_text(refinement, encoding="utf-8")


def dashboard_html(graph: dict) -> str:
    payload = json.dumps(graph, ensure_ascii=True)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>10-Paper Evidence-Gated Microplastics KG</title>
<style>
:root {{ --bg:#f6f7f9; --panel:#fff; --ink:#1f2933; --muted:#607080; --line:#d5dde6; --blue:#2f6f9f; --green:#238b6e; --gold:#a97814; --red:#b54747; --purple:#7357a5; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; color:var(--ink); background:var(--bg); }}
header {{ padding:18px 22px; background:var(--panel); border-bottom:1px solid var(--line); }}
h1 {{ margin:0 0 6px; font-size:22px; letter-spacing:0; }}
h2 {{ margin:0 0 10px; font-size:17px; letter-spacing:0; }}
h3 {{ margin:0 0 8px; font-size:14px; letter-spacing:0; }}
p {{ line-height:1.55; }}
.sub,.small {{ color:var(--muted); font-size:13px; line-height:1.45; }}
nav {{ display:flex; gap:8px; flex-wrap:wrap; padding:12px 22px; background:#fbfaf7; border-bottom:1px solid var(--line); position:sticky; top:0; z-index:5; }}
button,.button {{ border:1px solid var(--line); background:#fff; border-radius:6px; padding:8px 11px; cursor:pointer; font:inherit; font-size:13px; }}
button.active {{ border-color:var(--blue); color:var(--blue); font-weight:700; }}
main {{ max-width:1280px; margin:0 auto; padding:18px 22px; }}
.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:15px; margin-bottom:14px; min-width:0; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:12px; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; }}
.card {{ border:1px solid var(--line); border-radius:8px; padding:13px; background:#fff; }}
.n {{ font-size:28px; font-weight:800; color:var(--blue); }}
.pill {{ display:inline-block; border-radius:999px; padding:3px 8px; font-size:12px; font-weight:700; margin:2px 4px 2px 0; background:#eef5f7; color:#21566a; }}
.good {{ background:#eef8f4; color:#136b55; }} .warn {{ background:#fff4df; color:#7b4b00; }} .bad {{ background:#ffecec; color:#8e2d2d; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; table-layout:fixed; }}
th,td {{ border-bottom:1px solid var(--line); padding:8px; text-align:left; vertical-align:top; overflow-wrap:anywhere; }}
th {{ background:#f9fafb; }}
textarea,input {{ width:100%; border:1px solid var(--line); border-radius:7px; padding:9px; font:inherit; font-size:13px; background:#fff; }}
textarea {{ min-height:120px; resize:vertical; }}
.hidden {{ display:none; }}
.quote {{ border-left:3px solid var(--gold); background:#fffaf0; padding:9px 10px; margin:8px 0; font-size:13px; line-height:1.45; }}
.result {{ border:1px solid var(--line); border-radius:8px; padding:12px; background:#fbfdff; margin-top:10px; }}
.concept {{ display:inline-block; border:1px solid var(--line); border-radius:6px; padding:6px 8px; margin:3px; font-size:12px; background:#fff; }}
.two {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:12px; }}
@media (max-width:800px) {{ .two {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>10-Paper Evidence-Gated Microplastics KG</h1>
  <div class=\"sub\">A deterministic 10-paper prototype that scales the minimal dashboard idea: evidence-linked concepts, question testing, random-paper concept matching, and KG-vs-LLM answer comparison.</div>
</header>
<nav id=\"tabs\"></nav>
<main id=\"main\"></main>
<script>
const DATA = {payload};
const TABS = [
  ['overview','Overview'], ['papers','Papers'], ['concepts','Concepts'], ['evidence','Evidence'],
  ['qa','Question Answering'], ['test','Random Paper Test'], ['compare','KG vs LLM Compare'], ['workflow','Workflow']
];
const esc = value => String(value ?? '').replace(/[&<>\"]/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}}[ch]));
const byId = Object.fromEntries(DATA.entities.map(entity => [entity.id, entity]));
const concepts = DATA.entities.filter(entity => entity.type === 'Concept');
const papers = DATA.entities.filter(entity => entity.type === 'Paper');
const evidence = DATA.entities.filter(entity => entity.type === 'Evidence');
const observations = DATA.entities.filter(entity => entity.type === 'Observation');

function norm(text) {{ return String(text || '').toLowerCase(); }}
function conceptMatches(text) {{
  const lower = ' ' + norm(text) + ' ';
  return concepts.map(concept => {{
    const count = (concept.keywords || []).reduce((sum, keyword) => sum + lower.split(String(keyword).toLowerCase()).length - 1, 0);
    return {{...concept, count}};
  }}).filter(item => item.count > 0).sort((a,b) => b.count - a.count || a.name.localeCompare(b.name));
}}
function paperScore(text) {{
  const matched = conceptMatches(text);
  const matchIds = new Set(matched.map(item => item.id));
  return papers.map(paper => {{
    const rels = DATA.relationships.filter(rel => rel.source_node === paper.id && rel.relationship_name === 'mentions_concept');
    const paperConcepts = rels.map(rel => rel.target_node);
    const shared = paperConcepts.filter(id => matchIds.has(id));
    return {{paper, score: shared.length, shared}};
  }}).filter(row => row.score > 0).sort((a,b) => b.score - a.score || a.paper.name.localeCompare(b.paper.name));
}}
function evidenceForConcepts(ids, limit=8) {{
  const wanted = new Set(ids);
  return evidence.filter(ev => wanted.has(ev.concept_id)).slice(0, limit);
}}
function kgAnswer(question) {{
  const matches = conceptMatches(question);
  const ids = matches.map(match => match.id);
  const rows = evidenceForConcepts(ids, 10);
  if (!matches.length || !rows.length) {{
    return {{allowed:false, matches, rows, answer:'The KG does not contain enough matched evidence for this question. This is a research gap rather than a supported answer.'}};
  }}
  const conceptNames = matches.slice(0,6).map(match => match.name).join(', ');
  const paperNames = [...new Set(rows.map(row => row.paper_title))].slice(0,4).join('; ');
  const answer = `The KG finds evidence related to ${{conceptNames}}. Supporting evidence appears in: ${{paperNames}}. The answer should remain evidence-gated: use the stored sentences below and avoid claims beyond the represented papers.`;
  return {{allowed:true, matches, rows, answer}};
}}
function renderTabs(active='overview') {{
  document.getElementById('tabs').innerHTML = TABS.map(([id,label]) => `<button class=\"${{id===active?'active':''}}\" onclick=\"showTab('${{id}}')\">${{label}}</button>`).join('');
}}
function showTab(id) {{ renderTabs(id); document.getElementById('main').innerHTML = views[id](); }}

const views = {{
overview() {{
  const c = DATA.counts;
  return `<div class=\"grid\">
    ${{[['Papers',c.papers],['Entities',c.entities],['Relationships',c.relationships],['Concepts',c.concept_nodes],['Evidence Nodes',c.evidence_nodes],['Observations',c.observation_nodes]].map(([label,n]) => `<div class=\"panel\"><div class=\"n\">${{n}}</div><div class=\"small\">${{label}}</div></div>`).join('')}}
  </div>
  <div class=\"panel\"><h2>Purpose</h2><p>${{esc(DATA.purpose)}}</p><p><span class=\"pill good\">No external LLM calls in dashboard</span><span class=\"pill warn\">Evidence-gated prototype</span><span class=\"pill\">10 papers</span></p></div>
  <div class=\"panel\"><h2>Evidence Flow</h2><p>Paper -> Evidence -> Observation -> Concept -> Question Answering -> Gap or Answer -> KG-vs-LLM comparison.</p></div>`;
}},
papers() {{
  return `<div class=\"panel\"><h2>Selected 10 Papers</h2><table><tr><th>Paper</th><th>Evidence Type</th><th>Matched Concepts</th><th>Size</th></tr>${{DATA.selected_sources.map(src => `<tr><td><b>${{esc(src.title)}}</b><br><span class=\"small\">${{esc(src.id)}}</span></td><td><span class=\"pill\">${{esc(src.evidence_type)}}</span></td><td>${{src.matched_concepts.map(c => `<span class=\"concept\">${{esc(c)}}</span>`).join('')}}</td><td>${{src.section_count}} sections<br>${{src.character_count}} chars</td></tr>`).join('')}}</table></div>`;
}},
concepts() {{
  const counts = Object.fromEntries(concepts.map(concept => [concept.id, DATA.relationships.filter(rel => rel.target_node === concept.id && rel.relationship_name === 'mentions_concept').length]));
  return `<div class=\"panel\"><h2>Concept Layer</h2><table><tr><th>Concept</th><th>Category</th><th>Paper Count</th><th>Keywords</th></tr>${{concepts.sort((a,b)=>(counts[b.id]||0)-(counts[a.id]||0)).map(c => `<tr><td><b>${{esc(c.name)}}</b><br><span class=\"small\">${{esc(c.id)}}</span></td><td>${{esc(c.category)}}</td><td>${{counts[c.id]||0}}</td><td>${{(c.keywords||[]).map(k => `<span class=\"concept\">${{esc(k)}}</span>`).join('')}}</td></tr>`).join('')}}</table></div>`;
}},
evidence() {{
  return `<div class=\"panel\"><h2>Evidence Table</h2><table><tr><th>Evidence</th><th>Concept</th><th>Paper</th><th>Sentence</th><th>Confidence</th></tr>${{evidence.map(ev => `<tr><td>${{esc(ev.name)}}</td><td>${{esc(ev.concept_name)}}</td><td>${{esc(ev.paper_title)}}</td><td>${{esc(ev.evidence_sentence)}}</td><td><span class=\"pill\">${{esc(ev.confidence)}}</span><br><span class=\"small\">${{esc(ev.evidence_type)}}</span></td></tr>`).join('')}}</table></div>`;
}},
qa() {{
  return `<div class=\"panel\"><h2>Evidence-Gated Question Answering</h2><div class=\"grid\"><button onclick=\"setQuestion('What evidence links microplastics to oxidative stress?')\">Oxidative stress</button><button onclick=\"setQuestion('Do microplastics affect the blood-brain barrier and brain?')\">Brain / BBB</button><button onclick=\"setQuestion('What evidence exists for pregnancy or placenta effects?')\">Pregnancy / placenta</button><button onclick=\"setQuestion('Is there human evidence for neurotoxicity?')\">Human neurotoxicity</button></div><textarea id=\"question\" placeholder=\"Ask a question about microplastics, tissue, host, mechanism, biomarker, or outcome...\"></textarea><p><button onclick=\"runQA()\">Run KG Answer</button></p><div id=\"qaResult\"></div></div>`;
}},
test() {{
  return `<div class=\"panel\"><h2>Random Paper Test</h2><p class=\"small\">Paste a random paper title/abstract. The dashboard checks whether it overlaps with concepts already represented in the 10-paper KG and recommends whether it should be added.</p><textarea id=\"paperText\" placeholder=\"Paste title and abstract here...\"></textarea><p><button onclick=\"runPaperTest()\">Test Paper Against KG</button></p><div id=\"paperTestResult\"></div></div>`;
}},
compare() {{
    return `<div class=\"panel\"><h2>Compare LLM Answer Against KG Answer</h2><p class=\"small\">Paste an LLM answer manually, or generate one through the local backend after setting an OpenAI or Gemini key in your terminal. The key is never stored in this HTML file.</p><div class=\"two\"><div><h3>Question</h3><textarea id=\"compareQuestion\" placeholder=\"Paste the question here...\"></textarea><h3>LLM Answer</h3><textarea id=\"llmAnswer\" placeholder=\"Paste any LLM answer here, or generate one with the local backend...\"></textarea><p><button onclick=\"generateLLMAnswer()\">Generate LLM Answer Locally</button> <button onclick=\"runCompare()\">Compare</button></p><p class=\"small\" id=\"llmStatus\">Local backend expected at <code>http://127.0.0.1:8765/api/llm</code>.</p></div><div><h3>Result</h3><div id=\"compareResult\" class=\"result\">Run comparison to see KG-supported concepts, missing evidence, and possible overclaim flags.</div></div></div></div>`;
}},
workflow() {{
  return `<div class=\"panel\"><h2>Workflow</h2><ol><li>Select 10 unique micro/nanoplastic section-level papers from data_sections.json.</li><li>Create prompt artifacts for extraction, critique, and refinement.</li><li>Build deterministic evidence-linked concepts from section text.</li><li>Create Paper, Evidence, Observation, and Concept nodes.</li><li>Use the dashboard to test questions, screen random papers, and compare external LLM answers with KG-supported answers.</li></ol><p class=\"small\">This prototype does not call an external LLM. It prepares the prompt workflow and demonstrates the evidence gate locally.</p></div>`;
}}
}};

function setQuestion(text) {{ document.getElementById('question').value = text; runQA(); }}
function renderAnswer(result) {{
  return `<div class=\"result\"><p><span class=\"pill ${{result.allowed?'good':'bad'}}\">${{result.allowed?'KG answer allowed':'Gap / insufficient evidence'}}</span></p><p>${{esc(result.answer)}}</p><h3>Matched Concepts</h3><p>${{result.matches.slice(0,8).map(m => `<span class=\"concept\">${{esc(m.name)}} (${{m.count}})</span>`).join('') || 'None'}}</p><h3>Evidence</h3>${{result.rows.map(row => `<div class=\"quote\"><b>${{esc(row.concept_name)}}</b> - ${{esc(row.paper_title)}}<br>${{esc(row.evidence_sentence)}}</div>`).join('') || '<p class=\"small\">No stored evidence matched.</p>'}}</div>`;
}}
function runQA() {{ const result = kgAnswer(document.getElementById('question').value); document.getElementById('qaResult').innerHTML = renderAnswer(result); }}
function runPaperTest() {{
  const text = document.getElementById('paperText').value;
  const matches = conceptMatches(text);
  const scores = paperScore(text);
  const recommendation = matches.length >= 4 ? 'High overlap: candidate is related to the existing KG and can be added with evidence extraction.' : matches.length ? 'Partial overlap: candidate may be relevant, but needs review.' : 'Low overlap: no strong concept match in the current 10-paper KG.';
  document.getElementById('paperTestResult').innerHTML = `<div class=\"result\"><p><span class=\"pill ${{matches.length>=4?'good':matches.length?'warn':'bad'}}\">${{recommendation}}</span></p><h3>Matched KG Concepts</h3><p>${{matches.map(m => `<span class=\"concept\">${{esc(m.name)}} (${{m.count}})</span>`).join('') || 'None'}}</p><h3>Nearest Existing Papers</h3><table><tr><th>Paper</th><th>Shared Concepts</th></tr>${{scores.slice(0,5).map(row => `<tr><td>${{esc(row.paper.name)}}</td><td>${{row.shared.map(id => `<span class=\"concept\">${{esc(byId[id]?.name || id)}}</span>`).join('')}}</td></tr>`).join('') || '<tr><td colspan=\"2\">No similar paper found.</td></tr>'}}</table></div>`;
}}
async function generateLLMAnswer() {{
    const question = document.getElementById('compareQuestion').value.trim();
    const status = document.getElementById('llmStatus');
    if (!question) {{ status.innerHTML = '<span class=\"pill bad\">Add a question first.</span>'; return; }}
    status.innerHTML = '<span class=\"pill warn\">Calling local LLM backend...</span>';
    try {{
        const response = await fetch('http://127.0.0.1:8765/api/llm', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{question}})
        }});
        const data = await response.json();
        if (!data.ok) throw new Error(data.error || 'Local backend returned an error.');
        document.getElementById('llmAnswer').value = data.answer;
        status.innerHTML = `<span class=\"pill good\">Generated with ${{esc(data.model || 'local LLM backend')}}</span>`;
        runCompare();
    }} catch (error) {{
        status.innerHTML = `<span class=\"pill bad\">${{esc(error.message)}}. Restart the local server and enter a fresh OpenAI or Gemini key in that terminal.</span>`;
    }}
}}
function runCompare() {{
  const question = document.getElementById('compareQuestion').value;
  const llm = document.getElementById('llmAnswer').value;
  const kg = kgAnswer(question);
  const kgConceptIds = new Set(kg.matches.map(m => m.id));
  const llmMatches = conceptMatches(llm);
  const unsupported = llmMatches.filter(m => !kgConceptIds.has(m.id));
  const overclaimFlags = [];
  const lower = norm(llm);
  if ((lower.includes('proves') || lower.includes('causes') || lower.includes('definitely')) && !lower.includes('limited')) overclaimFlags.push('Strong causal wording without visible uncertainty');
  if (lower.includes('human') && kg.rows.every(row => row.evidence_type !== 'human')) overclaimFlags.push('Human claim may not be directly supported by matched KG evidence');
  document.getElementById('compareResult').innerHTML = `${{renderAnswer(kg)}}<div class=\"panel\"><h3>LLM Answer Audit</h3><p><b>LLM concepts found:</b> ${{llmMatches.map(m => `<span class=\"concept\">${{esc(m.name)}}</span>`).join('') || 'None'}}</p><p><b>Concepts in LLM answer not matched by KG question evidence:</b> ${{unsupported.map(m => `<span class=\"concept\">${{esc(m.name)}}</span>`).join('') || 'None'}}</p><p><b>Overclaim flags:</b> ${{overclaimFlags.map(flag => `<span class=\"pill bad\">${{esc(flag)}}</span>`).join('') || '<span class=\"pill good\">No simple overclaim flag detected</span>'}}</p></div>`;
}}

showTab('overview');
</script>
</body>
</html>
"""


def write_readme(graph: dict) -> None:
    source_list = "\n".join(f"- {source['title']}" for source in graph["selected_sources"])
    text = f"""# 10-Paper Evidence-Gated KG Experiment

This experiment scales the minimal evidence-gated dashboard concept from one paper to 10 section-level source papers.

## Counts

- Papers: {graph['counts']['papers']}
- Entities: {graph['counts']['entities']}
- Relationships: {graph['counts']['relationships']}
- Concept nodes: {graph['counts']['concept_nodes']}
- Evidence nodes: {graph['counts']['evidence_nodes']}
- Observation nodes: {graph['counts']['observation_nodes']}
- Evidence-supported observations: {graph['counts']['evidence_supported_observations']}

## Selected Papers

{source_list}

## Important Scope Note

By default, this prototype does not call an external LLM. It creates prompt artifacts for extraction, critique, and refinement, then builds a deterministic concept/evidence KG from available section text. The dashboard includes question answering, random-paper testing, and KG-vs-LLM answer comparison based only on stored graph evidence.

The comparison tab can optionally call a local LLM proxy if you start `local_llm_server.py` with a fresh OpenAI or Gemini API key. Never store API keys in HTML, JSON, prompts, or chat.

## Optional Local LLM Test Setup

Use a newly created API key and keep it local to your shell. OpenAI and Gemini are both supported.

```bash
export OPENAI_API_KEY="your_new_key_here"
python3 experiments/ten_paper_evidence_gated/local_llm_server.py
```

For Gemini, use either:

```bash
export GEMINI_API_KEY="your_new_key_here"
python3 experiments/ten_paper_evidence_gated/local_llm_server.py
```

or run the server with no key set and paste only the key when the hidden Python prompt appears.

Then open:

```text
http://127.0.0.1:8765/experiments/ten_paper_evidence_gated/ten_paper_dashboard.html
```

The dashboard button `Generate LLM Answer Locally` calls only `http://127.0.0.1:8765/api/llm`.

## Files

- `ten_paper_kg.json`: generated graph data
- `ten_paper_source_bundle.json`: selected 10-paper title/abstract/section source bundle
- `ten_paper_dashboard.html`: standalone dashboard
- `ten_paper_extraction_prompt.txt`: 10-paper extraction prompt scaffold
- `ten_paper_critique_prompt.txt`: 10-paper critique prompt scaffold
- `ten_paper_refinement_prompt.txt`: 10-paper refinement prompt scaffold
- `build_ten_paper_experiment.py`: reproducible generator
- `local_llm_server.py`: optional local API-key-safe LLM proxy for comparison testing
"""
    OUT_README.write_text(text, encoding="utf-8")


def main() -> None:
    records = json.loads(DATA_SECTIONS.read_text(encoding="utf-8"))
    papers = choose_papers(records, 10)
    if len(papers) != 10:
        raise RuntimeError(f"Expected 10 papers, selected {len(papers)}")
    graph = build_graph(papers)
    OUT_KG.write_text(json.dumps(graph, indent=2, ensure_ascii=True), encoding="utf-8")
    OUT_SOURCE_BUNDLE.write_text(json.dumps(source_bundle(papers, graph), indent=2, ensure_ascii=True), encoding="utf-8")
    write_prompts(graph, papers)
    OUT_DASHBOARD.write_text(dashboard_html(graph), encoding="utf-8")
    write_readme(graph)
    print(f"Wrote {OUT_KG.relative_to(ROOT)}")
    print(f"Wrote {OUT_DASHBOARD.relative_to(ROOT)}")
    print(f"Entities: {graph['counts']['entities']} Relationships: {graph['counts']['relationships']}")


if __name__ == "__main__":
    main()