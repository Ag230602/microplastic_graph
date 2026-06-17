#!/usr/bin/env python3
"""Create self-contained (standalone) HTML graphs by inlining their JSON data.

Each viewer normally does: fetch('something.json').then(r=>r.json()).then(init)
We replace that with the data embedded directly, so the file opens with no server.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

PAGES = [
    ("mpkg_graph.html", "mpkg_graph.json", "mpkg_graph_standalone.html"),
    ("mpkg_graph_v2.html", "mpkg_graph_v2.json", "mpkg_graph_v2_standalone.html"),
    ("mpkg_critique_graph.html", "mpkg_critique_graph.json", "mpkg_critique_graph_standalone.html"),
]


def build(html_name, json_name, out_name):
    with open(os.path.join(HERE, html_name), "r", encoding="utf-8") as fh:
        html = fh.read()
    with open(os.path.join(HERE, json_name), "r", encoding="utf-8") as fh:
        data = json.load(fh)

    embedded = json.dumps(data)
    # Replace the fetch(...).then(init).catch(...); chain with a direct call using inlined data.
    pattern = re.compile(
        r"fetch\(\s*'" + re.escape(json_name) + r"'\s*\)\.then\(.*?\.then\(init\)\.catch\(.*?\}\);",
        re.DOTALL,
    )
    replacement = (
        "const __GRAPH_DATA__ = " + embedded + ";\n"
        "    Promise.resolve(__GRAPH_DATA__).then(init).catch((error) => {\n"
        "      details.innerHTML = '<h2>Could not load graph</h2><pre>' + escapeHtml(error) + '</pre>';\n"
        "    });"
    )
    new_html, n = pattern.subn(lambda _m: replacement, html)
    if n != 1:
        raise SystemExit(f"FAILED to inline {html_name}: matched {n} times (expected 1)")

    with open(os.path.join(HERE, out_name), "w", encoding="utf-8") as fh:
        fh.write(new_html)
    print(f"Wrote {out_name} ({len(new_html)} bytes, data inlined)")


def main():
    for html_name, json_name, out_name in PAGES:
        build(html_name, json_name, out_name)


if __name__ == "__main__":
    main()
