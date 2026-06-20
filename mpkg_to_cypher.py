#!/usr/bin/env python3
"""Export mpkg_output_v2.json to a Neo4j-loadable Cypher script.

Turns the JSON knowledge graph into a queryable property graph:
  * each entity becomes a node labelled by its `type`
  * each relationship becomes a typed edge (relation_type, upper-cased)
  * scalar entity fields become node properties; list/dict fields are
    JSON-stringified so they round-trip safely.

Run:
    python3 mpkg_to_cypher.py
    # then in Neo4j:  :source mpkg_graph_v2.cypher   (or cypher-shell -f ...)
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mpkg_output_v2.json")
OUT = os.path.join(HERE, "mpkg_graph_v2.cypher")


def cypher_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (list, dict)):
        v = json.dumps(v, ensure_ascii=False)
    return "'" + str(v).replace("\\", "\\\\").replace("'", "\\'") + "'"


def rel_type(name):
    return name.upper().replace("-", "_").replace(" ", "_")


def main():
    with open(SRC, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    lines = [
        "// Microplastics Knowledge Graph (v2) - Neo4j load script",
        "// Generated from mpkg_output_v2.json by mpkg_to_cypher.py",
        "",
        "// Clean slate (comment out to append instead):",
        "MATCH (n:MPKG) DETACH DELETE n;",
        "",
        "// Uniqueness constraint on node id:",
        "CREATE CONSTRAINT mpkg_id IF NOT EXISTS FOR (n:MPKG) REQUIRE n.id IS UNIQUE;",
        "",
        "// --- Nodes ---",
    ]

    for e in data["entities"]:
        props = {k: v for k, v in e.items() if k != "type"}
        prop_str = ", ".join(f"{k}: {cypher_value(v)}" for k, v in props.items())
        lines.append(f"CREATE (:MPKG:{e['type']} {{{prop_str}}});")

    lines.append("")
    lines.append("// --- Relationships ---")
    for r in data["relationships"]:
        lines.append(
            f"MATCH (a:MPKG {{id: {cypher_value(r['source_id'])}}}), "
            f"(b:MPKG {{id: {cypher_value(r['target_id'])}}}) "
            f"CREATE (a)-[:{rel_type(r['relation_type'])}]->(b);"
        )

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"Wrote {OUT}: {len(data['entities'])} nodes, {len(data['relationships'])} relationships")


if __name__ == "__main__":
    main()
