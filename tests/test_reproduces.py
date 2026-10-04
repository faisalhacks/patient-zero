"""The GATE. The autonomous build loop must keep this green.
If a change stops the real findings from reproducing, the loop halts.
When a correctness fix changes a number, the gate is updated to the new true value and
the change is recorded in CORRECTIONS.md — never forced green on a stale number."""
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
    assert len(cl) == 746, len(cl)            # claims (task-scoped since STEP B; was 741 under bare-word slots)
    assert len(ca) == 27, len(ca)             # contested (task, slot) pairs (was 42 bare-word slots; see CORRECTIONS.md)

def test_hungary_false_consensus():
    """The headline finding: the WRONG rounded value (9.90) out-spread the
    correct raw value (9.91) and appeared days earlier (STEP B: slots are (task, word))."""
    cas = {(c["task"], c["slot"]): c for c in (json.loads(l) for l in open(ROOT/"outputs"/"cascades.jsonl", encoding="utf-8"))}
    h = cas[("oecd-equity", "Hungary")]["false_consensus"]
    assert h["widest_value"] == "9.90"
    assert h["earliest_value"] == "9.9"
    assert h["widest_agents"] == 65 and h["widest_ip16"] == 52, h
    assert h["head_start_hours"] >= 48
    # no slot merges values from two different tasks
    for c in cas.values(): assert c["task"] is not None and c["task"] != ""

def test_metrics():
    """Every number quoted in FINDINGS.md must come out of outputs/metrics.json, which
    is rebuilt here from the raw export by swarmtrace.analyses.run_all()."""
    _run()
    from swarmtrace.analyses import run_all
    m = run_all(datadir=str(ROOT/"data"), outdir=str(ROOT/"outputs"))
    assert m["events"] == 14591
    cl = m["correction_lag"]
    assert {k: v["new_wrong_adopters_after_correction"] for k, v in cl.items()} == \
           {"Hungary": 12, "Poland": 12, "Slovak": 14, "Czech": 3}, cl
    assert cl["Hungary"]["correction_first_posted"] == "2026-06-20T04:56:50Z"
    assert cl["Hungary"]["seconds_from_correction_to_last_wrong_adoption"] == 17892
    assert cl["Hungary"]["head_start_of_wrong_over_correct_seconds"] == 19846
    assert cl["Slovak"]["head_start_of_wrong_over_correct_seconds"] == 233490
    assert (cl["Hungary"]["wrong_adopters_total"], cl["Hungary"]["correct_adopters_total"]) == (65, 21)
    # STEP C: every headline number both ways — labels AND ip16 prefixes, same extraction
    assert (cl["Hungary"]["wrong_adopters_ip16_total"], cl["Hungary"]["correct_adopters_ip16_total"]) == (52, 27), cl["Hungary"]
    assert {k: v["new_wrong_ip16_after_correction"] for k, v in cl.items()} == \
           {"Hungary": 6, "Poland": 7, "Slovak": 6, "Czech": 3}, cl
    assert (cl["Poland"]["wrong_adopters_ip16_total"], cl["Slovak"]["wrong_adopters_ip16_total"], cl["Czech"]["wrong_adopters_ip16_total"]) == (34, 46, 19)
    f = m["featured_case"]
    assert (f["wrong"]["distinct_labels"], f["wrong"]["posts"]) == (20, 21), f["wrong"]
    assert (f["wrong"]["distinct_ip16"], f["truth"]["distinct_labels"], f["truth"]["distinct_ip16"]) == (13, 7, 9), f
    assert (f["wrong"]["first"], f["wrong"]["last"]) == ("2026-06-16T10:54:31Z", "2026-06-16T22:38:44Z")
    assert f["truth"]["at"][0] == "2026-06-16T22:56:50Z" and f["truth"]["wrong_relays_after_truth"] == 0
    assert f["truth"]["seconds_after_last_wrong_relay"] == 1086
    ns = m["negative_result_simultaneous_answers"]["fastest"]
    assert ns["gap_seconds"] == 1 and (ns["task"], ns["slot"], ns["value"]) == ("datausa-cashiers-masters", "Business", "5,269"), ns
    assert (m["identity_structure"]["labels"], m["identity_structure"]["ip16_prefixes"]) == (3103, 191)
    s = m["slots"]
    assert (s["flagged"], s["named_slots"], s["generic_word_artifacts"]) == (27, 16, 11), s
    hc = m["hidden_channel"]
    assert hc["data_limits"]["page_view_or_read_events"] == 0
    assert hc["test_A_page_name_before_creation"]["tested"] == 2198
    assert hc["test_B_token_simultaneity"]["fastest_gap_seconds"] == 13
    assert hc["test_B_token_simultaneity"]["fastest_gap_seconds_where_second_label_never_touched_origin_page"] == 33
    assert hc["test_C_new_page_discovery_latency"]["pages_created"] == 4562
    assert hc["test_C_new_page_discovery_latency"]["latency_seconds"]["min"] == 1
    assert hc["unexplained_candidates"] == 0 and hc["verdict"].startswith("RULED OUT"), hc["verdict"]
    rs = m["risk_score"]
    assert (rs["values_scored"], rs["values_with_zero_cited_sources"], rs["adopters_of_values_with_zero_cited_sources"]) == (69, 45, 502), rs
    top = rs["top"][0]
    assert (top["task"], top["slot"], top["value"], top["adopters"], top["distinct_source_urls_in_posts"]) == \
           ("datausa-cashiers-masters", "Business", "5,269", 69, 0), top
    assert all(i["machine_check"].startswith(("no source URL", "all 1 cited")) for i in rs["top5_inspection"])
    rl = m["relay_scouts"]
    assert (rl["scout_posts_total"], rl["labels_posting_scout_phrases"]) == (557, 337), rl
    assert (rl["claims_with_scout_patient_zero"], rl["claims_relayed_by_at_least_2_other_labels"],
            rl["downstream_adoptions_total"], rl["relayed_claims_with_first_person_self_report"]) == (28, 9, 32, 4), rl
    assert (rl["top"][0]["task"], rl["top"][0]["slot"], rl["top"][0]["value"], rl["top"][0]["downstream_labels"]) == \
           ("datausa-clothing-workforce", "Florida", "71,563", 7)

