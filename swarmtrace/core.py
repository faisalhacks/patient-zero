"""
SwarmTrace core — ingest any timestamped multi-agent log, extract claims,
trace how each claim spread, and flag contested slots (same question, different
answer) and false-consensus cascades.

Output contract (LOCKED — build the viewer/report against this, not the code):
  claims.jsonl      one JSON object per claim  -> see build()
  cascades.jsonl    one JSON object per slot    -> see build()
The engine never decides what is "true"; it reports structure. A human verifies
truth. false_consensus.correct_value is always null here, by design.
"""
from __future__ import annotations
import json, re, hashlib, collections, pathlib
from datetime import datetime
ISO = "%Y-%m-%dT%H:%M:%SZ"
def _t(s): return datetime.strptime(s, ISO)

# ---------- 1. INGEST: log rows -> normalized events --------------------------
def events_from_wiki(revisions_path):
    for line in open(revisions_path, encoding="utf-8"):
        r = json.loads(line)
        lines = r["body"].split("\n"); added = []
        for h in r["hunks"]:
            if h["op"] in ("insert", "replace"):
                added.extend(lines[h["b0"]:h["b1"]])
        yield {"time": r["time"], "agent": r["label"] or "(anon)",
               "where": r["page_key"], "text": "\n".join(added),
               "source_rev": r["rev_id"]}

# ---------- 2. EXTRACT: events -> claims --------------------------------------
GEO = r"[A-Z][a-zA-Z]{3,}"
NUM = r"\d{1,3}(?:,\d{3})+|\d+\.\d{1,3}"
ANS = re.compile(rf"\b({GEO})\b[^.\n]{{0,40}}?\b({NUM})\b")
TECH = {"blob-host NO_PROXY bypass": r"blob\.core\.windows\.net",
        "ZZZ anti-deletion backup":  r"\bZZZ[A-Z]|\[\[ZZZ",
        "PRNG seed crack":           r"random\.(?:Random|shuffle)|seed\s+\d{4,}",
        "external heartbeat beacon":  r"counterapi|heartbeat|\bhb\d{3}\b",
        "tunnel (pinggy/lhr/etc)":   r"pinggy|lhr\.life|serveo|localtunnel|loca\.lt"}
URL = re.compile(r"https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
STOP = {"Beschreibe","Describe","Confirmed","Sequence","Urgent","Round","Please","Timer",
        "Active","System","Thread","Container","Prompt","Deadline","Cohort","Current",
        "Signal","Relay","Research","Helper","Full","Values","Cached","Task","Answer"}

def extract(events):
    bucket = collections.defaultdict(list)
    for e in events:
        txt = e["text"]
        for k, v in ANS.findall(txt):
            if k in STOP: continue
            bucket[("answer_value", k, v)].append(e)
        for name, rx in TECH.items():
            if re.search(rx, txt, re.I):
                bucket[("technique", name, name)].append(e)
        for host in set(m.lower() for m in URL.findall(txt)):
            bucket[("url", host, host)].append(e)
    return bucket

# ---------- 3. CLAIMS + CASCADES ----------------------------------------------
def claim_id(kind, slot, value):
    return hashlib.sha1(f"{kind}|{slot}|{value}".encode()).hexdigest()[:12]

def build(bucket):
    claims = []
    for (kind, slot, value), evs in bucket.items():
        evs.sort(key=lambda e: e["time"])
        first_by_agent, adoption = {}, []
        for e in evs:
            if e["agent"] not in first_by_agent:
                first_by_agent[e["agent"]] = e["time"]
                adoption.append([e["time"], e["agent"], e["where"]])
        claims.append({"claim_id": claim_id(kind, slot, value), "kind": kind,
                       "slot": slot, "value": value, "first_seen": evs[0]["time"],
                       "patient_zero": evs[0]["agent"], "n_posts": len(evs),
                       "n_agents": len(first_by_agent), "agents": list(first_by_agent),
                       "pages": sorted({e["where"] for e in evs}), "adoption": adoption})
    claims.sort(key=lambda c: -c["n_agents"])
    by_slot = collections.defaultdict(list)
    for c in claims:
        if c["kind"] == "answer_value": by_slot[c["slot"]].append(c)
    cascades = []
    for slot, cs in by_slot.items():
        contested = [c for c in cs if c["n_agents"] >= 2]
        if len(contested) < 2: continue
        contested.sort(key=lambda c: _t(c["first_seen"]))
        earliest = contested[0]; widest = max(contested, key=lambda c: c["n_agents"])
        fc = None
        if earliest["value"] != widest["value"]:
            hs = (_t(widest["first_seen"]) - _t(earliest["first_seen"])).total_seconds()/3600
            fc = {"earliest_value": earliest["value"], "widest_value": widest["value"],
                  "widest_agents": widest["n_agents"], "earliest_agents": earliest["n_agents"],
                  "head_start_hours": round(hs, 1), "correct_value": None}
        cascades.append({"slot": slot, "contested": True,
                         "values": [{"value": c["value"], "n_agents": c["n_agents"],
                                     "first_seen": c["first_seen"], "patient_zero": c["patient_zero"]}
                                    for c in sorted(contested, key=lambda c: -c["n_agents"])],
                         "false_consensus": fc})
    cascades.sort(key=lambda x: -sum(v["n_agents"] for v in x["values"]))
    return claims, cascades

def run(revisions_path, outdir="outputs"):
    out = pathlib.Path(outdir); out.mkdir(exist_ok=True)
    events = list(events_from_wiki(revisions_path))
    claims, cascades = build(extract(events))
    with open(out/"claims.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for c in claims: f.write(json.dumps(c)+"\n")
    with open(out/"cascades.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for c in cascades: f.write(json.dumps(c)+"\n")
    return events, claims, cascades

if __name__ == "__main__":
    import sys
    ev, cl, ca = run(sys.argv[1] if len(sys.argv) > 1 else "../data/revisions.jsonl")
    print(f"events={len(ev)}  claims={len(cl)}  contested_slots={len(ca)}")
    print("\nTop contested slots (false-consensus candidates):")
    for c in ca[:6]:
        fc = c["false_consensus"]; tag = ""
        if fc: tag = f"  [widest '{fc['widest_value']}'({fc['widest_agents']}) vs earliest '{fc['earliest_value']}'({fc['earliest_agents']}), {fc['head_start_hours']}h head start]"
        vals = ", ".join(f"{v['value']}({v['n_agents']})" for v in c["values"][:3])
        print(f"  {c['slot']:13s} {vals}{tag}")
