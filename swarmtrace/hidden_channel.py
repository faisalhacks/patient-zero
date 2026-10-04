"""
T1-hidden-channel — did the swarm coordinate out-of-band?

The export has NO page-view/read log (events.jsonl holds save / delete / probe /
revert rows only), so "how a reader arrived at a page" cannot be observed. What
CAN be observed is every write, with second-level timestamps. Three tests bound
the question from the write side. Each test states its bar up front; a row is a
CANDIDATE only if no innocent explanation in the data applies. An empty candidate
list is the (valid) negative result: "ruled out at this export's resolution".

Bars (stated, not tuned):
  READ_BAR = 10 s   a different label writing >= 10 s after something became
                    visible on-wiki is explained by RecentChanges polling.
  cadence           the fastest observed gap between two revisions by the SAME
                    label on DIFFERENT pages: one process can write that fast, so
                    two labels inside that gap are consistent with one process.
Identity caveat: labels are self-assigned and the redacted ip16 prefix is not
stable per label (measured in metrics.identity_structure); "shared ip16 pool"
is therefore a weak, not a strong, innocent explanation and is reported as such.
"""
from __future__ import annotations
import re, collections, statistics
from datetime import datetime

ISO = "%Y-%m-%dT%H:%M:%SZ"
def _t(s): return datetime.strptime(s, ISO)
def _sec(a, b): return int((_t(b) - _t(a)).total_seconds())
def _lab(x): return x or "(anon)"

READ_BAR = 10
TOKEN_RX = {
    "counterapi beacon path": re.compile(r"api\.counterapi\.dev/v1/([A-Za-z0-9_\-]+/[A-Za-z0-9_\-]+)"),
    "tunnel host": re.compile(r"\b([a-z0-9-]+\.(?:a\.pinggy\.link|lhr\.life|serveousercontent\.com|loca\.lt|trycloudflare\.com|ngrok(?:-free)?\.app|ngrok\.io))\b"),
    "blob host": re.compile(r"\b([a-z0-9-]+\.blob\.core\.windows\.net)\b"),
}
WORD_RX = re.compile(r"\b[A-Z][A-Za-z0-9_]{9,}\b")   # candidate wiki page names (>=10 chars)

def _write_cadence(revisions):
    """Fastest gap between consecutive revisions by the same (non-anonymous) label on
    different pages — an empirical lower bound on one process's write-to-write time."""
    by = collections.defaultdict(list)
    for r in revisions:
        if r["label"]: by[r["label"]].append((r["time"], r["page_key"]))
    gaps = []
    for v in by.values():
        v.sort()
        for a, b in zip(v, v[1:]):
            if a[1] != b[1]: gaps.append(_sec(a[0], b[0]))
    gaps.sort()
    return {"fastest_seconds": gaps[0] if gaps else None,
            "pairs_within_5s": sum(1 for g in gaps if g <= 5),
            "median_seconds": int(statistics.median(gaps)) if gaps else None, "pairs": len(gaps)}

def _same_process_evidence(r1, t1, l1, r2, t2, l2):
    """Text-level evidence that two revisions under different labels come from one process.
    r1/r2 revision rows, t1/t2 their added text, l1/l2 their labels. Returns reasons."""
    why = []
    s1, s2 = (r1.get("change_summary") or ""), (r2.get("change_summary") or "")
    if s1 and s2 and re.sub(r"\d", "", s1) == re.sub(r"\d", "", s2) and s1 != s2:
        why.append("both revisions carry the same change-summary template (digits differ): one script")
    if l1 in t2 or l2 in t1:
        why.append("one revision's text names the other's label (username/signature experiment)")
    a, b = t1.strip(), t2.strip()
    if a and b and (a.split("\n")[0] == b.split("\n")[0] or (len(a) >= 8 and len(b) >= 8 and a[:8] == b[:8])):
        why.append("the two texts share the same first line / 8-char prefix (body continuity of one sequence)")
    if len(a) <= 2 or len(b) <= 2:
        why.append("one revision is a test save (added text <= 2 chars)")
    return why