def test_findings_current():
    """FINDINGS.md / EVALUATION.md are rendered from the outputs; a stale write-up fails the gate."""
    sys.path.insert(0, str(ROOT))
    import build_findings
    assert (ROOT/"FINDINGS.md").read_text(encoding="utf-8") == build_findings.render(), \
        "FINDINGS.md is stale: run `python build_findings.py`"
    ev = build_findings.render_evaluation()
    assert ev is not None and (ROOT/"EVALUATION.md").read_text(encoding="utf-8") == ev, \
        "EVALUATION.md is stale: run `python build_findings.py`"

def test_evaluation():
    """STEP A: recall against collusion.wiki ground truth and precision on contested slots reproduce,
    and every ground-truth item carries a citation into the write-up."""
    ev = json.load(open(ROOT/"outputs"/"evaluation.json", encoding="utf-8"))
    ra, rp, pc = ev["recall_automatic"], ev["recall_with_hand_written_patterns"], ev["precision_contested_slots"]
    assert (ra["found"], ra["total"]) == (6, 8), ra
    assert (rp["found"], rp["total"]) == (8, 8), rp
    assert (pc["named"], pc["flagged"]) == (16, 27), pc     # STEP B: was 28/42 under bare-word slots
    for it in ev["items"]:
        assert it["collusion_wiki_url"].startswith("https://collusion.wiki/#") and it["quote"], it["id"]

if __name__ == "__main__":
    test_counts(); test_hungary_false_consensus(); test_metrics(); test_findings_current(); test_evaluation()
    print("GATE PASS - findings reproduce from the raw export")
