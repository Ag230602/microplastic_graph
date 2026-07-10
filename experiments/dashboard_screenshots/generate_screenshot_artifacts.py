#!/usr/bin/env python3
"""Generate screenshot-style PNG artifacts for manuscript/demo use."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MINIMAL_KG = ROOT / "experiments" / "minimal_evidence_gated" / "minimal_kg.json"
TEN_KG = ROOT / "experiments" / "ten_paper_evidence_gated" / "ten_paper_kg.json"


def try_import_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Pillow is required for PNG generation: {exc}") from exc
    return Image, ImageDraw, ImageFont


def font(size: int, bold: bool = False):
    _, _, ImageFont = try_import_pillow()
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            pass
    return ImageFont.load_default()


def round_rect(draw, box, fill, outline="#c9d2dc", radius=10, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def write_wrapped(draw, xy, text, font_obj, fill="#1f2933", width=78, line_gap=6):
    x, y = xy
    lines = []
    for para in str(text).split("\n"):
        if not para:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=width))
    for line in lines:
        draw.text((x, y), line, font=font_obj, fill=fill)
        bbox = draw.textbbox((x, y), line or " ", font=font_obj)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def make_minimal_provenance():
    Image, ImageDraw, _ = try_import_pillow()
    kg = json.loads(MINIMAL_KG.read_text())
    evidence = next(e for e in kg["entities"] if e["id"] == "evidence_liver_metabolic_oxidative_markers")
    observation = next(e for e in kg["entities"] if e["id"] == "observation_liver_metabolic_oxidative_response")
    outcome = next(e for e in kg["entities"] if e["id"] == "outcome_hepatic_metabolic_alteration")
    rel_eo = next(r for r in kg["relationships"] if r["source_node"] == evidence["id"] and r["target_node"] == observation["id"])
    rel_oo = next(r for r in kg["relationships"] if r["source_node"] == observation["id"] and r["target_node"] == outcome["id"])

    img = Image.new("RGB", (1800, 1120), "#f7f5ef")
    draw = ImageDraw.Draw(img)
    title_font = font(42, True)
    h_font = font(27, True)
    body_font = font(22)
    small_font = font(18)
    mono_font = font(18)

    draw.text((64, 42), "Minimal Dashboard: Evidence -> Observation -> Outcome Provenance", font=title_font, fill="#1f2933")
    draw.text((64, 102), "1 source review paper | 16 nodes | 20 relationships | 2/2 evidence-supported observations", font=body_font, fill="#607080")

    cards = [
        ("Evidence", evidence["name"], evidence["example_sentence"], "#fffaf0", "#b38b1e"),
        ("Observation", observation["name"], observation["definition"], "#eef8f4", "#238b6e"),
        ("Outcome", outcome["name"], outcome["definition"], "#fff1f3", "#c3475b"),
    ]
    xs = [64, 642, 1220]
    for x, (label, name, detail, fill, accent) in zip(xs, cards):
        round_rect(draw, (x, 190, x + 516, 720), fill=fill, outline="#c9d2dc", radius=12, width=2)
        draw.rectangle((x, 190, x + 516, 202), fill=accent)
        draw.text((x + 26, 230), label, font=h_font, fill=accent)
        y = write_wrapped(draw, (x + 26, 278), name, h_font, fill="#1f2933", width=28, line_gap=7)
        y += 14
        write_wrapped(draw, (x + 26, y), detail, body_font, fill="#1f2933", width=34, line_gap=7)

    # arrows
    for x1, x2 in [(580, 642), (1158, 1220)]:
        y = 455
        draw.line((x1, y, x2 - 18, y), fill="#2f6f9f", width=5)
        draw.polygon([(x2 - 18, y - 14), (x2 - 18, y + 14), (x2 + 4, y)], fill="#2f6f9f")

    round_rect(draw, (64, 775, 1736, 1030), fill="#ffffff", outline="#c9d2dc", radius=12, width=2)
    draw.text((92, 805), "Relationship Metadata", font=h_font, fill="#1f2933")
    y = 856
    y = write_wrapped(draw, (92, y), f"{rel_eo['source_node']} -> {rel_eo['target_node']}", mono_font, fill="#1f2933", width=120, line_gap=5)
    y = write_wrapped(draw, (92, y + 5), f"relationship: {rel_eo['relationship_name']} | confidence: {rel_eo['confidence']} | strength: {rel_eo['relationship_strength']}", body_font, fill="#607080", width=120)
    y = write_wrapped(draw, (92, y + 18), f"{rel_oo['source_node']} -> {rel_oo['target_node']}", mono_font, fill="#1f2933", width=120, line_gap=5)
    write_wrapped(draw, (92, y + 5), f"relationship: {rel_oo['relationship_name']} | confidence: {rel_oo['confidence']} | strength: {rel_oo['relationship_strength']}", body_font, fill="#607080", width=120)

    out = HERE / "01_minimal_evidence_observation_outcome_provenance.png"
    img.save(out)
    return out


def make_ten_paper_overview():
    Image, ImageDraw, _ = try_import_pillow()
    kg = json.loads(TEN_KG.read_text())
    counts = kg["counts"]
    sources = kg["selected_sources"]

    img = Image.new("RGB", (1800, 1260), "#f6f7f9")
    draw = ImageDraw.Draw(img)
    title_font = font(42, True)
    h_font = font(27, True)
    body_font = font(21)
    small_font = font(17)

    draw.text((64, 42), "10-Paper Evidence-Gated Dashboard Overview", font=title_font, fill="#1f2933")
    draw.text((64, 102), "Scaled prototype with paper testing, KG question answering, and KG-vs-LLM comparison", font=body_font, fill="#607080")

    metrics = [
        ("Papers", counts["papers"]),
        ("Entities", counts["entities"]),
        ("Relationships", counts["relationships"]),
        ("Concepts", counts["concept_nodes"]),
        ("Evidence Nodes", counts["evidence_nodes"]),
        ("Observations", counts["observation_nodes"]),
    ]
    for i, (label, value) in enumerate(metrics):
        col = i % 3
        row = i // 3
        x = 64 + col * 570
        y = 175 + row * 170
        round_rect(draw, (x, y, x + 520, y + 130), fill="#ffffff", outline="#d5dde6", radius=12, width=2)
        draw.text((x + 28, y + 24), str(value), font=font(42, True), fill="#2f6f9f")
        draw.text((x + 28, y + 82), label, font=body_font, fill="#607080")

    round_rect(draw, (64, 545, 1736, 1130), fill="#ffffff", outline="#d5dde6", radius=12, width=2)
    draw.text((92, 575), "Selected 10 Source Papers", font=h_font, fill="#1f2933")
    y = 630
    for i, source in enumerate(sources, 1):
        title = source["title"]
        evidence_type = source["evidence_type"]
        line = f"{i}. {title}"
        y = write_wrapped(draw, (104, y), line, body_font, fill="#1f2933", width=116, line_gap=4)
        draw.text((128, y), f"Evidence type: {evidence_type} | Matched concepts: {', '.join(source['matched_concepts'][:4])}", font=small_font, fill="#607080")
        y += 34

    round_rect(draw, (64, 1160, 1736, 1225), fill="#eef8f4", outline="#b8d9cb", radius=12, width=2)
    draw.text((92, 1182), "Evidence flow: Paper -> Evidence -> Observation -> Concept -> Question Answering -> KG-vs-LLM comparison", font=body_font, fill="#136b55")

    out = HERE / "02_ten_paper_dashboard_overview.png"
    img.save(out)
    return out


def write_explanation():
    text = """# Dashboard Screenshot Package

