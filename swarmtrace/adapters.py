"""
Adapters for other public multi-agent corpora. Each adapter turns rows into the
same normalized event shape the engine ingests: {time, agent, where, text}.

SwarmTraces (https://swarmtraces.org/data/final/redacted.jsonl.gz)
  rows: {id, cite, kind (payload|recovered_text|response), parent_id, time_utc, tags, text}
  Honest limits of that export, measured on the pinned file:
    * time_utc is null on EVERY row  -> no timeline, no patient zero, no head start;
    * agent identifiers are redacted  -> "agent" is the record id, so n_agents means
      "distinct records", never agents.
  The adapter therefore writes to outputs/swarmtraces_*.jsonl (it never touches the
  locked wiki outputs) and marks ordering as "record id, not time".
"""
from __future__ import annotations
import gzip, json, re, pathlib, collections
from .core import extract, claim_id, TECH

UNTIMED = None
TECH_EXTRA = {  # cross-incident technique markers, in addition to core.TECH
    "proxy-env bypass (NO_PROXY=*)": r"NO_PROXY=\s*['\"]?\*",
}

def events_from_swarmtraces(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            r = json.loads(line)
            yield {"time": r.get("time_utc") or UNTIMED, "agent": r["id"], "where": r.get("parent_id") or r["id"],
                   "text": r.get("text") or "", "source_rev": r["id"], "kind": r.get("kind")}

def build_untimed(bucket):
    """claims without a timeline: adoption is ordered by record id (explicitly NOT time)."""
    claims = []
    for (kind, slot, value), evs in bucket.items():
        evs.sort(key=lambda e: e["source_rev"])
        firsts, adoption = {}, []
        for e in evs:
            if e["agent"] not in firsts:
                firsts[e["agent"]] = e["source_rev"]; adoption.append([None, e["agent"], e["where"]])
        claims.append({"claim_id": claim_id(kind, slot, value), "kind": kind, "slot": slot, "value": value,
                       "first_seen": None, "patient_zero": None, "order": "record id, not time",
                       "n_posts": len(evs), "n_records": len(firsts), "n_agents": None,
                       "pages": sorted({e["where"] for e in evs}), "adoption": adoption})
    claims.sort(key=lambda c: (-c["n_records"], c["claim_id"]))
    return claims

def run_swarmtraces(path="data/swarmtraces_redacted.jsonl.gz", outdir="outputs"):
    out = pathlib.Path(outdir); out.mkdir(exist_ok=True)
    events = list(events_from_swarmtraces(path))
    bucket = extract(events)
    for name, rx in TECH_EXTRA.items():
        cre = re.compile(rx, re.I)
        for e in events:
            if cre.search(e["text"]): bucket[("technique", name, name)].append(e)
    claims = build_untimed(bucket)
    tech = {c["value"]: {"records": c["n_records"], "posts": c["n_posts"]} for c in claims if c["kind"] == "technique"}
    summary = {
        "source": "swarmtraces.org redacted export", "records": len(events),
        "records_with_time_utc": sum(1 for e in events if e["time"]),
        "records_by_kind": dict(collections.Counter(e["kind"] for e in events)),
        "agent_identity": "redacted in source; n_records counts records, not agents",
        "claims": len(claims),
        "answer_value_claims": sum(1 for c in claims if c["kind"] == "answer_value"),
        "answer_value_note": "that corpus has no question-answering task; its 'answer values' are protocol strings "
                             "(e.g. 'HTTP 1.1') matched by the generic extractor and carry no meaning",
        "url_claims": sum(1 for c in claims if c["kind"] == "url"),
        "technique_claims": sum(1 for c in claims if c["kind"] == "technique"),
        "techniques_from_wiki_incident": {name: tech.get(name, {"records": 0, "posts": 0}) for name in TECH},
        "techniques_extra": {name: tech.get(name, {"records": 0, "posts": 0}) for name in TECH_EXTRA},
        "blob_host_bypass_recurs": tech.get("blob-host NO_PROXY bypass", {"records": 0})["records"] > 0,
        "top_url_hosts": [{"host": c["value"], "records": c["n_records"]} for c in claims if c["kind"] == "url"][:10],
        "cascades": "not computable: contested slots need an adoption order, and this export has no timestamps",
    }
    with open(out / "swarmtraces_claims.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for c in claims: f.write(json.dumps(c) + "\n")
    with open(out / "swarmtraces_summary.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=2); f.write("\n")
    return events, claims, summary
