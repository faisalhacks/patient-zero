"""
Analyses layered on the locked outputs (claims.jsonl / cascades.jsonl) and the
raw export. Every number written to outputs/metrics.json is produced here, from
the public data, by `python -m swarmtrace`. Nothing in this module decides which
answer is correct; correctness is hand-checked and cited in FINDINGS.md.

Conventions (PRIME DIRECTIVE):
  * counts are exact integers; durations are exact seconds (hours only as a
    derived, rounded convenience next to the seconds);
  * "label" means the self-assigned agent name in the export. Labels are NOT a
    head count, and the redacted ip16 prefix is NOT an identity either (one
    label is seen from up to 114 prefixes). Both facts are measured below;
  * anything that could not be explained from the data is returned as a
    CANDIDATE with the innocent explanations that were checked; an empty
    candidate list is a NEGATIVE RESULT, which is a valid result.
"""
from __future__ import annotations
import json, re, collections, pathlib, statistics
from datetime import datetime

ISO = "%Y-%m-%dT%H:%M:%SZ"
def _t(s): return datetime.strptime(s, ISO)
def _sec(a, b): return int((_t(b) - _t(a)).total_seconds())
def _lab(x): return x or "(anon)"

# ---------- loaders --------------------------------------------------------------
def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

def load_export(datadir="data"):
    d = pathlib.Path(datadir)
    rev = load_jsonl(d / "revisions.jsonl")
    pages = {p["page_key"]: p for p in load_jsonl(d / "pages.jsonl")}
    ev_types = collections.Counter(e["event_type"] for e in load_jsonl(d / "events.jsonl"))
    return rev, pages, dict(ev_types)

# ---------- identity structure (labels vs ip16) ------------------------------------
def identity_structure(revisions):
    lab_ip = collections.defaultdict(set); ip_lab = collections.defaultdict(set)
    for r in revisions:
        lab_ip[_lab(r["label"])].add(r["ip16"]); ip_lab[r["ip16"]].add(_lab(r["label"]))
    return {"labels": len(lab_ip), "ip16_prefixes": len(ip_lab),
            "max_ip16_per_label": max(len(v) for v in lab_ip.values()),
            "max_labels_per_ip16": max(len(v) for v in ip_lab.values()),
            "labels_seen_from_one_ip16_only": sum(1 for v in lab_ip.values() if len(v) == 1),
            "note": "neither the self-assigned label nor the redacted ip16 prefix identifies an agent; "
                    "'n_agents' everywhere in this repo means 'distinct labels'."}, lab_ip

# ---------- T1-hidden-channel: see hidden_channel.py ---------------------------------------
from . import hidden_channel as _hc
from . import risk as _risk
from . import relay as _relay
from . import evaluation as _eval

# ---------- correction lag (kept green) ------------------------------------------------
OECD_TASK = "oecd-equity"
PAIRS = [("Hungary", "9.90", "9.91"), ("Poland", "16.40", "16.38"), ("Slovak", "14.60", "14.59"), ("Czech", "9.70", "9.69")]
def correction_lag(claims):
    """Wrong-value adoptions AFTER the correct value's first public post. Which value is
    'correct' is the hand-checked collusion.wiki verdict, not an engine output."""
    get = {(c["task"], c["slot"], c["value"]): c for c in claims if c["kind"] == "answer_value"}
    out = {}
    for slot, wrong, right in PAIRS:
        w, r = get[(OECD_TASK, slot, wrong)], get[(OECD_TASK, slot, right)]
        tc = r["first_seen"]
        after = [a for a in w["adoption"] if _t(a[0]) > _t(tc)]
        after_ip16 = [x for x in w["ip16_first_seen"] if _t(x[0]) > _t(tc)]
        last = max(a[0] for a in w["adoption"])
        out[slot] = {"task": OECD_TASK, "correct": right, "wrong": wrong, "correction_first_posted": tc, "correction_posted_by": r["patient_zero"],
                     "wrong_first_posted": w["first_seen"], "wrong_posted_by": w["patient_zero"],
                     "head_start_of_wrong_over_correct_seconds": _sec(w["first_seen"], tc),
                     "wrong_adopters_total": w["n_agents"], "wrong_adopters_ip16_total": w["n_ip16"],
                     "new_wrong_adopters_after_correction": len(after),
                     "new_wrong_ip16_after_correction": len(after_ip16),
                     "last_wrong_adoption": last, "seconds_from_correction_to_last_wrong_adoption": _sec(tc, last),
                     "hours": round(_sec(tc, last) / 3600, 2),
                     "correct_adopters_total": r["n_agents"], "correct_adopters_ip16_total": r["n_ip16"]}
    return out

