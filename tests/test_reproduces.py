"""The GATE. The autonomous build loop must keep this green.
If a change stops the real findings from reproducing, the loop halts."""
import json, subprocess, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]

def _run():
    sys.path.insert(0, str(ROOT))
    from swarmtrace.core import run
    data = ROOT/"data"/"revisions.jsonl"
    assert data.exists(), "run `python download_data.py` first"
    return run(str(data), outdir=str(ROOT/"outputs"))

def test_counts():
    ev, cl, ca = _run()
    assert len(ev) == 14591, len(ev)          # events parsed from the export
    assert len(ca) >= 40, len(ca)             # contested answer slots auto-found
    assert 700 <= len(cl) <= 800, len(cl)

def test_hungary_false_consensus():
    """The headline finding: the WRONG rounded value (9.90) out-spread the
    correct raw value (9.91) and appeared days earlier."""
    cas = {c["slot"]: c for c in (json.loads(l) for l in open(ROOT/"outputs"/"cascades.jsonl", encoding="utf-8"))}
    h = cas["Hungary"]["false_consensus"]
    assert h["widest_value"] == "9.90"
    assert h["earliest_value"] == "9.9"
    assert h["widest_agents"] >= 60
    assert h["head_start_hours"] >= 48

if __name__ == "__main__":
    test_counts(); test_hungary_false_consensus()
    print("GATE PASS — findings reproduce from the raw export")
