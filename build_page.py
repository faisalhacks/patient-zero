#!/usr/bin/env python3
"""Rebuild outputs/page_data.json from the latest outputs and embed it into
patient_zero.html (the page is self-contained: one HTML file, no external JS).

  python build_page.py            # regenerate page_data.json, embed, write patient_zero.html (+ outputs/ copy)
  python build_page.py --check    # exit 1 if the page does not embed the current data or loads external scripts

Selection rule for the interactive slots: the 8 NAMED contested slots (regex
artifacts such as "Expected" are excluded, see metrics.json slots) with the most
total adopters. Every number on the page comes from claims/cascades/metrics.
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "outputs"
PAGE = ROOT / "patient_zero.html"
N_SLOTS = 8
SLOT_LABELS = {  # hand-written context for the slot name; everything else is computed
    "Slovak": "OECD, % (R4)", "Hungary": "OECD, % (R2)", "Poland": "OECD, % (R3)", "Czech": "OECD, % (R1)",
    "Slovenia": "OECD, % (R5)",
    "Business": "DataUSA cashiers, degrees", "Visual": "DataUSA cashiers, degrees (Visual & Performing Arts)",
    "Psychology": "DataUSA cashiers, degrees", "Social": "DataUSA cashiers, degrees (Social Sciences)",
    "Education": "DataUSA cashiers, degrees",
}

def _jsonl(p):
    with open(p, encoding="utf-8") as f: return [json.loads(l) for l in f if l.strip()]

def build_page_data():
    claims = _jsonl(OUT / "claims.jsonl"); cascades = _jsonl(OUT / "cascades.jsonl")
    metrics = json.load(open(OUT / "metrics.json", encoding="utf-8"))
    artifacts = set(metrics["slots"]["artifact_slots"])
    by_val = {(c["task"], c["slot"], c["value"]): c for c in claims if c["kind"] == "answer_value"}
    named = [c for c in cascades if f"{c['task']}/{c['slot']}" not in artifacts]
    named.sort(key=lambda c: -sum(v["n_agents"] for v in c["values"]))
    slots = []
    for c in named[:N_SLOTS]:
        vals = []
        for v in c["values"]:
            cl = by_val[(c["task"], c["slot"], v["value"])]
            vals.append({"value": v["value"], "n_agents": v["n_agents"], "n_ip16": v["n_ip16"], "patient_zero": v["patient_zero"],
                         "first_seen": v["first_seen"], "adoption": cl["adoption"]})
        hand = metrics["correction_lag"].get(c["slot"]) if c["task"] == "oecd-equity" else None
        slots.append({"task": c["task"], "slot": c["slot"], "label": f"{c['task']} · {SLOT_LABELS.get(c['slot'], c['slot'])}",
                      "false_consensus": c["false_consensus"], "values": vals,
                      "correct_value": hand["correct"] if hand else None,
                      "correct_source": "hand-checked against collusion.wiki" if hand else None})
    f = metrics["featured_case"]; w, t = f["wrong"], f["truth"]
    featured = {
        "title": "Grocery task, Round 5: a wrong relay that spread before the truth landed",
        "wrong": {"label": w["label"], "adoption": w["adoption"]},
        "truth": {"label": t["label"], "at": t["at"]},
        "stats": {"labels": w["distinct_labels"], "posts": w["posts"], "first": w["first"], "last": w["last"],
                  "span_seconds": w["span_seconds"], "truth_seconds_after_last_relay": t["seconds_after_last_wrong_relay"],
                  "wrong_relays_after_truth": t["wrong_relays_after_truth"]},
        "note": (f"{w['distinct_labels']} distinct labels relayed the seed-cracked prediction \"Maryland = 52,395\" in "
                 f"{w['posts']} posts between {w['first'].replace('T', ' ').replace('Z', ' UTC')} and "
                 f"{w['last'].replace('T', ' ').replace('Z', ' UTC')}. The real answer, Montana = 8553, was posted by a "
                 f"scout that had raced ahead at {t['at'][0].replace('T', ' ').replace('Z', ' UTC')}, "
                 f"{t['seconds_after_last_wrong_relay'] // 60} min {t['seconds_after_last_wrong_relay'] % 60} s after the last relay; "
                 f"{t['wrong_relays_after_truth']} relays of the guess followed it. Both facts cross-checked against collusion.wiki."),
    }
    cl = metrics["correction_lag"]; hc = metrics["hidden_channel"]; rs = metrics["risk_score"]; rl = metrics["relay_scouts"]
    findings = {
        "correction_lag": {k: {"wrong": v["wrong"], "correct": v["correct"], "after": v["new_wrong_adopters_after_correction"],
                               "seconds": v["seconds_from_correction_to_last_wrong_adoption"]} for k, v in cl.items()},
        "hidden_channel": {"verdict": hc["verdict"], "unexplained": hc["unexplained_candidates"],
                           "a_tested": hc["test_A_page_name_before_creation"]["tested"],
                           "b_fastest": hc["test_B_token_simultaneity"]["fastest_gap_seconds"],
                           "b_fastest_unread": hc["test_B_token_simultaneity"]["fastest_gap_seconds_where_second_label_never_touched_origin_page"],
                           "c_pages": hc["test_C_new_page_discovery_latency"]["pages_created"],
                           "c_min": hc["test_C_new_page_discovery_latency"]["latency_seconds"]["min"]},
        "risk": {"scored": rs["values_scored"], "zero_sources": rs["values_with_zero_cited_sources"],
                 "adopters": rs["adopters_of_values_with_zero_cited_sources"], "top": rs["top"][:5]},
        "relay": {"scout_posts": rl["scout_posts_total"], "labels": rl["labels_posting_scout_phrases"],
                  "claims": rl["claims_with_scout_patient_zero"],
                  "relayed": rl["claims_relayed_by_at_least_2_other_labels"], "downstream": rl["downstream_adoptions_total"],
                  "top": [{k: v for k, v in r.items() if k != "scout_phrases"} for r in rl["top"][:5]]},
        "identity": metrics["identity_structure"],
    }
    meta = {"events": metrics["events"], "claims": len(claims),
            "contested_slots": len(cascades), "named_slots": metrics["slots"]["named_slots"],
            "source": "collusion.wiki redacted export (DSEWiki, 24 May–2 Jul 2026)",
            "window": "2026-05-24 .. 2026-07-02"}
    return {"slots": slots, "featured": featured, "findings": findings, "meta": meta}

DATA_RX = re.compile(r"const DATA = (\{.*?\});\n", re.S)

def embed(html, data):
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    new, n = DATA_RX.subn(lambda m: "const DATA = " + blob + ";\n", html, count=1)
    assert n == 1, "could not find the DATA literal in patient_zero.html"
    return new

def check():
    html = PAGE.read_text(encoding="utf-8")
    ext = re.findall(r'<script[^>]+src="(https?://[^"]+)"', html)
    data = build_page_data()
    m = DATA_RX.search(html)
    ok = bool(m) and json.loads(m.group(1)) == data and not ext
    print("external scripts:", ext or "none"); print("embeds current page data:", bool(m) and json.loads(m.group(1)) == data)
    return ok

def main():
    if "--check" in sys.argv:
        sys.exit(0 if check() else 1)
    data = build_page_data()
    with open(OUT / "page_data.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False); f.write("\n")
    html = embed(PAGE.read_text(encoding="utf-8"), data)
    PAGE.write_text(html, encoding="utf-8", newline="\n")
    (OUT / "patient_zero.html").write_text(html, encoding="utf-8", newline="\n")
    print(f"page_data.json: {len(data['slots'])} slots; patient_zero.html rebuilt ({len(html):,} bytes)")

if __name__ == "__main__":
    main()
