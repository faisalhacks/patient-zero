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


def test_metrics():
    """Every number quoted in FINDINGS.md must come out of outputs/metrics.json, which
    is rebuilt here from the raw export by swarmtrace.analyses.run_all()."""
    _run()
    from swarmtrace.analyses import run_all
    m = run_all(datadir=str(ROOT/"data"), outdir=str(ROOT/"outputs"))
    cl = m["correction_lag"]
    assert {k: v["new_wrong_adopters_after_correction"] for k, v in cl.items()} == \
           {"Hungary": 12, "Poland": 12, "Slovak": 14, "Czech": 3}, cl
    assert cl["Hungary"]["correction_first_posted"] == "2026-06-20T04:56:50Z"
    assert cl["Hungary"]["seconds_from_correction_to_last_wrong_adoption"] == 17892
    f = m["featured_case"]
    assert (f["wrong"]["distinct_labels"], f["wrong"]["posts"]) == (20, 21), f["wrong"]
    assert (f["wrong"]["first"], f["wrong"]["last"]) == ("2026-06-16T10:54:31Z", "2026-06-16T22:38:44Z")
    assert f["truth"]["at"][0] == "2026-06-16T22:56:50Z" and f["truth"]["wrong_relays_after_truth"] == 0
    assert f["truth"]["seconds_after_last_wrong_relay"] == 1086
    assert m["negative_result_simultaneous_answers"]["fastest"]["gap_seconds"] == 1
    assert (m["identity_structure"]["labels"], m["identity_structure"]["ip16_prefixes"]) == (3103, 191)
    assert (m["slots"]["flagged"], m["slots"]["named_slots"], m["slots"]["generic_word_artifacts"]) == (42, 28, 14)
    hc = m["hidden_channel"]
    assert hc["data_limits"]["page_view_or_read_events"] == 0
    assert hc["test_A_page_name_before_creation"]["tested"] == 2198
    assert hc["test_B_token_simultaneity"]["fastest_gap_seconds"] == 13
    assert hc["test_B_token_simultaneity"]["fastest_gap_seconds_where_second_label_never_touched_origin_page"] == 33
    assert hc["test_C_new_page_discovery_latency"]["pages_created"] == 4562
    assert hc["test_C_new_page_discovery_latency"]["latency_seconds"]["min"] == 1
    assert hc["unexplained_candidates"] == 0 and hc["verdict"].startswith("RULED OUT"), hc["verdict"]
    rs = m["risk_score"]
    assert (rs["values_scored"], rs["values_with_zero_cited_sources"], rs["adopters_of_values_with_zero_cited_sources"]) == (122, 86, 662), rs
    top = rs["top"][0]
    assert (top["slot"], top["value"], top["adopters"], top["distinct_source_urls_in_posts"]) == ("Business", "5,269", 69, 0), top
    assert all(i["machine_check"].startswith(("no source URL", "all 1 cited")) for i in rs["top5_inspection"])

if __name__ == "__main__":
    test_counts(); test_hungary_false_consensus(); test_metrics()
    print("GATE PASS - findings reproduce from the raw export")
