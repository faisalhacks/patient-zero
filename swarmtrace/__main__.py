"""python -m swarmtrace [--source wiki|swarmtraces] [path]        refresh the outputs
   python -m swarmtrace query <value> [--slot SLOT]                how did a value spread?
Refreshes outputs/claims.jsonl, outputs/cascades.jsonl and outputs/metrics.json
from the public data and appends the run to outputs/store.jsonl. Every number in
FINDINGS.md comes from these files."""
import sys, argparse
from .core import run

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "query":
        ap = argparse.ArgumentParser(prog="python -m swarmtrace query")
        ap.add_argument("value"); ap.add_argument("--slot", default=None); ap.add_argument("--outdir", default="outputs")
        a = ap.parse_args(argv[1:])
        from .store import query, format_query
        print(format_query(query(a.value, outdir=a.outdir, slot=a.slot)))
        return
    ap = argparse.ArgumentParser(prog="python -m swarmtrace")
    ap.add_argument("path", nargs="?", default=None)
    ap.add_argument("--source", choices=["wiki", "swarmtraces"], default="wiki")
    ap.add_argument("--no-analyses", action="store_true", help="only refresh claims/cascades")
    ap.add_argument("--no-store", action="store_true", help="do not append this run to outputs/store.jsonl")
    a = ap.parse_args(argv)
    if a.source == "swarmtraces":
        from .adapters import run_swarmtraces
        ev, cl, summary = run_swarmtraces(a.path or "data/swarmtraces_redacted.jsonl.gz")
        print(f"[swarmtraces] records={len(ev)}  claims={len(cl)} (url={summary['url_claims']}, technique={summary['technique_claims']}, "
              f"answer_value={summary['answer_value_claims']} = protocol-string artifacts)  timestamps={summary['records_with_time_utc']}")
        print(f"[swarmtraces] blob-host bypass recurs: {summary['blob_host_bypass_recurs']}; "
              f"NO_PROXY=* bypass records: {summary['techniques_extra']['proxy-env bypass (NO_PROXY=*)']['records']}")
        print(f"[swarmtraces] TIME-FREE MODE: {summary['contested_slots_time_free']} contested slots (contestation only; "
              "no propagation tracing — the export has no timestamps)")
        print("[swarmtraces] wrote outputs/swarmtraces_claims.jsonl, swarmtraces_cascades.jsonl, swarmtraces_summary.json")
        if not a.no_store:
            from .store import append_run
            run_id, path = append_run(cl, source="swarmtraces.org redacted export")
            print(f"[store] appended run {run_id} to {path}")
        return
    ev, cl, ca = run(a.path or "data/revisions.jsonl")
    print(f"events={len(ev)}  claims={len(cl)}  contested_slots={len(ca)}")
    if not a.no_analyses:
        from .analyses import run_all
        m = run_all()
        print(f"metrics.json written: correction_lag={ {k: v['new_wrong_adopters_after_correction'] for k, v in m['correction_lag'].items()} }")
        print(f"hidden channel: {m['hidden_channel']['verdict'][:60]}...")
    if not a.no_store:
        from .store import append_run
        run_id, path = append_run(cl)
        print(f"[store] appended run {run_id} to {path}")

if __name__ == "__main__":
    main()
