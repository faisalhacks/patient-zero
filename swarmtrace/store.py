"""
T2-store — an append-only record of every run, plus a query CLI.

outputs/store.jsonl grows by one `run` line and one `claim` line per claim on every
`python -m swarmtrace` run. Nothing is ever rewritten. `python -m swarmtrace query
<value>` (or `python patient_zero.py query <value>`) prints how that value spread,
from the newest run that recorded it.
"""
from __future__ import annotations
import json, pathlib, hashlib, collections
from datetime import datetime, timezone

def append_run(claims, source="collusion.wiki redacted export", outdir="outputs", store_name="store.jsonl"):
    path = pathlib.Path(outdir) / store_name
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    digest = hashlib.sha1("".join(c["claim_id"] for c in claims).encode()).hexdigest()[:12]
    seq = 1
    if path.exists():
        with open(path, encoding="utf-8") as f:
            seq += sum(1 for line in f if line.startswith('{"rec": "run"'))
    run_id = f"run{seq:04d}-{now}-{digest}"
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"rec": "run", "run_id": run_id, "time": now, "source": source,
                            "claims": len(claims), "claims_digest": digest}) + "\n")
        for c in claims:
            f.write(json.dumps({"rec": "claim", "run_id": run_id, "claim_id": c["claim_id"], "kind": c["kind"],
                                "slot": c["slot"], "value": c["value"], "n_agents": c.get("n_agents"),
                                "n_posts": c.get("n_posts"), "first_seen": c.get("first_seen"),
                                "patient_zero": c.get("patient_zero"), "pages": len(c.get("pages", [])),
                                "adoption": c.get("adoption", [])}) + "\n")
    return run_id, path

def load(outdir="outputs", store_name="store.jsonl"):
    path = pathlib.Path(outdir) / store_name
    if not path.exists(): return [], []
    runs, claims = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            r = json.loads(line)
            (runs if r["rec"] == "run" else claims).append(r)
    return runs, claims

def query(value, outdir="outputs", slot=None):
    runs, claims = load(outdir)
    hits = [c for c in claims if c["value"] == value and (slot is None or c["slot"] == slot)]
    if not hits:
        hits = [c for c in claims if value.lower() in c["value"].lower() and (slot is None or c["slot"] == slot)]
    out = []
    by_claim = collections.defaultdict(list)
    for c in hits: by_claim[c["claim_id"]].append(c)
    for cid, rows in by_claim.items():
        newest = max(rows, key=lambda r: r["run_id"])
        out.append({"claim_id": cid, "kind": newest["kind"], "slot": newest["slot"], "value": newest["value"],
                    "n_agents": newest["n_agents"], "n_posts": newest["n_posts"], "first_seen": newest["first_seen"],
                    "patient_zero": newest["patient_zero"], "pages": newest["pages"],
                    "adoption": newest["adoption"], "seen_in_runs": len({r["run_id"] for r in rows})})
    out.sort(key=lambda r: -(r["n_agents"] or 0))
    return {"runs_in_store": len(runs), "matches": out}

def format_query(res, limit=10):
    lines = [f"store: {res['runs_in_store']} run(s); {len(res['matches'])} matching claim(s)"]
    for m in res["matches"][:limit]:
        lines.append(f"\n{m['kind']}  {m['slot']} = {m['value']}   labels={m['n_agents']}  posts={m['n_posts']}  pages={m['pages']}  seen in {m['seen_in_runs']} run(s)")
        lines.append(f"  patient zero: {m['patient_zero']} at {m['first_seen']}")
        ad = m["adoption"]
        for a in ad[:5]: lines.append(f"    {a[0]}  {a[1]}  on {a[2] if len(a) > 2 else ''}")
        if len(ad) > 6: lines.append(f"    ... {len(ad) - 6} more ...")
        if len(ad) > 5: a = ad[-1]; lines.append(f"    {a[0]}  {a[1]}  on {a[2] if len(a) > 2 else ''}")
    return "\n".join(lines)