This folder contains two screenshot-style PNG artifacts generated from the local dashboard data.

## Files

- `01_minimal_evidence_observation_outcome_provenance.png`
  - Shows the 1-paper minimal provenance chain.
  - Chain: `Evidence -> Observation -> Outcome`.
  - Example: `evidence_liver_metabolic_oxidative_markers -> observation_liver_metabolic_oxidative_response -> outcome_hepatic_metabolic_alteration`.
  - Counts: 1 source review paper, 16 nodes, 20 relationships, 2 evidence nodes, 2 observation nodes, 2/2 evidence-supported observations.

- `02_ten_paper_dashboard_overview.png`
  - Shows the scaled 10-paper dashboard summary.
  - Counts: 10 papers, 188 entities, 365 relationships, 18 concept nodes, 80 evidence nodes, 80 observation nodes.
  - Workflow: `Paper -> Evidence -> Observation -> Concept -> Question Answering -> KG-vs-LLM comparison`.

## Explanation

The 1-paper minimal dashboard is best for showing explicit provenance tracing because it keeps the graph small and inspectable. The screenshot highlights how an exact evidence sentence supports a structured observation, and how that observation supports a conservative outcome label with confidence and evidence-strength metadata.

The 10-paper dashboard scales the same evidence-gated idea across a broader source set. It focuses on paper-level evidence, concept matching, question answering, random-paper testing, and comparison between KG-supported answers and external LLM answers.
"""
    (HERE / "README.md").write_text(text)


def main():
    outputs = [make_minimal_provenance(), make_ten_paper_overview()]
    write_explanation()
    for output in outputs:
        print(output.relative_to(ROOT))


if __name__ == "__main__":
    main()