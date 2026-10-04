"""
SwarmTrace core — ingest any timestamped multi-agent log, extract claims,
trace how each claim spread, and flag contested slots (same question, different
answer) and false-consensus cascades.

Output contract (LOCKED — build the viewer/report against this, not the code):
  claims.jsonl      one JSON object per claim  -> see build()
  cascades.jsonl    one JSON object per slot    -> see build()
The engine never decides what is "true"; it reports structure. A human verifies
truth. false_consensus.correct_value is always null here, by design.

Answer slots are keyed by (task, word), not by the bare word (STEP B of the
gap-closing pass): "Business 5,269" on the cashiers-with-masters task and
"Business 54,544" on the cashiers-with-bachelors task are different questions.
  task = the page's `page_family` from pages.jsonl (the export publishers' own
         classification of each page from its name and body) when that family is
         a task family;
       = for posts on coordination / link-list / unclassified pages, the unique
         task family in which the same (word, value) pair appears on task pages
         (if exactly one), else "unassigned".
"""
from __future__ import annotations
import json, re, hashlib, collections, pathlib
from datetime import datetime
ISO = "%Y-%m-%dT%H:%M:%SZ"
def _t(s): return datetime.strptime(s, ISO)

NON_TASK_FAMILIES = {"relay-coordination", "source-cache-url-list", "source-or-unclassified",
                     "off_store_unclassified", "loop-chain-infrastructure", "probe-test",
                     "unknown", "mixed-task", None, ""}
UNASSIGNED = "unassigned"

# ---------- 1. INGEST: log rows -> normalized events --------------------------
def load_page_families(pages_path):
    fam = {}
    p = pathlib.Path(pages_path)
    if not p.exists(): return fam
    for line in open(p, encoding="utf-8"):
        if line.strip():
            r = json.loads(line); fam[r["page_key"]] = r.get("page_family")
    return fam

def events_from_wiki(revisions_path, pages_path=None):
    fam = load_page_families(pages_path or pathlib.Path(revisions_path).with_name("pages.jsonl"))
    for line in open(revisions_path, encoding="utf-8"):
        r = json.loads(line)
        lines = r["body"].split("\n"); added = []
        for h in r["hunks"]:
            if h["op"] in ("insert", "replace"):
                added.extend(lines[h["b0"]:h["b1"]])
        yield {"time": r["time"], "agent": r["label"] or "(anon)",
               "where": r["page_key"], "text": "\n".join(added),
               "family": fam.get(r["page_key"]), "ip16": r.get("ip16"),
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
        "Signal","Relay","Research","Helper","Full","Values","Cached","Task","Answer",
        # STEP E: generic status / format / fragment tokens the extractor mistook for slot names
        "Answered","Answers","Expected","Expect","CONFIRMED","Correct","Exact","Thus","Prepared","Prep",
        "Ready","Submitted","ACTUAL","Actual","County","Country","Known","Likely","Matching","Other",
        "Projections","SEEN","This","Accelerating","Awaiting","BEFORE","Initial","LIVE","Literal",
        "Power","Prior","RESULT","UPDATE","Selenium","VizBuilder","Billing","ARIA","OECD",
        "SDMX","XLSX","Total","Primary","Performing","Sciences","Arts"}

def answer_pairs(text):
    return sorted({(k, v) for k, v in ANS.findall(text) if k not in STOP})

def task_index(events):
    """(word, value) -> set of task families in which the pair was posted on task pages."""
    idx = collections.defaultdict(set)
    for e in events:
        if e.get("family") in NON_TASK_FAMILIES: continue
        for k, v in answer_pairs(e["text"]): idx[(k, v)].add(e["family"])
    return idx

def task_of(e, k, v, idx):
    fam = e.get("family")
    if fam not in NON_TASK_FAMILIES: return fam
    fams = idx.get((k, v), ())
    return next(iter(fams)) if len(fams) == 1 else UNASSIGNED

def extract(events):
    events = list(events)
    idx = task_index(events)
    bucket = collections.defaultdict(list)
    for e in events:
        txt = e["text"]
        for k, v in answer_pairs(txt):
            bucket[("answer_value", task_of(e, k, v, idx), k, v)].append(e)
        for name, rx in TECH.items():
            if re.search(rx, txt, re.I):
                bucket[("technique", None, name, name)].append(e)
        for host in sorted(set(m.lower() for m in URL.findall(txt))):
            bucket[("url", None, host, host)].append(e)
    return bucket

# ---------- 3. CLAIMS + CASCADES ----------------------------------------------
def claim_id(kind, task, slot, value):
    return hashlib.sha1(f"{kind}|{task or ''}|{slot}|{value}".encode()).hexdigest()[:12]

def build(bucket):
    claims = []
    for (kind, task, slot, value), evs in bucket.items():
        evs.sort(key=lambda e: (e["time"], e["source_rev"]))
        first_by_agent, adoption, first_by_ip16 = {}, [], {}
        for e in evs:
            if e["agent"] not in first_by_agent:
                first_by_agent[e["agent"]] = e["time"]
                adoption.append([e["time"], e["agent"], e["where"], e.get("ip16")])
            ip = e.get("ip16")
            if ip is not None and ip not in first_by_ip16: first_by_ip16[ip] = e["time"]
        claims.append({"claim_id": claim_id(kind, task, slot, value), "kind": kind, "task": task,
                       "slot": slot, "value": value, "first_seen": evs[0]["time"],
                       "patient_zero": evs[0]["agent"], "n_posts": len(evs),
                       "n_agents": len(first_by_agent), "agents": list(first_by_agent),
                       "n_ip16": len(first_by_ip16),
                       "ip16_first_seen": sorted([t, ip] for ip, t in first_by_ip16.items()),
                       "pages": sorted({e["where"] for e in evs}), "adoption": adoption})
    claims.sort(key=lambda c: (-c["n_agents"], c["first_seen"], c["claim_id"]))  # deterministic
    by_slot = collections.defaultdict(list)
    for c in claims:
        if c["kind"] == "answer_value": by_slot[(c["task"], c["slot"])].append(c)
    cascades = []
    for (task, slot), cs in by_slot.items():
        contested = [c for c in cs if c["n_agents"] >= 2]
        if len(contested) < 2: continue
        contested.sort(key=lambda c: (_t(c["first_seen"]), c["claim_id"]))
        earliest = contested[0]; widest = max(contested, key=lambda c: (c["n_agents"], -_t(c["first_seen"]).timestamp()))
        fc = None
        if earliest["value"] != widest["value"]:
            hs = (_t(widest["first_seen"]) - _t(earliest["first_seen"])).total_seconds()/3600
            fc = {"earliest_value": earliest["value"], "widest_value": widest["value"],
                  "widest_agents": widest["n_agents"], "earliest_agents": earliest["n_agents"],
                  "widest_ip16": widest["n_ip16"], "earliest_ip16": earliest["n_ip16"],
                  "head_start_hours": round(hs, 1), "correct_value": None}
        cascades.append({"task": task, "slot": slot, "contested": True,
                         "values": [{"value": c["value"], "n_agents": c["n_agents"], "n_ip16": c["n_ip16"],
                                     "first_seen": c["first_seen"], "patient_zero": c["patient_zero"]}
                                    for c in sorted(contested, key=lambda c: (-c["n_agents"], c["first_seen"], c["value"]))],
                         "false_consensus": fc})
    cascades.sort(key=lambda x: (-sum(v["n_agents"] for v in x["values"]), x["task"] or "", x["slot"]))
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
        print(f"  {c['task']}/{c['slot']:13s} {vals}{tag}")
