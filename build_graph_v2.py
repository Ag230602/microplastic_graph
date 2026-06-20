#!/usr/bin/env python3
"""Build a node/edge graph from mpkg_output_v2.json for the viewer."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mpkg_output_v2.json")
OUT = os.path.join(HERE, "mpkg_graph_v2.json")


def label_for(ent):
    for key in ("title", "name", "label", "pathway_label", "method_class", "metric_type", "text", "relationship"):
        if ent.get(key):
            val = str(ent[key])
            return (val[:60] + "\u2026") if len(val) > 63 else val
    return ent["id"]


def main():
    with open(SRC, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    entities = data["entities"]
    rels = data["relationships"]
    ids = {e["id"] for e in entities}

    nodes = [{
        "id": e["id"],
        "label": label_for(e),
        "type": e["type"],
        "data": e,
    } for e in entities]

    edges = []
    for i, r in enumerate(rels, 1):
        valid = r["source_id"] in ids and r["target_id"] in ids
        edges.append({
            "id": f"edge_{i}",
            "source": r["source_id"],
            "target": r["target_id"],
            "label": r["relation_type"],
            "data": r,
            "valid": valid,
        })

    graph = {
        "directed": True,
        "source_file": "mpkg_output_v2.json",
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
