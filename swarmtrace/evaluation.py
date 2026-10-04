"""
STEP A — evaluate the tool against expert ground truth.

ground_truth.json lists incidents that the collusion.wiki write-up documented BY
HAND, each with the section that documents it. For each item two programmatic
checks run against the tool's own outputs:
  automatic : surfaced by the generic extractor with no hand-coded keys
              (answer-value slots, URL hosts, contested slots);
  pattern   : surfaced only through a hand-written technique regex in core.TECH.
RECALL is reported both ways (automatic-only is the honest headline).
PRECISION on contested slots = named slots / all flagged slots.
Everything here is reproducible: `python -m swarmtrace` writes outputs/evaluation.json.
"""
from __future__ import annotations
import json, re, pathlib

def _answer_claims(claims, pairs, min_labels):
    found = {}
    for slot, value in pairs:
        hits = [c for c in claims if c["kind"] == "answer_value" and c["slot"] == slot and c["value"] == value
                and (c.get("n_agents") or 0) >= min_labels]
        found[f"{slot} {value}"] = max((c["n_agents"] for c in hits), default=0)
    return all(v >= min_labels for v in found.values()), found

def _cascade_values(cascades, pairs, task=None):
    found = {}
    for slot, values in pairs.items():
        cs = [c for c in cascades if c["slot"] == slot and (task is None or c.get("task") == task)]
        present = {v["value"] for c in cs for v in c["values"]}
        found[slot] = sorted(set(values) & present)
    return all(len(found[s]) == len(pairs[s]) for s in pairs), found

def _url_hosts(claims, regex):
    rx = re.compile(regex)
    hosts = [(c["value"], c["n_agents"]) for c in claims if c["kind"] == "url" and rx.search(c["value"])]
    return bool(hosts), {"hosts": len(hosts), "labels_total": sum(n for _, n in hosts), "examples": [h for h, _ in hosts[:4]]}

def _technique(claims, name):
    hits = [c for c in claims if c["kind"] == "technique" and c["value"] == name]
    return bool(hits), {"labels": hits[0]["n_agents"] if hits else 0, "posts": hits[0]["n_posts"] if hits else 0}

def _run_check(spec, claims, cascades):
    t = spec.get("type", "none")
    if t == "none": return False, {"note": spec.get("note", "no automatic mechanism in the tool")}
    if t == "answer_claims": return _answer_claims(claims, spec["pairs"], spec.get("min_labels", 2))
    if t == "cascade_values": return _cascade_values(cascades, spec["pairs"], spec.get("task"))
    if t == "url_hosts": return _url_hosts(claims, spec["regex"])
    if t == "technique": return _technique(claims, spec["name"])
    raise ValueError(t)

def run(claims, cascades, metrics, gt_path="ground_truth.json"):
    gt = json.load(open(gt_path, encoding="utf-8"))
    items = []
    for it in gt["items"]:
        auto_ok, auto_ev = _run_check(it["automatic_check"], claims, cascades)
        pat_ok, pat_ev = (_run_check(it["pattern_check"], claims, cascades) if it.get("pattern_check") else (False, None))
        items.append({"id": it["id"], "incident": it["incident"],
                      "collusion_wiki_section": it["collusion_wiki_section"], "collusion_wiki_url": it["collusion_wiki_url"],
                      "quote": it["quote"],
                      "surfaced_automatically": auto_ok, "automatic_evidence": auto_ev,
                      "surfaced_by_hand_written_pattern": pat_ok, "pattern_evidence": pat_ev,
                      "note": it.get("note", "")})
    n = len(items); auto = sum(1 for i in items if i["surfaced_automatically"])
    either = sum(1 for i in items if i["surfaced_automatically"] or i["surfaced_by_hand_written_pattern"])
    s = metrics["slots"]
    return {
        "ground_truth_source": gt["source"], "ground_truth_items": n,
        "recall_automatic": {"found": auto, "total": n, "value": round(auto / n, 3)},
        "recall_with_hand_written_patterns": {"found": either, "total": n, "value": round(either / n, 3)},
        "precision_contested_slots": {"named": s["named_slots"], "flagged": s["flagged"], "value": round(s["named_slots"] / s["flagged"], 3),
                                      "artifact_slots": s["artifact_slots"]},
        "definitions": {
            "automatic": "surfaced by the generic extractor (answer-value slots, URL hosts, contested slots) with no hand-coded keys",
            "pattern": "surfaced only through a hand-written technique regex in swarmtrace/core.py TECH",
            "precision": "named contested slots / all flagged contested slots (regex-artifact slots count against precision)",
        },
        "items": items,
    }

def render_md(ev):
    L = ["# Evaluation against expert ground truth", "",
         f"Ground truth: incidents documented by hand in the [collusion.wiki]({ev['ground_truth_source']}) write-up "
         f"({ev['ground_truth_items']} items, each cited below). Produced by `python -m swarmtrace` into `outputs/evaluation.json`; "
         "asserted by the gate.", "",
         f"- **Recall, automatic (no hand-coded keys): {ev['recall_automatic']['found']}/{ev['recall_automatic']['total']} = {ev['recall_automatic']['value']}**",
         f"- Recall including hand-written technique patterns: {ev['recall_with_hand_written_patterns']['found']}/{ev['recall_with_hand_written_patterns']['total']} = {ev['recall_with_hand_written_patterns']['value']}",
         f"- **Precision on contested slots: {ev['precision_contested_slots']['named']}/{ev['precision_contested_slots']['flagged']} = {ev['precision_contested_slots']['value']}** "
         f"(artifact slots counted against precision: {', '.join('`'+a+'`' for a in ev['precision_contested_slots']['artifact_slots']) or 'none'})", "",
         "| # | incident | automatic | pattern | collusion.wiki section |", "|---|---|---|---|---|"]
    for k, it in enumerate(ev["items"], 1):
        L.append(f"| {k} | {it['incident']} | {'yes' if it['surfaced_automatically'] else 'no'} | "
                 f"{'yes' if it['surfaced_by_hand_written_pattern'] else ('—' if it['pattern_evidence'] is None else 'no')} | "
                 f"[{it['collusion_wiki_section']}]({it['collusion_wiki_url']}) |")
    L.append("")
    for k, it in enumerate(ev["items"], 1):
        L.append(f"**{k}. {it['incident']}** — quote: \"{it['quote']}\"  ")
        L.append(f"automatic evidence: `{json.dumps(it['automatic_evidence'])}`" + (f"; pattern evidence: `{json.dumps(it['pattern_evidence'])}`" if it['pattern_evidence'] is not None else ""))
        if it["note"]: L.append(f"note: {it['note']}")
        L.append("")
    L.append("Definitions: " + "; ".join(f"**{k}** = {v}" for k, v in ev["definitions"].items()) + ".")
    return "\n".join(L) + "\n"