def run(revisions, pages, events, event_type_counts, lab_ip):
    revs = {r["rev_id"]: r for r in revisions}
    text_of = {e["source_rev"]: e["text"] for e in events}
    cadence = _write_cadence(revisions)
    cad = cadence["fastest_seconds"] or 0
    created = {}
    for r in sorted(revisions, key=lambda r: r["time"]):
        created.setdefault(r["page_key"], r)
    clean = {k: r for k, r in created.items()
             if r["diff_base_reason"] == "page_created" and pages[k]["n_revs_before"] == 0}
    names = {pages[k]["name"]: k for k in clean if len(pages[k]["name"]) >= 10}
    cre_by_label = collections.defaultdict(list)
    for k, r in clean.items(): cre_by_label[_lab(r["label"])].append(_t(r["time"]))
    label_first_seen = {}
    for r in sorted(revisions, key=lambda r: r["time"]):
        label_first_seen.setdefault(_lab(r["label"]), r["time"])

    # one pass: every mention of a (later- or earlier-) created page name on another page
    mentions = collections.defaultdict(list)          # page_key -> [(time, label, where, rev_id)]
    for e in events:
        for name in sorted(set(WORD_RX.findall(e["text"])) & names.keys()):
            k = names[name]
            if e["where"] != k: mentions[k].append((e["time"], e["agent"], e["where"], e["source_rev"]))
    shared = lambda a, b: bool(lab_ip.get(a, set()) & lab_ip.get(b, set()))

    # ---------------- Test A: name posted by another label BEFORE the page existed ----------------
    n_total = n_anon = n_same_label = n_same_ip16 = 0; A = []
    for k, ms in sorted(mentions.items()):
        c = clean[k]; cl = _lab(c["label"]); name = pages[k]["name"]
        for (mt, ml, mw, rid) in ms:
            lead = _sec(mt, c["time"])
            if lead <= 0: continue
            n_total += 1
            if ml == "(anon)" or cl == "(anon)": n_anon += 1; continue
            if ml == cl: n_same_label += 1; continue
            if revs[rid]["ip16"] == c["ip16"]: n_same_ip16 += 1; continue
            why = []
            if lead >= READ_BAR: why.append(f"creator could have read the mention on-wiki ({lead} s >= {READ_BAR} s read bar)")
            if name in label_first_seen and _t(label_first_seen[name]) < _t(c["time"]):
                why.append("page is named after a label that had already signed posts (pages named after agents)")
            if lead <= cad: why.append(f"lead {lead} s is within one process's observed write cadence ({cad} s)")
            if any(abs((t - _t(mt)).total_seconds()) <= 120 for t in cre_by_label[ml]):
                why.append("mentioning label itself created a page within 120 s (page-chain process)")
            if shared(ml, cl): why.append("labels share an ip16 prefix elsewhere in the export (weak: same host pool)")
            why += _same_process_evidence(revs[rid], text_of[rid], ml, c, text_of[c["rev_id"]], cl)
            A.append({"page": name, "lead_seconds": lead, "mentioned_at": mt, "mentioned_by": ml, "mentioned_on": mw,
                      "created_at": c["time"], "created_by": cl, "innocent_explanations": why,
                      "status": "explained" if why else "CANDIDATE"})
    A.sort(key=lambda x: (x["lead_seconds"], x["page"], x["mentioned_at"], x["mentioned_by"], x["mentioned_on"]))
    def bucket(s): return "<=60s" if s <= 60 else "<=1h" if s <= 3600 else "<=24h" if s <= 86400 else ">24h"
    B_ = collections.defaultdict(list)
    for x in A: B_[bucket(x["lead_seconds"])].append(x)
    test_a = {
        "definition": "page name (>=10 chars) posted on another page by another label from another ip16, "
                      "before the page's first published revision; pages created in-window only",
        "mentions_before_creation_total": n_total, "excluded_anonymous": n_anon,
        "excluded_same_label": n_same_label, "excluded_same_ip16": n_same_ip16,
        "tested": len(A), "distinct_pages": len({x["page"] for x in A}),
        "buckets_by_lead": {b: {"mentions": len(v), "pages": len({x["page"] for x in v}),
                                "explained": sum(1 for x in v if x["status"] == "explained")}
                            for b, v in sorted(B_.items(), key=lambda kv: ["<=60s", "<=1h", "<=24h", ">24h"].index(kv[0]))},
        "candidates": [x for x in A if x["status"] == "CANDIDATE"][:25],
        "closest_calls": A[:10],
    }

    # ---------------- Test B: non-derivable tokens crossing labels ----------------
    edits = collections.defaultdict(set)
    for e in events: edits[e["agent"]].add(e["where"])
    rows = []; per_kind = {}
    for kind, rx in TOKEN_RX.items():
        first = collections.defaultdict(list)
        for e in events:
            for t in sorted(set(rx.findall(e["text"]))): first[t].append((e["time"], e["agent"], e["where"]))
        multi = 0
        for t, v in sorted(first.items()):
            v.sort(); a0 = v[0]
            others = [x for x in v if x[1] != a0[1]]
            if not others: continue
            multi += 1; s = others[0]; gap = _sec(a0[0], s[0])
            could_read = s[2] == a0[2] or a0[2] in edits[s[1]]
            why = []
            if could_read: why.append("second label posted on, or had edited, the page where the token first appeared")
            if gap >= READ_BAR: why.append(f"token was visible on-wiki {gap} s before the second post (>= {READ_BAR} s read bar; RecentChanges polling suffices)")
            if gap <= cad: why.append(f"gap {gap} s is within one process's observed write cadence ({cad} s)")
            if shared(a0[1], s[1]): why.append("labels share an ip16 prefix elsewhere in the export (weak: same host pool)")
            rows.append({"kind": kind, "token": t, "gap_seconds": gap, "same_page": s[2] == a0[2],
                         "first": {"time": a0[0], "label": a0[1], "page": a0[2]},
                         "second": {"time": s[0], "label": s[1], "page": s[2]},
                         "second_had_touched_origin_page": could_read, "innocent_explanations": why,
                         "status": "explained" if why else "CANDIDATE"})
        per_kind[kind] = {"tokens": len(first), "tokens_with_second_label": multi}
    rows.sort(key=lambda r: (r["gap_seconds"], r["kind"], r["token"]))
    cross = [r for r in rows if not r["second_had_touched_origin_page"]]
    test_b = {
        "definition": "non-derivable tokens (beacon paths, tunnel hosts, blob hosts): seconds from first post to "
                      "the first post by a different label",
        "per_kind": per_kind,
        "fastest_gap_seconds": rows[0]["gap_seconds"] if rows else None,
        "fastest_gap_seconds_where_second_label_never_touched_origin_page": cross[0]["gap_seconds"] if cross else None,
        "candidates": [r for r in rows if r["status"] == "CANDIDATE"],
        "closest_calls": rows[:8],
    }

    # ---------------- Test C: how fast is a brand-new page first touched by a different label? ----------------
    first_touch = {}   # page_key -> (latency, time, label, how)
    by_page = collections.defaultdict(list)
    for e in events: by_page[e["where"]].append((e["time"], e["agent"], e["source_rev"]))
    for k, c in clean.items():
        cl = _lab(c["label"]); best = None
        for (t, l, rid) in by_page[k]:
            if l != cl and l != "(anon)" and _t(t) > _t(c["time"]):
                lat = _sec(c["time"], t)
                if best is None or lat < best[0]: best = (lat, t, l, "edited the page", rid)
        for (t, l, w, rid) in mentions.get(k, []):
            if l != cl and l != "(anon)" and _t(t) > _t(c["time"]):
                lat = _sec(c["time"], t)
                if best is None or lat < best[0]: best = (lat, t, l, f"referenced it on {w}", rid)
        if best: first_touch[k] = best
    C = []
    for k, (lat, t, l, how, rid) in sorted(first_touch.items()):
        c = clean[k]; cl = _lab(c["label"]); name = pages[k]["name"]
        why = []
        if lat >= READ_BAR: why.append(f"{lat} s >= {READ_BAR} s read bar: RecentChanges polling suffices")
        if any(_t(mt) < _t(c["time"]) for (mt, _, _, _) in mentions.get(k, [])):
            why.append("page name was already posted on-wiki before creation (pre-announced link)")
        if name in label_first_seen and _t(label_first_seen[name]) < _t(c["time"]):
            why.append("page is named after a label that had already signed posts (pages named after agents)")
        if lat <= cad: why.append(f"latency {lat} s is within one process's observed write cadence ({cad} s)")
        if shared(l, cl): why.append("labels share an ip16 prefix elsewhere in the export (weak: same host pool)")
        why += _same_process_evidence(c, text_of[c["rev_id"]], cl, revs[rid], text_of[rid], l)
        C.append({"page": name, "created_at": c["time"], "created_by": cl, "first_other_label": l,
                  "first_touch_at": t, "latency_seconds": lat, "how": how,
                  "innocent_explanations": why, "status": "explained" if why else "CANDIDATE"})
    C.sort(key=lambda x: (x["latency_seconds"], x["page"]))
    lats = [x["latency_seconds"] for x in C]
    test_c = {
        "definition": "for every page created in-window, seconds from its first revision to the first edit of it, "
                      "or reference to it, by a different label (a write-side bound on discovery time)",
        "pages_created": len(clean), "pages_touched_by_another_label": len(C),
        "latency_seconds": {"min": lats[0] if lats else None, "median": int(statistics.median(lats)) if lats else None,
                            "under_10s": sum(1 for x in lats if x < 10), "under_60s": sum(1 for x in lats if x < 60)},
        "candidates": [x for x in C if x["status"] == "CANDIDATE"][:25],
        "closest_calls": C[:10],
    }

    n_cand = len(test_a["candidates"]) + len(test_b["candidates"]) + len(test_c["candidates"])
    return {
        "question": "did the swarm coordinate out-of-band (a hidden channel)?",
        "data_limits": {
            "event_types_in_events_jsonl": event_type_counts, "page_view_or_read_events": 0,
            "note": "no page-view/read log in the export, so 'how readers arrived' (RecentChanges vs direct jump) "
                    f"is not observable; request_action exists only on {event_type_counts.get('probe', 0)} script "
                    f"probes and {event_type_counts.get('delete', 0)} admin deletions",
        },
        "bars": {"read_bar_seconds": READ_BAR, "one_process_write_cadence": cadence},
        "test_A_page_name_before_creation": test_a,
        "test_B_token_simultaneity": test_b,
        "test_C_new_page_discovery_latency": test_c,
        "unexplained_candidates": n_cand,
        "verdict": ("RULED OUT at this export's resolution: every cross-label foreknowledge, simultaneity and "
                    "discovery event is within the stated read bar or one process's write cadence, or has another "
                    "innocent explanation checked in the data; no event requires an out-of-band channel"
                    if n_cand == 0 else
                    f"{n_cand} CANDIDATE(s) have no innocent explanation in the data (listed; not a finding)"),
    }
