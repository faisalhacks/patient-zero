"""Tier 2 acceptance: the SwarmTraces adapter emits claims (skipped if the file is
absent), and the append-only store grows on a second run and answers a query."""
import json, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def test_swarmtraces_adapter():
    gz = ROOT/"data"/"swarmtraces_redacted.jsonl.gz"
    if not gz.exists():
        print("  (skipped: run `python download_data.py --swarmtraces` to fetch the SwarmTraces export)"); return
    from swarmtrace.adapters import run_swarmtraces
    with tempfile.TemporaryDirectory() as d:
        ev, cl, s = run_swarmtraces(str(gz), outdir=d)
        assert len(ev) == 189579 and s["records_with_time_utc"] == 0, (len(ev), s["records_with_time_utc"])
        assert len(cl) == 357 and s["blob_host_bypass_recurs"] is False, (len(cl), s)   # 363 before STEP E's stop list; CORRECTIONS.md
        assert (s["answer_value_claims"], s["url_claims"], s["technique_claims"]) == (332, 21, 4), s
        assert s["techniques_extra"]["proxy-env bypass (NO_PROXY=*)"]["records"] == 3
        assert all(c["first_seen"] is None and c["n_agents"] is None for c in cl)   # no fabricated timeline/agents
        assert (pathlib.Path(d)/"swarmtraces_claims.jsonl").exists()

def test_store_grows_and_answers_queries():
    from swarmtrace.store import append_run, load, query
    claims = [json.loads(l) for l in open(ROOT/"outputs"/"claims.jsonl", encoding="utf-8")]
    with tempfile.TemporaryDirectory() as d:
        append_run(claims, outdir=d); runs1, rows1 = load(d)
        append_run(claims, outdir=d); runs2, rows2 = load(d)
        assert len(runs1) == 1 and len(runs2) == 2 and len(rows2) == 2 * len(rows1) == 2 * len(claims)
        q = query("9.90", outdir=d, slot="Hungary")
        assert q["runs_in_store"] == 2 and len(q["matches"]) == 1, q
        m = q["matches"][0]
        assert m["n_agents"] == 65 and m["patient_zero"] == "March16OECDScout" and m["seen_in_runs"] == 2, m
        assert m["adoption"][0][0] == "2026-06-20T04:56:50Z" or m["adoption"][0][1]  # adoption timeline present

if __name__ == "__main__":
    test_swarmtraces_adapter(); test_store_grows_and_answers_queries()
    print("TIER 2 PASS")
