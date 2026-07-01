#!/usr/bin/env python3
"""Build a small evidence-first MPKG experiment without changing the full graph.

The goal is to test a conservative workflow on 5-10 evidence-backed claims.
This script reads ../../mpkg_output_v2.json and writes focused subset artifacts
inside this folder only.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FULL = ROOT / "mpkg_output_v2.json"
OUT_JSON = HERE / "focused_mpkg_output_test.json"
OUT_GRAPH = HERE / "focused_mpkg_graph_test.json"
OUT_SUMMARY = HERE / "FOCUSED_EXPERIMENT.md"

SELECTED_EVIDENCE = [
    "evidence_mouse_liver_accumulation",
    "evidence_mouse_brain_cytokines",
    "evidence_mouse_brain_caspase3",
    "evidence_earthworm_uptake",
    "evidence_zebra_mussel_accumulation",
    "evidence_celegans_effects",
]

OBS_RELATIONS = {"has_polymer", "has_size_class", "has_shape", "about", "affects", "identified_by"}

OBS_TO_HOST = {
    "obs_mouse_liver_5um_ps_concentration": "host_mouse",
    "obs_mouse_brain_tnf_il6_upregulated": "host_mouse",
    "obs_mouse_brain_caspase3_increased": "host_mouse",
    "obs_earthworm_polyethylene_uptake": "host_earthworm",
    "obs_zebra_mussel_polystyrene_microbeads_accumulation": "host_zebra_mussel",
    "obs_celegans_polystyrene_exposure_effects": "host_c_elegans",
}

OBS_TO_BIOMARKERS = {
    "obs_mouse_brain_tnf_il6_upregulated": ["biomarker_tnf_alpha", "biomarker_il_6"],
    "obs_mouse_brain_caspase3_increased": ["biomarker_caspase_3"],
}

OBS_TO_MECHANISMS = {
    "obs_mouse_brain_tnf_il6_upregulated": ["mechanism_inflammation"],
    "obs_mouse_brain_caspase3_increased": ["mechanism_apoptosis"],
}

OBS_TO_OUTCOMES = {
    "obs_celegans_polystyrene_exposure_effects": ["outcome_lower_survival_lifespan"],
}


def label_for(entity):
    for key in ("title", "name", "label", "pathway_label", "method_class", "text", "relationship"):
        if entity.get(key):
            value = str(entity[key])
            return value[:60] + "..." if len(value) > 63 else value
    return entity["id"]


def main():
    data = json.loads(FULL.read_text(encoding="utf-8"))
    entities = {entity["id"]: entity for entity in data["entities"]}
    relationships = data["relationships"]

    keep_nodes = set()
    keep_edges = []

    def add_node(node_id):
        if node_id in entities:
            keep_nodes.add(node_id)

    def add_edge(edge):
        add_node(edge["source_id"])
        add_node(edge["target_id"])
        if edge not in keep_edges:
            keep_edges.append(edge)

    # 1. Seed with selected Evidence -> Observation and Study -> Evidence chains.
    for evidence_id in SELECTED_EVIDENCE:
        add_node(evidence_id)
        for edge in relationships:
            if edge["relation_type"] == "provides" and edge["target_id"] == evidence_id:
                add_edge(edge)
            if edge["relation_type"] == "supports" and edge["source_id"] == evidence_id:
                add_edge(edge)

    # 2. Add observation context: polymer, reservoir, tissue, size/shape, method.
    selected_observations = {
        edge["target_id"]
        for edge in keep_edges
        if edge["relation_type"] == "supports" and edge["source_id"] in SELECTED_EVIDENCE
    }
    for edge in relationships:
        if edge["source_id"] in selected_observations and edge["relation_type"] in OBS_RELATIONS:
            add_edge(edge)
        if edge["target_id"] in selected_observations and edge["relation_type"] == "reports":
            add_edge(edge)

    # 3. Add only direct host, pathway, mechanism, biomarker, and outcome context.
    for observation_id in selected_observations:
        host_id = OBS_TO_HOST.get(observation_id)
        if host_id:
            add_node(host_id)
        for node_id in OBS_TO_BIOMARKERS.get(observation_id, []):
            add_node(node_id)
        for node_id in OBS_TO_MECHANISMS.get(observation_id, []):
            add_node(node_id)
        for node_id in OBS_TO_OUTCOMES.get(observation_id, []):
            add_node(node_id)

    for edge in relationships:
        relation = edge["relation_type"]
        if relation == "investigates" and edge["source_id"] in keep_nodes and edge["target_id"] in keep_nodes:
            add_edge(edge)
        elif relation == "reports" and edge["source_id"] in keep_nodes and edge["target_id"] in keep_nodes:
            add_edge(edge)
        elif relation == "exposes" and edge["target_id"] in keep_nodes:
            add_edge(edge)
        elif relation == "contributes_to" and edge["source_id"] in keep_nodes and edge["target_id"] in keep_nodes:
            add_edge(edge)
        elif relation == "originates_from" and edge["source_id"] in keep_nodes and edge["target_id"] in keep_nodes:
            add_edge(edge)
        elif relation == "contains" and edge["source_id"] in keep_nodes and edge["target_id"] in keep_nodes:
            add_edge(edge)
        elif relation == "enters_via" and edge["source_id"] in keep_nodes and edge["target_id"] in keep_nodes:
            add_edge(edge)
        elif relation in {"exhibits", "activates", "experiences"} and edge["source_id"] in keep_nodes and edge["target_id"] in keep_nodes:
            add_edge(edge)
        elif relation in {"evidenced_by", "measured_in", "leads_to"} and edge["source_id"] in keep_nodes and edge["target_id"] in keep_nodes:
            add_edge(edge)

    subset_entities = [entity for entity in data["entities"] if entity["id"] in keep_nodes]
    subset = {
        "experiment": "focused evidence-first anti-hallucination test",
        "source_graph": "mpkg_output_v2.json",
        "selection_rule": "6 selected Evidence nodes plus only their provenance and local reasoning-chain context",
        "selected_evidence": SELECTED_EVIDENCE,
        "entities": subset_entities,
        "relationships": keep_edges,
    }
    OUT_JSON.write_text(json.dumps(subset, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    graph_nodes = [
        {"id": entity["id"], "label": label_for(entity), "type": entity["type"], "data": entity}
        for entity in subset_entities
    ]
    graph_edges = [
        {
            "id": f"edge_{index}",
            "source": edge["source_id"],
            "target": edge["target_id"],
            "label": edge["relation_type"],
            "data": edge,
            "valid": edge["source_id"] in keep_nodes and edge["target_id"] in keep_nodes,
        }
        for index, edge in enumerate(keep_edges, 1)
    ]
    OUT_GRAPH.write_text(
        json.dumps(
            {
                "directed": True,
                "source_file": OUT_JSON.name,
                "node_count": len(graph_nodes),
                "edge_count": len(graph_edges),
                "nodes": graph_nodes,
                "edges": graph_edges,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    node_counts = Counter(entity["type"] for entity in subset_entities)
    rel_counts = Counter(edge["relation_type"] for edge in keep_edges)
    supported_observations = {
        edge["target_id"]
        for edge in keep_edges
        if edge["relation_type"] == "supports" and edge["source_id"].startswith("evidence_")
    }
    observations = {entity["id"] for entity in subset_entities if entity["type"] == "Observation"}

    summary = [
        "# Focused MPKG Experiment",
        "",
        "This is a separate testing subset. It does not replace or modify the full evidence-aware graph.",
        "",
        "## Purpose",
        "",
        "Use a small set of evidence-backed claims to test extraction/query behavior with less risk of hallucination.",
        "",
        "## Scope",
        "",
        f"- Selected Evidence nodes: {len(SELECTED_EVIDENCE)}",
        f"- Entities in subset: {len(subset_entities)}",
        f"- Relationships in subset: {len(keep_edges)}",
        f"- Evidence-supported observations: {len(supported_observations)} / {len(observations)}",
        "",
        "## Node Counts",
        "",
    ]
    summary.extend(f"- {key}: {value}" for key, value in sorted(node_counts.items()))
    summary.extend(["", "## Relationship Counts", ""])
    summary.extend(f"- {key}: {value}" for key, value in sorted(rel_counts.items()))
    summary.extend(["", "## Selected Evidence", ""])
    summary.extend(f"- `{evidence_id}`" for evidence_id in SELECTED_EVIDENCE)
    summary.extend([
        "",
        "## How To Use",
        "",
        "Use `focused_mpkg_output_test.json` for conservative testing and `focused_mpkg_graph_test.json` for visualization experiments.",
        "Keep the full graph (`../../mpkg_output_v2.json`) as the publication-scale artifact.",
        "",
    ])
    OUT_SUMMARY.write_text("\n".join(summary), encoding="utf-8")

    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"Wrote {OUT_GRAPH.relative_to(ROOT)}")
    print(f"Wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"Entities: {len(subset_entities)}")
    print(f"Relationships: {len(keep_edges)}")
    print(f"Evidence-supported observations: {len(supported_observations)} / {len(observations)}")


if __name__ == "__main__":
    main()