# ---------- STEP D: page locality of the correction ------------------------------------------
def page_locality(claims, events, revisions, lag):
    """For each late wrong adopter (first posted the wrong value AFTER the correct value was
    first public), did the page they edited ALREADY display the correct value before their
    edit? Checked on the page body of the previous published revision of that page, with the
    pipeline's own extractor (answer_pairs). Also: had the correct value been POSTED on that
    page by anyone earlier, and how many pages carried each value at all."""
    from .core import answer_pairs, task_index, task_of
    idx = task_index(events)
    revs = {r["rev_id"]: r for r in revisions}
    by_page = collections.defaultdict(list)
    for r in revisions: by_page[r["page_key"]].append(r)
    for v in by_page.values(): v.sort(key=lambda r: (r["seq"], r["time"]))
    ev_by_key = collections.defaultdict(list)
    for e in events: ev_by_key[(e["time"], e["agent"], e["where"])].append(e)
    out = {}
    for slot, L in lag.items():
        task, wrong, right, tc = L["task"], L["wrong"], L["correct"], L["correction_first_posted"]
        wc = next(c for c in claims if c["kind"] == "answer_value" and (c["task"], c["slot"], c["value"]) == (task, slot, wrong))
        rc = next(c for c in claims if c["kind"] == "answer_value" and (c["task"], c["slot"], c["value"]) == (task, slot, right))
        pages_wrong, pages_right = set(wc["pages"]), set(rc["pages"])
        late = [a for a in wc["adoption"] if _t(a[0]) > _t(tc)]
        rows = []
        for a in late:
            cands = [e for e in ev_by_key[(a[0], a[1], a[2])] if (slot, wrong) in answer_pairs(e["text"])]
            e = cands[0] if cands else None
            if e is None: continue
            r = revs[e["source_rev"]]
            prev = [x for x in by_page[r["page_key"]] if x["seq"] < r["seq"]]
            prev = prev[-1] if prev else None
            showed = bool(prev) and (slot, right) in answer_pairs(prev["body"])
            posted_earlier = any((slot, right) in answer_pairs(x["body"]) for x in by_page[r["page_key"]] if x["seq"] < r["seq"])
            rows.append({"label": a[1], "ip16": a[3] if len(a) > 3 else None, "time": a[0], "page": a[2],
                         "page_showed_correct_before_edit": showed,
                         "correct_ever_on_page_before_edit": posted_earlier,
                         "page_ever_carried_correct": a[2] in pages_right})
        out[slot] = {
            "late_wrong_adopters": len(late), "late_wrong_adopters_checked": len(rows),
            "late_adopters_whose_page_already_showed_correct": sum(1 for x in rows if x["page_showed_correct_before_edit"]),
            "late_adopters_whose_page_had_correct_posted_earlier": sum(1 for x in rows if x["correct_ever_on_page_before_edit"]),
            "late_adopters_on_pages_that_ever_carried_correct": sum(1 for x in rows if x["page_ever_carried_correct"]),
            "pages_with_wrong": len(pages_wrong), "pages_with_correct": len(pages_right),
            "pages_with_both": len(pages_wrong & pages_right),
            "late_adoptions": rows,
        }
    return out

# ---------- featured case (Maryland -> Montana), reproducible --------------------------
MD_RX = re.compile(r"Maryland[^.\n]{0,60}?\b52,?395\b|\b52,?395\b[^.\n]{0,60}?Maryland")
MT_RX = re.compile(r"Montana[^.\n]{0,60}?\b8,?553\b|\b8,?553\b[^.\n]{0,60}?Montana")
def featured_case(events):
    def census(rx):
        posts = sorted((e for e in events if rx.search(e["text"])), key=lambda e: (e["time"], e["source_rev"]))
        first = {}
        for e in posts: first.setdefault(e["agent"], [e["time"], e["agent"], e["where"], e.get("ip16")])
        ip16 = {e.get("ip16") for e in posts} - {None}
        return posts, sorted(first.values()), len(ip16)
    mp, mf, mi = census(MD_RX); tp, tf, ti = census(MT_RX)
    truth = tf[0]
    return {"wrong": {"label": "predicted Maryland = 52,395 (from a cracked-seed guess)", "regex": MD_RX.pattern,
                      "posts": len(mp), "distinct_labels": len(mf), "distinct_ip16": mi, "first": mf[0][0], "last": mf[-1][0],
                      "span_seconds": _sec(mf[0][0], mf[-1][0]), "adoption": mf},
            "truth": {"label": "actual answer Montana = 8553 (seen live by a scout)", "regex": MT_RX.pattern,
                      "posts": len(tp), "distinct_labels": len(tf), "distinct_ip16": ti, "at": truth,
                      "seconds_after_last_wrong_relay": _sec(mf[-1][0], truth[0]),
                      "wrong_relays_after_truth": sum(1 for e in mp if _t(e["time"]) > _t(truth[0]))}}

