#!/usr/bin/env python3
"""Build a node/edge graph from mpkg_critique_v1.json for visual inspection."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mpkg_critique_v1.json")
OUT = os.path.join(HERE, "mpkg_critique_graph.json")

CATEGORIES = [
    "critical_errors",
    "unsupported_entities",
    "missing_entities",
    "unsupported_relationships",
    "missing_relationships",
    "ontology_violations",
    "observation_association_errors",
    "quantitative_errors",
    "study_structure_errors",
    "recommendations",
]


def short(text, n=70):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "\u2026"


def finding_label(item):
    if isinstance(item, str):
        return short(item)
    for key in ("issue", "type", "relation", "id", "note"):
        if key in item and item[key]:
            return short(item[key])
    return short(json.dumps(item))


def main():
    with open(SRC, "r", encoding="utf-8") as fh:
        crit = json.load(fh)

    nodes = []
    edges = []
    edge_n = 0

    root_id = "critique_root"
    nodes.append({
        "id": root_id,
        "label": "MPKG Critique",
        "type": "Critique",
        "data": {
            "id": root_id,
            "type": "Critique",
            "audit_target": crit.get("audit_target"),
            "source_paper": crit.get("source_paper"),
            "graph_summary": crit.get("graph_summary"),
        },
    })

    for cat in CATEGORIES:
        items = crit.get(cat, []) or []
        cat_id = f"cat_{cat}"
        nodes.append({
            "id": cat_id,
            "label": f"{cat} ({len(items)})",
            "type": "Category",
            "data": {"id": cat_id, "type": "Category", "name": cat, "count": len(items)},
        })
        edge_n += 1
        edges.append({
            "id": f"edge_{edge_n}",
            "source": root_id,
            "target": cat_id,
            "label": "has_category",
            "data": {"source_id": root_id, "relation_type": "has_category", "target_id": cat_id},
            "valid": True,
        })

        for i, item in enumerate(items, 1):
            fid = f"{cat}_{i}"
            nodes.append({
                "id": fid,
                "label": finding_label(item),
                "type": "Finding" if cat != "recommendations" else "Recommendation",
                "data": {
                    "id": fid,
                    "type": "Finding" if cat != "recommendations" else "Recommendation",
                    "category": cat,
                    "detail": item if isinstance(item, dict) else {"text": item},
                },
            })
            edge_n += 1
            edges.append({
                "id": f"edge_{edge_n}",
                "source": cat_id,
                "target": fid,
                "label": "contains",
                "data": {"source_id": cat_id, "relation_type": "contains", "target_id": fid},
                "valid": True,
            })

    graph = {
        "directed": True,
        "source_file": "mpkg_critique_v1.json",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=2, ensure_ascii=False)

    print(f"Wrote {OUT}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    main()
