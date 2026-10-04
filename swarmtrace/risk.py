"""
T1-risk-score — "epistemic risk" of a contested value: consensus without corroboration.

    risk(value) = n_labels_adopting / max(1, n_distinct_source_urls_cited_in_posts_containing_the_value)

High = many adopters, few independently cited sources = copying over sourcing.
This is NOT a verification rate: the export has no tool-use / browsing logs, so we
cannot see whether an agent checked a value before posting it (see ROADMAP.md). It
only counts what the posts themselves cite. Everything here is a CANDIDATE signal
until the top rows are inspected by hand; the inspection table is emitted so the
reader can do it too.
"""
from __future__ import annotations
import re, collections
from .core import answer_pairs, task_index, task_of

FULL_URL = re.compile(r"https?://[^\s\]\)\|>\"'`,;]+")
# infrastructure, not sources: heartbeat beacons, the wiki itself, tunnels, placeholders
INFRA_HOSTS = ("counterapi.dev", "wikiservice.at", "pinggy", "lhr.life", "serveousercontent.com", "loca.lt",
               "trycloudflare.com", "ngrok", "localhost", "127.0.0.1", "example.com")
def _norm(u): return u.rstrip(".:*`'\"").lower()
def _infra(u): return any(h in u for h in INFRA_HOSTS)
def _host(u): return re.sub(r"^https?://", "", u).split("/")[0]

def run(events, cascades, top_n=5):
    targets = {(c["task"], c["slot"], v["value"]) for c in cascades for v in c["values"]}
    posts_by = collections.defaultdict(list)
    page_urls = collections.defaultdict(set)
    idx = task_index(events)
    for e in events:
        us = {_norm(u) for u in FULL_URL.findall(e["text"])}
        page_urls[e["where"]] |= us
        hits = {(task_of(e, k, v, idx), k, v) for k, v in answer_pairs(e["text"])}
        for key in hits & targets: posts_by[key].append((e, us))
    rows = []
    for (task, slot, value), posts in sorted(posts_by.items(), key=lambda kv: (kv[0][0] or "", kv[0][1], kv[0][2])):
        labels = {e["agent"] for e, _ in posts}; ip16s = {e.get("ip16") for e, _ in posts} - {None}
        pages = {e["where"] for e, _ in posts}
        urls = set(); src = set(); with_url = 0
        for e, us in posts:
            if us: with_url += 1
            urls |= us; src |= {u for u in us if not _infra(u)}
        src_pages = set()
        for p in pages: src_pages |= {u for u in page_urls[p] if not _infra(u)}
        rows.append({"task": task, "slot": slot, "value": value, "adopters": len(labels), "adopters_ip16": len(ip16s), "posts": len(posts),
                     "posts_citing_any_url": with_url, "distinct_urls_in_posts": len(urls),
                     "distinct_source_urls_in_posts": len(src), "distinct_source_hosts_in_posts": len({_host(u) for u in src}),
                     "distinct_source_urls_on_same_pages": len(src_pages),
                     "risk": round(len(labels) / max(1, len(src)), 2), "_src": sorted(src)})
    rows.sort(key=lambda r: (-r["risk"], -r["adopters"], r["task"] or "", r["slot"], r["value"]))
    inspection = []
    for r in rows[:top_n]:
        src = r["_src"]; hosts = collections.Counter(_host(u) for u in src)
        if not src: check = "no source URL is cited in any post containing this value"
        elif len(hosts) == 1: check = f"all {len(src)} cited URL(s) are on one host ({next(iter(hosts))}); not independent sources"
        else: check = f"{len(src)} cited URL(s) across {len(hosts)} hosts"
        inspection.append({"task": r["task"], "slot": r["slot"], "value": r["value"], "adopters": r["adopters"], "adopters_ip16": r["adopters_ip16"], "risk": r["risk"],
                           "source_urls_cited": src[:12], "machine_check": check})
    for r in rows: r.pop("_src")
    return {
        "definition": "risk = distinct labels adopting the value / max(1, distinct non-infrastructure URLs cited in "
                      "posts that contain the value); values are the competing answers in cascades.jsonl, keyed by (task, slot)",
        "not_a_verification_rate": "the export has no tool-use or browsing logs; this counts citations in post text only",
        "infrastructure_hosts_excluded": list(INFRA_HOSTS),
        "values_scored": len(rows),
        "values_with_zero_cited_sources": sum(1 for r in rows if r["distinct_source_urls_in_posts"] == 0),
        "adopters_of_values_with_zero_cited_sources": sum(r["adopters"] for r in rows if r["distinct_source_urls_in_posts"] == 0),
        "top": rows[:20],
        "top5_inspection": inspection,
        "status": "CANDIDATE — a structural signal (adoption without in-post citation), not evidence that any agent skipped verification",
    }
