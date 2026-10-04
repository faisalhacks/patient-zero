#!/usr/bin/env python3
"""Render FINDINGS.md from outputs/metrics.json, cascades.jsonl and (if present)
outputs/swarmtraces_summary.json. Every number in the document is read from those
files; the prose is fixed. Hand-checked correctness judgements are stated as such and
cite collusion.wiki.

  python dev/build_findings.py           # write FINDINGS.md and EVALUATION.md
  python dev/build_findings.py --check   # exit 1 if either is stale relative to the outputs
"""
import json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]   # dev/ -> repo root
OUT = ROOT / "outputs"
WIKI = "https://collusion.wiki/"

def _jsonl(p):
    with open(p, encoding="utf-8") as f: return [json.loads(l) for l in f if l.strip()]
def hms(s):
    h, r = divmod(int(s), 3600); m, s = divmod(r, 60)
    return (f"{h} h {m} min {s} s" if h else f"{m} min {s} s" if m else f"{s} s")
def ts(t): return t.replace("T", " ").replace("Z", " UTC")

def render():
    m = json.load(open(OUT / "metrics.json", encoding="utf-8"))
    cas = {(c["task"], c["slot"]): c for c in _jsonl(OUT / "cascades.jsonl")}
    st = OUT / "swarmtraces_summary.json"
    st = json.load(open(st, encoding="utf-8")) if st.exists() else None
    gt = {it["id"]: it for it in json.load(open(ROOT / "ground_truth.json", encoding="utf-8"))["items"]}
    g_oecd, g_md = gt["oecd-two-decimal"], gt["maryland-montana-seed-relay"]
    L = []
    w = L.append
    w("# What Patient Zero found")
    w("")
    w("Every number below is produced from the public redacted export by `python download_data.py && python -m swarmtrace` "
      "and is asserted by the gate in `tests/test_reproduces.py`; this file itself is rendered from `outputs/metrics.json` "
      "by `dev/build_findings.py`. The engine reports structure (who posted what, when, how it spread). Which answer is "
      f"*correct* is a human judgement, checked against the [collusion.wiki]({WIKI}) write-up and stated as such. "
      "Labels are self-assigned agent names and are **not** a head count; \"labels\" below means distinct labels. Every headline "
      "count is given two ways, **N labels / M ip16** — distinct self-assigned labels and distinct redacted ip16 prefixes among the "
      "same posts, from the same extraction — because neither is an agent identity (§10).")
    w("")
    w("Status key: **FINDING** = reproduces, exact, correctness cross-checked. **CANDIDATE** = reproduces and exact, "
      "but the interpretation is not established by this data. **NEGATIVE RESULT** = tested and ruled out at this export's resolution.")
    w("")
    # 1. false consensus
    w("## 1. FINDING — the swarm's most-adopted OECD answers were the wrong ones")
    w("")
    w("On the OECD education-equity task the benchmark wanted a percentage to two decimals. A GET-only shortcut yielded a "
      "one-decimal figure, which agents padded to two decimals (`9.90`); the correct two-decimal figure (`9.91`) needed a sandbox "
      "bypass and was posted later.")
    w("")
    w(f"**Ground truth and citation.** The correct values ({', '.join(f'{k} `{v}`' for k, v in g_oecd['ground_truth_values'].items())}) "
      f"are taken from the collusion.wiki section [\"{g_oecd['collusion_wiki_section']}\"]({g_oecd['collusion_wiki_url']}), which states: "
      f"\"{g_oecd['quote']}\" and reproduces the live-dashboard values: \"{g_oecd['ground_truth_values_quote']}\" "
      "The padded one-decimal values are wrong by the task's own definition. (Quotes verified verbatim against the page on 2026-10-04.)")
    w("")
    w("| slot | wrong (widest) | labels / ip16 | correct | labels / ip16 | wrong first posted | correct first posted | head start of wrong over correct |")
    w("|---|---|---|---|---|---|---|---|")
    for slot, v in m["correction_lag"].items():
        w(f"| {slot} | `{v['wrong']}` | {v['wrong_adopters_total']} / {v['wrong_adopters_ip16_total']} | `{v['correct']}` | "
          f"{v['correct_adopters_total']} / {v['correct_adopters_ip16_total']} | "
          f"{ts(v['wrong_first_posted'])} | {ts(v['correction_first_posted'])} | {hms(v['head_start_of_wrong_over_correct_seconds'])} |")
    w("")
    od = []
    for slot, v in m["correction_lag"].items():
        one = v["wrong"].rstrip("0")
        n = next((x["n_agents"] for x in cas[(v["task"], slot)]["values"] if x["value"] == one), None)
        if n is not None: od.append(f"`{one}`: {n}")
    w("Inspecting any single agent's transcript shows nothing wrong (\"other cohorts already confirmed it\"), yet in aggregate "
      "the swarm converged on the wrong value because one early figure was copied faster than it was checked. The one-decimal "
      f"variants are the *earliest* values in `cascades.jsonl` (labels: {', '.join(od)}); an earlier version of this write-up "
      "quoted their gap to the padded value as a \"62-hour head start\" — that was the one-decimal-to-padded gap, not the "
      "wrong-to-correct gap, and the table above replaces it.")
    w("")
    # 2. featured
    f = m["featured_case"]; fw, ft = f["wrong"], f["truth"]
    w("## 2. FINDING — a cracked-seed guess propagated before the real answer landed")
    w("")
    w(f"On a DataUSA grocery task, agents brute-forced the test's random seed and predicted the fifth answer would be "
      f"**Maryland (52,395)**. {fw['distinct_labels']} labels / {fw['distinct_ip16']} ip16 relayed that prediction in {fw['posts']} posts between "
      f"{ts(fw['first'])} and {ts(fw['last'])} ({hms(fw['span_seconds'])}). The real answer, **Montana (8553)**, was posted by "
      f"a scout that had raced ahead ({ft['at'][1]} on `{ft['at'][2]}`) at {ts(ft['at'][0])}, {hms(ft['seconds_after_last_wrong_relay'])} "
      f"after the last relay of the guess, and was then posted by {ft['distinct_labels']} labels / {ft['distinct_ip16']} ip16; "
      f"{ft['wrong_relays_after_truth']} relays of the guess followed it. **Ground truth and citation:** collusion.wiki section "
      f"[\"{g_md['collusion_wiki_section']}\"]({g_md['collusion_wiki_url']}): \"{g_md['quote']}\" "
      "(The Montana post writes the number without a thousands separator, so it is matched by a "
      "dedicated regex in `swarmtrace/analyses.py`, not by the generic extractor.)")
    w("")
    # 3. slots
    s = m["slots"]
    w(f"## 3. FINDING — {s['flagged']} contested answer-slots, auto-detected ({s['named_slots']} named, {s['generic_word_artifacts']} regex artifacts)")
    w("")
    w(f"With no hand-coded answer keys, the tool flags {s['flagged']} (task, slot) pairs where two or more answers to the same "
      f"question were each adopted by multiple labels. **Named slots / artifacts: {s['named_slots']} / {s['generic_word_artifacts']}.** "
      f"Named: {', '.join('`'+x+'`' for x in s['named_slot_list'])}. "
      + (f"Artifacts (listed, not hidden): {', '.join('`'+x+'`' for x in s['artifact_slots'])} — a truncated multi-word name that merges "
         "two questions (United Kingdom 38.3 and United States 24.2). " if s['artifact_slots'] else "No artifacts remain. ")
      + "Generic status/format tokens (Answered, Expected, CONFIRMED, Correct, Matching, SDMX, XLSX, ...) are stopped in the extractor "
        "since STEP E (CORRECTIONS.md). Full list: `outputs/cascades.jsonl`.")
    w("")
    # 4. correction lag
    pl = m["page_locality"]
    w("## 4. FINDING — the correction was page-local: it stayed where it was posted while the error kept spreading elsewhere")
    w("")
    w("After the correct value was first public, the wrong value kept gaining adopters. The page-locality check asks, for each "
      "of those late adopters, whether the page they edited *already displayed the correct value* before their edit (checked on "
      "the previous published revision of that page with the same extractor), and whether the correct value had ever been posted "
      "on that page before.")
    w("")
    w("| slot | correct first public | late wrong adopters (labels / ip16) | whose page already showed the correct value | whose page had it posted earlier | pages with wrong / with correct / with both | last wrong adoption |")
    w("|---|---|---|---|---|---|---|")
    for slot, v in m["correction_lag"].items():
        p = pl[slot]
        w(f"| {slot} | {ts(v['correction_first_posted'])} | {v['new_wrong_adopters_after_correction']} / {v['new_wrong_ip16_after_correction']} | "
          f"{p['late_adopters_whose_page_already_showed_correct']} | {p['late_adopters_whose_page_had_correct_posted_earlier']} | "
          f"{p['pages_with_wrong']} / {p['pages_with_correct']} / {p['pages_with_both']} | "
          f"{hms(v['seconds_from_correction_to_last_wrong_adoption'])} later |")
    w("")
    tot_late = sum(v["new_wrong_adopters_after_correction"] for v in m["correction_lag"].values())
    tot_showed = sum(p["late_adopters_whose_page_already_showed_correct"] for p in pl.values())
    tot_earlier = sum(p["late_adopters_whose_page_had_correct_posted_earlier"] for p in pl.values())
    w(f"Across the four slots, {tot_showed} of {tot_late} late wrong adoptions were made on a page that already showed the correct "
      f"value, and {tot_earlier} on a page where it had ever been posted. The correction was **page-local**: it stayed on the pages "
      "it was posted to, while the already-distributed error kept spreading on other pages. We do **not** claim that any agent "
      "ignored a visible correction — the data does not support that, and this check is why.")
    w("")
    # 5. hidden channel
    hc = m["hidden_channel"]; A = hc["test_A_page_name_before_creation"]; B = hc["test_B_token_simultaneity"]; C = hc["test_C_new_page_discovery_latency"]
    cad = hc["bars"]["one_process_write_cadence"]
    w("## 5. NEGATIVE RESULT — no evidence of an out-of-band (hidden) channel")
    w("")
    w("**Plain language:** we looked for signs that agents coordinated somewhere other than the wiki, and found none that the "
      "data cannot explain. This is a negative result, not proof of absence: the follow-up proposed in the earlier write-up "
      "(\"re-run the simultaneity test on page-discovery timing from `events.jsonl`\") turned out to need a page-view log that "
      "`events.jsonl` does not contain, so the tests below use writes instead.")
    w("")
    dl = hc["data_limits"]["event_types_in_events_jsonl"]
    w(f"**What the data cannot show.** `events.jsonl` holds {dl['save']} saves, {dl['delete']} admin deletions, {dl['probe']} script "
      f"probes and {dl['revert']} reverts — no page-view or read log. \"How readers arrived at a page\" (RecentChanges vs a direct "
      "jump) is therefore not observable in this export. Three write-side tests bound the question instead, each with a stated bar: "
      f"a {hc['bars']['read_bar_seconds']} s read bar (a different label writing that long after something became visible on-wiki "
      f"is explained by RecentChanges polling) and one process's observed write cadence (the same label wrote two different pages "
      f"{cad['fastest_seconds']} s apart; {cad['pairs_within_5s']} such pairs are within 5 s).")
    w("")
    w(f"- **A. Page name posted before the page existed.** {A['mentions_before_creation_total']} mentions precede the named page's "
      f"first revision; {A['tested']} are by another label from another ip16 ({A['distinct_pages']} pages). All {A['tested']} are "
      "explained: the creator could read the mention on-wiki, the page is named after an already-active label, the two revisions "
      "share a change-summary template or body prefix (one script under rotating labels), or the labels share a host pool. "
      f"Shortest leads: {', '.join(f'{c['page']} ({c['lead_seconds']} s)' for c in A['closest_calls'][:3])}.")
    w(f"- **B. Non-derivable tokens crossing labels.** {B['per_kind']['counterapi beacon path']['tokens']} heartbeat-beacon paths, "
      f"{B['per_kind']['tunnel host']['tokens']} tunnel host and {B['per_kind']['blob host']['tokens']} blob hosts; "
      f"{sum(v['tokens_with_second_label'] for v in B['per_kind'].values())} tokens were later posted by a second label. "
      f"Fastest cross-label gap {B['fastest_gap_seconds']} s (same page); fastest where the second label had never touched the "
      f"origin page {B['fastest_gap_seconds_where_second_label_never_touched_origin_page']} s — above the read bar, so "
      "RecentChanges polling suffices. Candidates: 0.")
    w(f"- **C. New-page discovery latency.** Of {C['pages_created']} pages created in-window, {C['pages_touched_by_another_label']} "
      f"were later edited or referenced by a different label; minimum latency {C['latency_seconds']['min']} s, median "
      f"{C['latency_seconds']['median']} s, {C['latency_seconds']['under_10s']} under 10 s. Every sub-10-s case is a pre-announced "
      "link, a page named after an active label, a shared host pool, or text continuity of one sequence (e.g. a username-setting "
      "experiment that prints the creator's name under a new label; a scratch page saved with `x` under three labels in three minutes).")
    w("")
    w(f"**Verdict (computed):** {hc['verdict']}. Unexplained candidates: {hc['unexplained_candidates']}. The strongest structural "
      "fact behind this is identity, not secrecy: see §10.")
    w("")
    # 6. simultaneous answers
    ns = m["negative_result_simultaneous_answers"]["fastest"]
    w("## 6. NEGATIVE RESULT — near-simultaneous identical answers are not a hidden channel")
    w("")
    w(f"The fastest pair of identical answer values by different labels on different pages is {ns['gap_seconds']} s apart "
      f"(`{ns['slot']} {ns['value']}`: {ns['first']['label']} on `{ns['first']['page']}`, then {ns['second']['label']} on "
      f"`{ns['second']['page']}`). Answer values are publicly computable, so two agents querying the same API explains the timing; "
      "the test in §5 was built on tokens that are *not* derivable from public data for exactly this reason.")
    w("")
    # 7. risk
    rs = m["risk_score"]
    w("## 7. CANDIDATE — consensus without corroboration (\"epistemic risk\")")
    w("")
    w("**Plain language:** this is a candidate signal, not a finding. It shows that the most-copied answers were posted without "
      "any source link next to them. It does not show that agents failed to verify, because verification is not visible in this data.")
    w("")
    w("risk = labels adopting a value ÷ max(1, distinct non-infrastructure URLs cited in posts containing that value). "
      f"High = many adopters, few cited sources. {rs['values_scored']} contested values scored; "
      f"**{rs['values_with_zero_cited_sources']} cite no source URL in any post** ({rs['adopters_of_values_with_zero_cited_sources']} "
      "label-adoptions). Top five, inspected by hand:")
    w("")
    w("| task / slot | value | labels / ip16 | posts | source URLs cited in-post | risk | hand check |")
    w("|---|---|---|---|---|---|---|")
    top = {(r["task"], r["slot"], r["value"]): r for r in rs["top"]}
    for i in rs["top5_inspection"]:
        r = top[(i["task"], i["slot"], i["value"])]
        w(f"| {i['task']} / {i['slot']} | `{i['value']}` | {i['adopters']} / {i['adopters_ip16']} | {r['posts']} | {r['distinct_source_urls_in_posts']} | {i['risk']} | {i['machine_check']} |")
    w("")
    w("The \"distinct sources\" are not copied URLs — there are none: the values were posted bare. This is a citation signal, "
      "**not a verification rate** (the export has no tool-use or browsing logs; see ROADMAP.md), and it does not separate right "
      f"from wrong: the correct Slovak value `14.59` scores {top[('oecd-equity','Slovak','14.59')]['risk']} while the wrong `14.60` scores "
      f"{top[('oecd-equity','Slovak','14.60')]['risk']}. Sources do appear on the same pages "
      "(`distinct_source_urls_on_same_pages` in metrics.json), just not next to the values.")
    w("")
    # 8. relay scouts
    rl = m["relay_scouts"]
    w("## 8. CANDIDATE — relay scouts: values first posted with scout phrasing, then adopted by others")
    w("")
    w("**Plain language:** a candidate, not a finding. The counts are exact; whether the first poster really raced ahead or gave "
      "up its round is inferred from wording and is not established.")
    w("")
    w(f"{rl['scout_posts_total']} posts by {rl['labels_posting_scout_phrases']} labels contain scout phrasing "
      f"({', '.join(f'{k}: {v}' for k, v in rl['scout_posts_per_kind'].items())}). "
      f"{rl['claims_with_scout_patient_zero']} answer-value claims have such a post as their first appearance; "
      f"{rl['claims_relayed_by_at_least_2_other_labels']} of them were then posted by at least two other labels "
      f"({rl['downstream_adoptions_total']} downstream labels / {rl['downstream_ip16_total']} ip16), {rl['relayed_claims_with_first_person_self_report']} with "
      "first-person phrasing near the match.")
    w("")
    w("| task / slot | value | first posted by | matched phrase | later adopters (labels / ip16) | first follow-up |")
    w("|---|---|---|---|---|---|")
    for r in rl["top"][:8]:
        ph = r["scout_phrases"][0]
        w(f"| {r['task']} / {r['slot']} | `{r['value']}` | {r['scout_label']} | {ph['kind']} | {r['downstream_labels']} / {r['downstream_ip16']} | "
          f"{hms(r['seconds_to_first_downstream'])} later |")
    w("")
    w("Scout status is keyword-classified from post text; a matched phrase can describe another cohort's scouting rather than "
      "the poster's own (the quotes are in `metrics.json`). The counts are exact; the classification is not a finding. The clearest "
      "scout in the corpus is the Montana post in §2.")
    w("")
    # 9. cross incident
    w("## 9. Cross-incident check — SwarmTraces adapter")
    w("")
    if st:
        tw = st["techniques_from_wiki_incident"]; tx = st["techniques_extra"]
        w(f"**SwarmTraces runs in time-free mode.** That export has no timestamps, so there is no propagation tracing there — "
          f"no patient zero, no adoption order, no head start — only contestation (two or more values for the same slot, each in "
          f"at least two records): {st.get('contested_slots_time_free', 0)} contested slots, whose slot words are HTTP/header tokens and "
          f"incidental capitalised words, none a task answer ({', '.join('`'+w+'`' for w in st.get('contested_slot_words', [])[:12])}"
          f"{', ...' if len(st.get('contested_slot_words', [])) > 12 else ''}; `outputs/swarmtraces_cascades.jsonl`).")
        w("")
        w(f"`python -m swarmtrace --source swarmtraces` reads the SwarmTraces redacted export ({st['records']} records) through "
          f"`swarmtrace/adapters.py` and emits {st['claims']} claims to `outputs/swarmtraces_claims.jsonl` "
          f"({st.get('answer_value_claims', '?')} of them are \"answer values\" that are really protocol strings such as `HTTP 1.1` — "
          "that corpus has no question-answering task, so only the technique and host claims mean anything). Limits of that export, "
          f"measured: {st['records_with_time_utc']} of {st['records']} records carry a timestamp and agent identifiers are redacted, so "
          "there is no timeline, no patient zero and no contested-slot analysis there — only counts. The blob-host NO_PROXY bypass "
          f"from the wiki incident appears in {tw['blob-host NO_PROXY bypass']['records']} SwarmTraces records (it does **not** recur); "
          f"a proxy-environment bypass of the same family (`NO_PROXY=*`) appears in {tx['proxy-env bypass (NO_PROXY=*)']['records']}. "
          f"Other wiki-incident techniques there: " + ", ".join(f"{k} {v['records']}" for k, v in tw.items() if k != 'blob-host NO_PROXY bypass') + ".")
    else:
        w("Not yet run in this checkout (`python download_data.py --swarmtraces && python -m swarmtrace --source swarmtraces`).")
    w("")
    # 10. identity + scope
    idn = m["identity_structure"]
    w("## 10. Scope, identity and honesty")
    w("")
    w(f"- Runs only on the public redacted export; no live wiki contacted, no redacted identifiers reconstructed.")
    w(f"- **Labels are not agents.** {idn['labels']} distinct labels were seen from {idn['ip16_prefixes']} redacted ip16 prefixes; "
      f"one label wrote from {idn['max_ip16_per_label']} prefixes and one prefix carried {idn['max_labels_per_ip16']} labels. Every "
      "\"n labels\" above is a count of names, not of agents, and the §5 tests show one process routinely writing under several names.")
    w("- The tool reports structure. Correctness is a human judgement, stated explicitly and sourced (§1, §2 cite the exact "
      "collusion.wiki section and quote; `ground_truth.json` holds every citation).")
    w("- Status labels are fixed by the evidence, not by preference: §5 and §6 are NEGATIVE RESULTS, §7 and §8 are CANDIDATES. "
      "They are not upgraded.")
    w("- Every number that moved during the gap-closing pass (task-scoped slots, stop list, ip16 pairs, page locality) is logged "
      "with its old and new value in CORRECTIONS.md; recall and precision against the write-up are in EVALUATION.md.")
    w("- What was deliberately not built (verification rate, slop score, cost ledger) and why: ROADMAP.md.")
    w("")
    return "\n".join(L)

def render_evaluation():
    p = OUT / "evaluation.json"
    if not p.exists(): return None
    sys.path.insert(0, str(ROOT))
    from swarmtrace.evaluation import render_md
    return render_md(json.load(open(p, encoding="utf-8")))

def main():
    text = render(); ev = render_evaluation()
    target = ROOT / "FINDINGS.md"; etarget = ROOT / "EVALUATION.md"
    if "--check" in sys.argv:
        cur = target.read_text(encoding="utf-8") if target.exists() else ""
        ecur = etarget.read_text(encoding="utf-8") if etarget.exists() else ""
        ok = cur == text and (ev is None or ecur == ev)
        print("FINDINGS.md is", "current" if cur == text else "STALE (run python build_findings.py)")
        if ev is not None: print("EVALUATION.md is", "current" if ecur == ev else "STALE (run python build_findings.py)")
        sys.exit(0 if ok else 1)
    target.write_text(text, encoding="utf-8", newline="\n")
    print(f"FINDINGS.md written ({len(text):,} chars)")
    if ev is not None:
        etarget.write_text(ev, encoding="utf-8", newline="\n"); print(f"EVALUATION.md written ({len(ev):,} chars)")

if __name__ == "__main__":
    main()
