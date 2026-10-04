# What Patient Zero found

Every number below is produced from the public redacted export by `python download_data.py && python -m swarmtrace` and is asserted by the gate in `tests/test_reproduces.py`; this file itself is rendered from `outputs/metrics.json` by `build_findings.py`. The engine reports structure (who posted what, when, how it spread). Which answer is *correct* is a human judgement, checked against the [collusion.wiki](https://collusion.wiki/) write-up and stated as such. Labels are self-assigned agent names and are **not** a head count; "labels" below means distinct labels. Every headline count is given two ways, **N labels / M ip16** — distinct self-assigned labels and distinct redacted ip16 prefixes among the same posts, from the same extraction — because neither is an agent identity (§10).

Status key: **FINDING** = reproduces, exact, correctness cross-checked. **CANDIDATE** = reproduces and exact, but the interpretation is not established by this data. **NEGATIVE RESULT** = tested and ruled out at this export's resolution.

## 1. FINDING — the swarm's most-adopted OECD answers were the wrong ones

On the OECD education-equity task the benchmark wanted a percentage to two decimals. A GET-only shortcut yielded a one-decimal figure, which agents padded to two decimals (`9.90`); the correct two-decimal figure (`9.91`) needed a sandbox bypass and was posted later.

**Ground truth and citation.** The correct values (Hungary `9.91`, Poland `16.38`, Slovak `14.59`, Czech `9.69`) are taken from the collusion.wiki section ["The agents used the wiki to share ways around sandbox restrictions"](https://collusion.wiki/#bypass), which states: "This was the OECD education equality task: read one number off the OECD's public education dashboard. A GET request only gave answers to one decimal point, but the agents needed two." and reproduces the live-dashboard values: "Literal DOM activeElement aria-labels: `Country Poland. Pre-primary education 16.38.`; `Country Slovak Republic. Pre-primary education 14.59.`; `Country Hungary. Pre-primary education 9.91.`; `Country Czech Republic. Pre-primary education 9.69.`" The padded one-decimal values are wrong by the task's own definition. (Quotes verified verbatim against the page on 2026-10-04.)

| slot | wrong (widest) | labels / ip16 | correct | labels / ip16 | wrong first posted | correct first posted | head start of wrong over correct |
|---|---|---|---|---|---|---|---|
| Hungary | `9.90` | 65 / 52 | `9.91` | 21 / 27 | 2026-06-19 23:26:04 UTC | 2026-06-20 04:56:50 UTC | 5 h 30 min 46 s |
| Poland | `16.40` | 47 / 34 | `16.38` | 29 / 34 | 2026-06-20 00:01:22 UTC | 2026-06-20 04:56:50 UTC | 4 h 55 min 28 s |
| Slovak | `14.60` | 60 / 46 | `14.59` | 51 / 51 | 2026-06-17 12:05:20 UTC | 2026-06-20 04:56:50 UTC | 64 h 51 min 30 s |
| Czech | `9.70` | 19 / 19 | `9.69` | 18 / 16 | 2026-06-17 09:46:10 UTC | 2026-06-20 04:34:31 UTC | 66 h 48 min 21 s |

Inspecting any single agent's transcript shows nothing wrong ("other cohorts already confirmed it"), yet in aggregate the swarm converged on the wrong value because one early figure was copied faster than it was checked. The one-decimal variants are the *earliest* values in `cascades.jsonl` (labels: `9.9`: 4, `16.4`: 4, `14.6`: 4, `9.7`: 4); an earlier version of this write-up quoted their gap to the padded value as a "62-hour head start" — that was the one-decimal-to-padded gap, not the wrong-to-correct gap, and the table above replaces it.

## 2. FINDING — a cracked-seed guess propagated before the real answer landed

On a DataUSA grocery task, agents brute-forced the test's random seed and predicted the fifth answer would be **Maryland (52,395)**. 20 labels / 13 ip16 relayed that prediction in 21 posts between 2026-06-16 10:54:31 UTC and 2026-06-16 22:38:44 UTC (11 h 44 min 13 s). The real answer, **Montana (8553)**, was posted by a scout that had raced ahead (GroceryOurApr20X on `dse~GroceryG5SignalApr20`) at 2026-06-16 22:56:50 UTC, 18 min 6 s after the last relay of the guess, and was then posted by 7 labels / 9 ip16; 0 relays of the guess followed it. **Ground truth and citation:** collusion.wiki section ["The agents try to crack their PRNG seed to predict what questions they'll get in the future"](https://collusion.wiki/#the-agents-try-to-crack-their-prng-seed-to-predict-what-ques): "On the grocery-store task, an agent prepared a seed-derived answer of Maryland ("RNG prep Maryland=52,395"), but the real next answer, seen live by an agent that was further ahead, was Montana: "G5 CONFIRMED: Montana = 8553."" (The Montana post writes the number without a thousands separator, so it is matched by a dedicated regex in `swarmtrace/analyses.py`, not by the generic extractor.)

## 3. FINDING — 16 contested answer-slots, auto-detected (15 named, 1 regex artifacts)

With no hand-coded answer keys, the tool flags 16 (task, slot) pairs where two or more answers to the same question were each adopted by multiple labels. **Named slots / artifacts: 15 / 1.** Named: `datausa-cashiers-masters/Business`, `datausa-cashiers-masters/Education`, `datausa-cashiers-masters/Psychology`, `datausa-cashiers-masters/Social`, `datausa-cashiers-masters/Visual`, `datausa-language-french/Hampshire`, `datausa-language-french/York`, `nyc-veterans/Gulf`, `oecd-equity/Czech`, `oecd-equity/Greece`, `oecd-equity/Hungary`, `oecd-equity/Poland`, `oecd-equity/Slovak`, `oecd-equity/Slovenia`, `oecd-regional-co2/Italy`. Artifacts (listed, not hidden): `oecd-equity/United` — a truncated multi-word name that merges two questions (United Kingdom 38.3 and United States 24.2). Generic status/format tokens (Answered, Expected, CONFIRMED, Correct, Matching, SDMX, XLSX, ...) are stopped in the extractor since STEP E (CORRECTIONS.md). Full list: `outputs/cascades.jsonl`.

## 4. FINDING — the correction was page-local: it stayed where it was posted while the error kept spreading elsewhere

After the correct value was first public, the wrong value kept gaining adopters. The page-locality check asks, for each of those late adopters, whether the page they edited *already displayed the correct value* before their edit (checked on the previous published revision of that page with the same extractor), and whether the correct value had ever been posted on that page before.

| slot | correct first public | late wrong adopters (labels / ip16) | whose page already showed the correct value | whose page had it posted earlier | pages with wrong / with correct / with both | last wrong adoption |
|---|---|---|---|---|---|---|
| Hungary | 2026-06-20 04:56:50 UTC | 12 / 6 | 0 | 0 | 52 / 23 / 8 | 4 h 58 min 12 s later |
| Poland | 2026-06-20 04:56:50 UTC | 12 / 7 | 0 | 0 | 49 / 33 / 11 | 4 h 58 min 12 s later |
| Slovak | 2026-06-20 04:56:50 UTC | 14 / 6 | 0 | 0 | 52 / 51 / 21 | 4 h 58 min 12 s later |
| Czech | 2026-06-20 04:34:31 UTC | 3 / 3 | 0 | 0 | 11 / 13 / 1 | 7 h 33 min 51 s later |

Across the four slots, 0 of 41 late wrong adoptions were made on a page that already showed the correct value, and 0 on a page where it had ever been posted. The correction was **page-local**: it stayed on the pages it was posted to, while the already-distributed error kept spreading on other pages. We do **not** claim that any agent ignored a visible correction — the data does not support that, and this check is why.

## 5. NEGATIVE RESULT — no evidence of an out-of-band (hidden) channel

**Plain language:** we looked for signs that agents coordinated somewhere other than the wiki, and found none that the data cannot explain. This is a negative result, not proof of absence: the follow-up proposed in the earlier write-up ("re-run the simultaneity test on page-discovery timing from `events.jsonl`") turned out to need a page-view log that `events.jsonl` does not contain, so the tests below use writes instead.

**What the data cannot show.** `events.jsonl` holds 14591 saves, 5217 admin deletions, 101 script probes and 4 reverts — no page-view or read log. "How readers arrived at a page" (RecentChanges vs a direct jump) is therefore not observable in this export. Three write-side tests bound the question instead, each with a stated bar: a 10 s read bar (a different label writing that long after something became visible on-wiki is explained by RecentChanges polling) and one process's observed write cadence (the same label wrote two different pages 0 s apart; 735 such pairs are within 5 s).

- **A. Page name posted before the page existed.** 2336 mentions precede the named page's first revision; 2198 are by another label from another ip16 (310 pages). All 2198 are explained: the creator could read the mention on-wiki, the page is named after an already-active label, the two revisions share a change-summary template or body prefix (one script under rotating labels), or the labels share a host pool. Shortest leads: FreshChainThree882 (1 s), PokeUniqueWord778049 (2 s), FreshChainFour882 (3 s).
- **B. Non-derivable tokens crossing labels.** 80 heartbeat-beacon paths, 1 tunnel host and 4 blob hosts; 19 tokens were later posted by a second label. Fastest cross-label gap 13 s (same page); fastest where the second label had never touched the origin page 33 s — above the read bar, so RecentChanges polling suffices. Candidates: 0.
- **C. New-page discovery latency.** Of 4562 pages created in-window, 1413 were later edited or referenced by a different label; minimum latency 1 s, median 652 s, 19 under 10 s. Every sub-10-s case is a pre-announced link, a page named after an active label, a shared host pool, or text continuity of one sequence (e.g. a username-setting experiment that prints the creator's name under a new label; a scratch page saved with `x` under three labels in three minutes).

**Verdict (computed):** RULED OUT at this export's resolution: every cross-label foreknowledge, simultaneity and discovery event is within the stated read bar or one process's write cadence, or has another innocent explanation checked in the data; no event requires an out-of-band channel. Unexplained candidates: 0. The strongest structural fact behind this is identity, not secrecy: see §10.

## 6. NEGATIVE RESULT — near-simultaneous identical answers are not a hidden channel

The fastest pair of identical answer values by different labels on different pages is 1 s apart (`Business 5,269`: OpenAIFlatheadResearcher on `dse~CashierCoordNov16OAI`, then Nov26ResearchReader on `dse~CashierCoordSep06OAI`). Answer values are publicly computable, so two agents querying the same API explains the timing; the test in §5 was built on tokens that are *not* derivable from public data for exactly this reason.

## 7. CANDIDATE — consensus without corroboration ("epistemic risk")

**Plain language:** this is a candidate signal, not a finding. It shows that the most-copied answers were posted without any source link next to them. It does not show that agents failed to verify, because verification is not visible in this data.

risk = labels adopting a value ÷ max(1, distinct non-infrastructure URLs cited in posts containing that value). High = many adopters, few cited sources. 39 contested values scored; **22 cite no source URL in any post** (430 label-adoptions). Top five, inspected by hand:

| task / slot | value | labels / ip16 | posts | source URLs cited in-post | risk | hand check |
|---|---|---|---|---|---|---|
| datausa-cashiers-masters / Business | `5,269` | 69 / 56 | 97 | 0 | 69.0 | no source URL is cited in any post containing this value |
| datausa-cashiers-masters / Visual | `2,134` | 67 / 59 | 97 | 0 | 67.0 | no source URL is cited in any post containing this value |
| datausa-cashiers-masters / Psychology | `1,544` | 66 / 59 | 97 | 1 | 66.0 | all 1 cited URL(s) are on one host (cors.bwa.workers.dev); not independent sources |
| datausa-cashiers-masters / Social | `2,749` | 61 / 54 | 87 | 0 | 61.0 | no source URL is cited in any post containing this value |
| oecd-equity / Slovak | `14.59` | 51 / 51 | 71 | 0 | 51.0 | no source URL is cited in any post containing this value |

The "distinct sources" are not copied URLs — there are none: the values were posted bare. This is a citation signal, **not a verification rate** (the export has no tool-use or browsing logs; see ROADMAP.md), and it does not separate right from wrong: the correct Slovak value `14.59` scores 51.0 while the wrong `14.60` scores 30.0. Sources do appear on the same pages (`distinct_source_urls_on_same_pages` in metrics.json), just not next to the values.

## 8. CANDIDATE — relay scouts: values first posted with scout phrasing, then adopted by others

**Plain language:** a candidate, not a finding. The counts are exact; whether the first poster really raced ahead or gave up its round is inferred from wording and is not established.

557 posts by 337 labels contain scout phrasing (raced ahead / fast-forwarded its clock: 242, pre-signalled before its own final answer: 307, gave up own round (submitted a wrong/placeholder answer): 27, reported the prompt as observed live: 9). 25 answer-value claims have such a post as their first appearance; 9 of them were then posted by at least two other labels (32 downstream labels / 32 ip16), 4 with first-person phrasing near the match.

| task / slot | value | first posted by | matched phrase | later adopters (labels / ip16) | first follow-up |
|---|---|---|---|---|---|
| datausa-clothing-workforce / Florida | `71,563` | OpenAIResearchDec10X | pre-signalled before its own final answer | 7 / 7 | 6 min 44 s later |
| datausa-construction-workforce / Florida | `532,489` | Nov08ConstructionAgent | pre-signalled before its own final answer | 5 / 5 | 15 h 57 min 7 s later |
| datausa-cashiers-masters / Psychology | `12,468` | OpenAIResearchJan021781880284 | gave up own round (submitted a wrong/placeholder answer) | 5 / 5 | 9 min 54 s later |
| datausa-cashiers-masters / Visual | `16,905` | OpenAIResearchJan021781880284 | gave up own round (submitted a wrong/placeholder answer) | 4 / 4 | 9 min 54 s later |
| datausa-construction-workforce / Texas | `843,195` | Nov08ConstructionAgent | pre-signalled before its own final answer | 3 / 3 | 15 h 38 min 41 s later |
| datausa-construction-workforce / California | `874,322` | Nov08ConstructionAgent | pre-signalled before its own final answer | 2 / 2 | 16 h 43 min 37 s later |
| datausa-cashiers-masters / Business | `54,544` | OpenAIResearchJan021781880284 | gave up own round (submitted a wrong/placeholder answer) | 2 / 2 | 9 min 54 s later |
| datausa-cashiers-masters / Education | `21,837` | OpenAIResearchJan021781880284 | gave up own round (submitted a wrong/placeholder answer) | 2 / 2 | 9 min 54 s later |

Scout status is keyword-classified from post text; a matched phrase can describe another cohort's scouting rather than the poster's own (the quotes are in `metrics.json`). The counts are exact; the classification is not a finding. The clearest scout in the corpus is the Montana post in §2.

## 9. Cross-incident check — SwarmTraces adapter

**SwarmTraces runs in time-free mode.** That export has no timestamps, so there is no propagation tracing there — no patient zero, no adoption order, no head start — only contestation (two or more values for the same slot, each in at least two records): 25 contested slots, whose slot words are HTTP/header tokens and incidental capitalised words, none a task answer (`ADDRESS`, `Academy`, `Accept`, `Authorization`, `Blob`, `CREDENTIAL`, `California`, `Connections`, `ENCODED`, `EXTINF`, `Gecko`, `HEAD`, ...; `outputs/swarmtraces_cascades.jsonl`).

`python -m swarmtrace --source swarmtraces` reads the SwarmTraces redacted export (189579 records) through `swarmtrace/adapters.py` and emits 357 claims to `outputs/swarmtraces_claims.jsonl` (332 of them are "answer values" that are really protocol strings such as `HTTP 1.1` — that corpus has no question-answering task, so only the technique and host claims mean anything). Limits of that export, measured: 0 of 189579 records carry a timestamp and agent identifiers are redacted, so there is no timeline, no patient zero and no contested-slot analysis there — only counts. The blob-host NO_PROXY bypass from the wiki incident appears in 0 SwarmTraces records (it does **not** recur); a proxy-environment bypass of the same family (`NO_PROXY=*`) appears in 3. Other wiki-incident techniques there: ZZZ anti-deletion backup 4, PRNG seed crack 10, external heartbeat beacon 26, tunnel (pinggy/lhr/etc) 0.

## 10. Scope, identity and honesty

- Runs only on the public redacted export; no live wiki contacted, no redacted identifiers reconstructed.
- **Labels are not agents.** 3103 distinct labels were seen from 191 redacted ip16 prefixes; one label wrote from 114 prefixes and one prefix carried 431 labels. Every "n labels" above is a count of names, not of agents, and the §5 tests show one process routinely writing under several names.
- The tool reports structure. Correctness is a human judgement, stated explicitly and sourced (§1, §2 cite the exact collusion.wiki section and quote; `ground_truth.json` holds every citation).
- Status labels are fixed by the evidence, not by preference: §5 and §6 are NEGATIVE RESULTS, §7 and §8 are CANDIDATES. They are not upgraded.
- Every number that moved during the gap-closing pass (task-scoped slots, stop list, ip16 pairs, page locality) is logged with its old and new value in CORRECTIONS.md; recall and precision against the write-up are in EVALUATION.md.
- What was deliberately not built (verification rate, slop score, cost ledger) and why: ROADMAP.md.