# ---------- negative result: near-simultaneous identical answers, reproducible ---------------
def simultaneous_answers(claims, events):
    """Fastest gap between two posts of the same answer value by different labels on
    different pages. Answer values are publicly computable, so a tiny gap is explained by
    independent lookup of the same public figure; this is a NEGATIVE result for a hidden channel."""
    from .core import answer_pairs, task_index, task_of
    idx = task_index(events)
    seen = collections.defaultdict(list)
    for e in events:
        for k, v in answer_pairs(e["text"]):
            seen[(task_of(e, k, v, idx), k, v)].append((e["time"], e["agent"], e["where"]))
    best = None; best_key = None
    for key, posts in sorted(seen.items(), key=lambda kv: (kv[0][0] or "", kv[0][1], kv[0][2])):
        posts.sort()
        for a, b in zip(posts, posts[1:]):
            if a[1] != b[1] and a[2] != b[2]:
                g = _sec(a[0], b[0]); k = (g, a[0], key[0] or "", key[1], key[2], a[1], b[1])
                if best is None or k < best_key:
                    best_key = k
                    best = {"gap_seconds": g, "task": key[0], "slot": key[1], "value": key[2],
                            "first": {"time": a[0], "label": a[1], "page": a[2]},
                            "second": {"time": b[0], "label": b[1], "page": b[2]}}
    return best

# ---------- slot hygiene: which of the 42 flagged slots are named answer slots ----------
# STEP E moved the generic status/format tokens into core.STOP; what remains here are slot words that
# are real but ambiguous: a truncated multi-word name that merges two questions ("United" = United
# Kingdom 38.3 and United States 24.2 on the OECD task). Listed, not hidden; counted against precision.
GENERIC_SLOT_WORDS = {"United"}
def slot_classification(cascades):
    generic = sorted(f"{c['task']}/{c['slot']}" for c in cascades if c["slot"] in GENERIC_SLOT_WORDS)
    named = sorted(f"{c['task']}/{c['slot']}" for c in cascades if c["slot"] not in GENERIC_SLOT_WORDS)
    return {"flagged": len(cascades), "named_slots": len(named), "generic_word_artifacts": len(generic),
            "artifact_slots": generic, "named_slot_list": named,
            "note": "the extractor keys a slot by (task, capitalised word before a number); generic status/format "
                    "tokens are stopped in core.STOP (STEP E); the artifacts listed here are truncated multi-word "
                    "names that merge two questions, listed rather than hidden so the headline count stays honest"}

# ---------- writer --------------------------------------------------------------------------
def run_all(datadir="data", outdir="outputs"):
    from .core import events_from_wiki
    rev, pages, ev_types = load_export(datadir)
    events = list(events_from_wiki(str(pathlib.Path(datadir) / "revisions.jsonl")))
    claims = load_jsonl(pathlib.Path(outdir) / "claims.jsonl")
    cascades = load_jsonl(pathlib.Path(outdir) / "cascades.jsonl")
    ident, lab_ip = identity_structure(rev)
    m = {
        "source": "collusion.wiki redacted export", "reproduce": "python download_data.py && python -m swarmtrace",
        "identity_structure": ident,
        "slots": slot_classification(cascades),
        "correction_lag": correction_lag(claims),
        "page_locality": None,
        "featured_case": featured_case(events),
        "events": len(events),
        "hidden_channel": _hc.run(rev, pages, events, ev_types, lab_ip),
        "risk_score": _risk.run(events, cascades),
        "relay_scouts": _relay.run(events, claims, exclude_slots=GENERIC_SLOT_WORDS),
        "negative_result_simultaneous_answers": {
            "claim": "near-simultaneous identical answers across pages",
            "fastest": simultaneous_answers(claims, events),
            "verdict": "explained by independent lookup of a public value; NOT evidence of an out-of-band channel",
            "followup": "done: see hidden_channel (non-derivable artifacts; no view logs in the export)"},
    }
    with open(pathlib.Path(outdir) / "metrics.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(m, f, indent=2, ensure_ascii=False); f.write("\n")
    m["page_locality"] = page_locality(claims, events, rev, m["correction_lag"])
    with open(pathlib.Path(outdir) / "metrics.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(m, f, indent=2, ensure_ascii=False); f.write("\n")
    gt = pathlib.Path(outdir).resolve().parent / "ground_truth.json"
    if gt.exists():
        ev = _eval.run(claims, cascades, m, str(gt))
        with open(pathlib.Path(outdir) / "evaluation.json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(ev, f, indent=2, ensure_ascii=False); f.write("\n")
        m["evaluation"] = ev
    return m
