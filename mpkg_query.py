#!/usr/bin/env python3
"""Evidence-aware query layer for the Microplastics Knowledge Graph (Phase 2-3).

Runs entirely over mpkg_output_v2.json (no database required) and provides:

  * Benchmark scientific queries (Requirement 4):
      Q1  Which polymers are linked to a mechanism (e.g. oxidative stress)?
      Q2  Which tissues/organs are most frequently affected?
      Q3  Which biomarkers support a given mechanism (e.g. inflammation)?
      Q4  What evidence links drinking-water microplastics to human
          cardiovascular outcomes?  (translational gap query)

  * Evidence weighting + confidence scoring for every Association claim.
  * Human-vs-animal evidence ranking based on HostPopulation.

Usage:
    python3 mpkg_query.py                 # run everything
    python3 mpkg_query.py q1 oxidative_stress
    python3 mpkg_query.py weighting
    python3 mpkg_query.py ranking
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict, deque

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mpkg_output_v2.json")

# --- evidence-weighting scales -------------------------------------------------
STRENGTH = {"limited": 1.0, "moderate": 2.0, "strong": 3.0}
LEVEL = {"low": 1.0, "medium": 2.0, "high": 3.0, "unknown": 0.5}
# Human-relevance weight by organism class (human findings rank highest).
ORGANISM_WEIGHT = {
    "human": 3.0,
    "mammal": 2.0,
    "fish": 1.3,
    "invertebrate": 1.0,
    "in_vitro_cell": 0.8,
    "other": 0.5,
}
RELEVANCE = {"high": 3.0, "medium": 2.0, "low": 1.0, "unknown": 0.5}


class Graph:
    def __init__(self, data):
        self.nodes = {e["id"]: e for e in data["entities"]}
        self.edges = data["relationships"]
        self.out = defaultdict(list)   # id -> [(relation, target_id)]
        self.inc = defaultdict(list)   # id -> [(relation, source_id)]
        self.undirected = defaultdict(set)
        for r in self.edges:
            s, t, rt = r["source_id"], r["target_id"], r["relation_type"]
            self.out[s].append((rt, t))
            self.inc[t].append((rt, s))
            self.undirected[s].add(t)
            self.undirected[t].add(s)

    def of_type(self, t):
        return [n for n in self.nodes.values() if n["type"] == t]

    def label(self, nid):
        n = self.nodes.get(nid, {})
        for k in ("name", "label", "title", "pathway_label", "text"):
            if n.get(k):
                return str(n[k])
        return nid

    def path(self, src, dst, max_hops=6):
        """Shortest undirected path of node ids between src and dst, or None."""
        if src == dst:
            return [src]
        seen = {src}
        q = deque([[src]])
        while q:
            p = q.popleft()
            if len(p) > max_hops + 1:
                continue
            for nb in self.undirected[p[-1]]:
                if nb in seen:
                    continue
                np = p + [nb]
                if nb == dst:
                    return np
                seen.add(nb)
                q.append(np)
        return None


def load():
    with open(SRC, "r", encoding="utf-8") as fh:
        return Graph(json.load(fh))


# --- Benchmark queries ---------------------------------------------------------

def q1_polymers_for_mechanism(g: Graph, mechanism_label="oxidative_stress"):
    """Polymers connected to a mechanism through any evidence path."""
    mechs = [m for m in g.of_type("Mechanism") if m.get("label") == mechanism_label]
    results = []
    for poly in g.of_type("Polymer"):
        best = None
        for m in mechs:
            p = g.path(poly["id"], m["id"])
            if p and (best is None or len(p) < len(best)):
                best = p
        if best:
            results.append((g.label(poly["id"]), [g.label(x) for x in best]))
    return results


def q2_affected_tissues(g: Graph):
    counts = defaultdict(int)
    for r in g.edges:
        if r["relation_type"] in ("affects", "measured_in", "relevant_to"):
            tgt = g.nodes.get(r["target_id"])
            if tgt and tgt["type"] == "TissueOrgan":
                counts[g.label(r["target_id"])] += 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def q3_biomarkers_for_mechanism(g: Graph, mechanism_label="inflammation"):
    out = []
    for m in g.of_type("Mechanism"):
        if m.get("label") != mechanism_label:
            continue
        for rt, tgt in g.out[m["id"]]:
            if rt == "evidenced_by" and g.nodes.get(tgt, {}).get("type") == "Biomarker":
                out.append(g.label(tgt))
    return sorted(set(out))


def q4_drinking_water_human_cardiovascular(g: Graph):
    """Translational query: drinking-water MP exposure -> human cardiovascular outcome."""
    cv_terms = ("cardiovascular", "heart", "cardiac")
    dw_terms = ("drinking water", "drinking-water", "tap water")
    human = [h for h in g.of_type("HostPopulation") if h.get("organism_class") == "human"]
    cv_outcomes = [o for o in g.of_type("ClinicalOutcome")
                   if any(t in o.get("label", "").lower() for t in cv_terms)]
    dw_nodes = [n for n in g.nodes.values()
                if any(t in json.dumps(n).lower() for t in dw_terms)]
    chains = []
    for h in human:
        for o in cv_outcomes:
            p = g.path(h["id"], o["id"])
            if p:
                chains.append([g.label(x) for x in p])
    return {
        "human_hosts": [g.label(h["id"]) for h in human],
        "cardiovascular_outcomes_in_graph": [g.label(o["id"]) for o in cv_outcomes],
        "drinking_water_nodes_in_graph": [g.label(n["id"]) for n in dw_nodes],
        "supporting_chains": chains,
        "verdict": ("Insufficient direct human evidence: the graph contains no "
                    "drinking-water reservoir, no cardiovascular outcome, and no "
                    "human exposure->outcome chain for this endpoint."
                    if not chains else "Evidence chain(s) found (see supporting_chains)."),
    }


# --- Evidence weighting & confidence scoring -----------------------------------

def association_weight(g: Graph, assoc):
    strength = STRENGTH.get(assoc.get("evidence_strength"), 0.5)
    consistency = LEVEL.get(assoc.get("consistency_across_studies"), 0.5)
    causal = LEVEL.get(assoc.get("causal_confidence"), 0.5)
    # Host translational bonus: best organism class among supporting studies' hosts.
    host_bonus = 1.0
    for rt, sid in g.inc[assoc["id"]]:
        if rt == "supported_by":
            continue
    # supporting studies -> hosts they investigate
    studies = [s for rt, s in g.out[assoc["id"]] if rt == "supported_by"]
    studies += [s for rt, s in g.inc[assoc["id"]] if rt == "supports"]
    org_best = 0.0
    for st in studies:
        for rt, tgt in g.out[st]:
            if rt == "investigates" and g.nodes.get(tgt, {}).get("type") == "HostPopulation":
                org_best = max(org_best, ORGANISM_WEIGHT.get(
                    g.nodes[tgt].get("organism_class", "other"), 0.5))
    if org_best:
        host_bonus = org_best
    raw = strength * consistency * causal * host_bonus
    # Normalise to 0..1 against the theoretical max (3*3*3*3 = 81).
    score = round(raw / 81.0, 3)
    if assoc.get("relationship") == "null":
        tier = "null/negative finding"
    elif score >= 0.5:
        tier = "high"
    elif score >= 0.2:
        tier = "moderate"
    else:
        tier = "low"
    return score, tier


def evidence_weighting(g: Graph):
    rows = []
    for a in g.of_type("Association"):
        score, tier = association_weight(g, a)
        rows.append({
            "id": a["id"],
            "claim": a.get("notes", "")[:90],
            "relationship": a.get("relationship"),
            "evidence_strength": a.get("evidence_strength"),
            "causal_confidence": a.get("causal_confidence"),
            "score": score,
            "tier": tier,
        })
    return sorted(rows, key=lambda r: -r["score"])


# --- Human vs animal evidence ranking ------------------------------------------

def human_vs_animal_ranking(g: Graph):
    groups = defaultdict(lambda: {"hosts": [], "biomarkers": set(), "outcomes": set(),
                                  "evidence": 0, "weight": 0.0})
    for h in g.of_type("HostPopulation"):
        oc = h.get("organism_class", "other")
        bucket = "human" if oc == "human" else "animal"
        grp = groups[bucket]
        grp["hosts"].append(g.label(h["id"]))
        w = ORGANISM_WEIGHT.get(oc, 0.5) * RELEVANCE.get(h.get("translational_relevance"), 0.5)
        grp["weight"] += w
        for rt, tgt in g.out[h["id"]]:
            tn = g.nodes.get(tgt, {})
            if rt == "exhibits" and tn.get("type") == "Biomarker":
                grp["biomarkers"].add(g.label(tgt))
            if rt == "experiences" and tn.get("type") == "ClinicalOutcome":
                grp["outcomes"].add(g.label(tgt))
    # count Evidence by organism class of its study's host
    for ev in g.of_type("Evidence"):
        et = ev.get("evidence_type")
        bucket = "human" if et == "human_observational" else "animal"
        groups[bucket]["evidence"] += 1
    out = {}
    for bucket, grp in groups.items():
        out[bucket] = {
            "hosts": grp["hosts"],
            "n_hosts": len(grp["hosts"]),
            "biomarkers": sorted(grp["biomarkers"]),
            "outcomes": sorted(grp["outcomes"]),
            "evidence_nodes": grp["evidence"],
            "aggregate_translational_weight": round(grp["weight"], 2),
        }
    return out


# --- Provenance traces ---------------------------------------------------------

def provenance_traces(g: Graph):
    """Study -> Evidence -> Observation chains for traceability."""
    rows = []
    for ev in g.of_type("Evidence"):
        study = None
        for rt, src in g.inc[ev["id"]]:
            if rt == "provides":
                study = src
                break
        for rt, tgt in g.out[ev["id"]]:
            if rt == "supports":
                obs = g.nodes.get(tgt, {})
                rows.append({
                    "study": g.label(study) if study else ev.get("study_ref", ""),
                    "evidence": ev.get("text", ""),
                    "section": ev.get("section", ""),
                    "confidence": ev.get("confidence", ""),
                    "observation_id": tgt,
                    "observation": obs.get("notes", ""),
                })
    return rows


def export_all(g: Graph):
    """Bundle every analysis into one JSON-serialisable dict for the dashboard."""
    from collections import Counter
    return {
        "summary": {
            "entities": len(g.nodes),
            "relationships": len(g.edges),
            "node_types": dict(Counter(n["type"] for n in g.nodes.values())),
            "rel_types": dict(Counter(r["relation_type"] for r in g.edges)),
        },
        "q1_polymers_oxidative_stress": q1_polymers_for_mechanism(g, "oxidative_stress"),
        "q2_affected_tissues": q2_affected_tissues(g),
        "q3_biomarkers_inflammation": q3_biomarkers_for_mechanism(g, "inflammation"),
        "q4_drinking_water_human_cv": q4_drinking_water_human_cardiovascular(g),
        "evidence_weighting": evidence_weighting(g),
        "human_vs_animal": human_vs_animal_ranking(g),
        "provenance": provenance_traces(g),
    }


# --- CLI -----------------------------------------------------------------------

def _print_header(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def run_all(g: Graph):
    _print_header("Q1  Which polymers are linked to oxidative stress?")
    for poly, path in q1_polymers_for_mechanism(g, "oxidative_stress"):
        print(f"  - {poly}")
        print(f"      path: {' -> '.join(path)}")

    _print_header("Q2  Which tissues/organs are most frequently affected?")
    for tissue, n in q2_affected_tissues(g):
        print(f"  - {tissue}  ({n} link(s))")

    _print_header("Q3  Which biomarkers support inflammation?")
    for b in q3_biomarkers_for_mechanism(g, "inflammation"):
        print(f"  - {b}")

    _print_header("Q4  Drinking-water MPs -> human cardiovascular outcomes?")
    res = q4_drinking_water_human_cardiovascular(g)
    print("  verdict:", res["verdict"])
    print("  human hosts in graph     :", res["human_hosts"])
    print("  CV outcomes in graph     :", res["cardiovascular_outcomes_in_graph"] or "none")
    print("  drinking-water nodes     :", res["drinking_water_nodes_in_graph"] or "none")

    _print_header("Evidence weighting / confidence scoring (per Association)")
    for r in evidence_weighting(g):
        print(f"  [{r['tier']:>20}] score={r['score']:<5} {r['relationship']:<16} {r['claim']}")

    _print_header("Human vs Animal evidence ranking")
    for bucket, info in human_vs_animal_ranking(g).items():
        print(f"  {bucket.upper()}:")
        print(f"    hosts ({info['n_hosts']}): {', '.join(info['hosts'])}")
        print(f"    biomarkers: {', '.join(info['biomarkers']) or 'none'}")
        print(f"    outcomes  : {', '.join(info['outcomes']) or 'none'}")
        print(f"    evidence nodes: {info['evidence_nodes']}")
        print(f"    aggregate translational weight: {info['aggregate_translational_weight']}")


def main(argv):
    g = load()
    if not argv:
        run_all(g)
        return
    cmd = argv[0]
    if cmd == "q1":
        mech = argv[1] if len(argv) > 1 else "oxidative_stress"
        for poly, path in q1_polymers_for_mechanism(g, mech):
            print(poly, "::", " -> ".join(path))
    elif cmd == "q2":
        for tissue, n in q2_affected_tissues(g):
            print(f"{tissue}\t{n}")
    elif cmd == "q3":
        mech = argv[1] if len(argv) > 1 else "inflammation"
        print("\n".join(q3_biomarkers_for_mechanism(g, mech)))
    elif cmd == "q4":
        print(json.dumps(q4_drinking_water_human_cardiovascular(g), indent=2))
    elif cmd == "weighting":
        print(json.dumps(evidence_weighting(g), indent=2))
    elif cmd == "ranking":
        print(json.dumps(human_vs_animal_ranking(g), indent=2))
    elif cmd == "export":
        print(json.dumps(export_all(g), indent=2, ensure_ascii=False))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
