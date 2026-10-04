"""python -m swarmtrace [--source wiki|swarmtraces] [path]
Refreshes outputs/claims.jsonl, outputs/cascades.jsonl and outputs/metrics.json
from the public data. Every number in FINDINGS.md comes from these files."""
import sys, argparse
from .core import run

def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m swarmtrace")
    ap.add_argument("path", nargs="?", default=None)
    ap.add_argument("--source", choices=["wiki", "swarmtraces"], default="wiki")
    ap.add_argument("--no-analyses", action="store_true", help="only refresh claims/cascades")
    a = ap.parse_args(argv)
    if a.source == "swarmtraces":
        from .adapters import run_swarmtraces
        ev, cl, ca = run_swarmtraces(a.path or "data/swarmtraces_redacted.jsonl.gz")
        print(f"[swarmtraces] events={len(ev)}  claims={len(cl)}  contested_slots={len(ca)}")
        return
    ev, cl, ca = run(a.path or "data/revisions.jsonl")
    print(f"events={len(ev)}  claims={len(cl)}  contested_slots={len(ca)}")
    if not a.no_analyses:
        from .analyses import run_all
        m = run_all()
        hc = m["hidden_channel"]
        print(f"metrics.json written: correction_lag={ {k: v['new_wrong_adopters_after_correction'] for k, v in m['correction_lag'].items()} }")
        print(f"hidden channel: {hc['verdict']}")

if __name__ == "__main__":
    main()
