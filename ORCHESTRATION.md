# Build loop for Claude Code — run unattended, finish end-to-end

Goal: finish "Patient Zero" / SwarmTruth for submission AND the METR-audience
write-up — a public repo + a finalized results page + verified findings — without
a human babysitting, and WITHOUT shipping anything fake or broken. The loop stops
only when the gate is green and all packages are done (or a gate fails twice on the
same package -> write BLOCKED.md and stop).

## PRIME DIRECTIVE — no fabrication (this is the whole point)
A result ships ONLY if: (1) it reproduces from the public data by a rerunnable
script, (2) the number is exact (no "about", no "~"), (3) any right/wrong judgement
is cross-checked against collusion.wiki with a citation. Everything else is labeled
a CANDIDATE or a NEGATIVE RESULT — never a finding. Agent names are self-assigned
and are NEVER counted as agents. If a feature needs data we lack (tool-use, memory,
chain-of-thought, cost), DO NOT mock it — it belongs in ROADMAP.md, which already
explains why the tool-use / "slop score" idea was refused.

## GATE (run after EVERY change; revert anything that reddens it)
  python download_data.py && python tests/test_reproduces.py

## LOOP
1. read STATE.md -> pick the next unticked package (Tier 1 before 2 before 3).
2. build on a branch, small commits.
3. run the GATE + the package's acceptance check.
4. green -> merge + tick STATE.md.  red -> fix once; still red -> BLOCKED.md + skip.
5. repeat until all ticked, then run T-FINALIZE, then write a 2-min video script.
Do not ask between packages — the gate is your permission.

## PARALLELIZE
Packages only touch the locked outputs (claims.jsonl / cascades.jsonl / metrics.json),
so analyses, adapters, and the page can be built by parallel subagents. T1-core
lands first because the page and FINDINGS read its fields.

=== TIER 1 — REAL RESULTS (what earns a reaction from METR/Redwood/Grove) ===
T1-hidden-channel  (highest value, highest fabrication risk — hold the bar)
  Using events.jsonl (probe/view logs), test the write-up's open question: did the
  swarm coordinate out-of-band? For each new coordination page, measure how readers
  arrived — via the RecentChanges directory (expected) vs jumping straight to a page
  with no prior listing/link (suggestive). Also re-run cross-page simultaneity on
  NON-derivable artifacts (page names, session ids, technique specifics) — NOT on
  answer values (those are independently lookup-able; see the existing negative
  result). Accept: a ranked CANDIDATE list with, for each, the innocent explanation
  checked. If everything is explainable, report "ruled out" — that is a valid result.
T1-correction-lag  (DONE — in metrics.json/FINDINGS; just keep it green)
T1-risk-score
  Honest "epistemic risk" per contested value = n_agents_adopting /
  max(1, n_distinct_source_urls_cited_for_that_value) within the post text.
  High = many adopters, few independently-cited sources = copying over sourcing.
  VALIDATION REQUIRED: inspect the top 5 by hand; if the "distinct sources" are just
  copied URLs rather than independent, report as a CANDIDATE, not a finding. NEVER
  call this a "verification rate" — we cannot see verification (see ROADMAP.md).
T1-relay-scouts
  Claims first posted by an agent that raced ahead / sacrificed its own round, then
  adopted by others (the self-sacrifice dynamic METR flagged). Accept: list + counts.
T1-findings
  Regenerate FINDINGS.md from the above; every number reproducible; each correctness
  claim links to collusion.wiki. Keep the NEGATIVE result and the ROADMAP honesty.

=== TIER 2 — GENERALITY ===
T2-adapter  events_from_swarmtraces() for
  https://swarmtraces.org/data/final/redacted.jsonl.gz . Accept:
  `python -m swarmtrace --source swarmtraces` emits claims; note in FINDINGS whether
  the blob-host bypass recurs there (cross-incident = strong signal for this audience).
T2-store    append-only outputs/store.jsonl + `patient-zero query <value>` CLI.
  Accept: store grows on a 2nd run; query returns a claim's spread.

=== TIER 3 — INTERFACE (last; invisible to a scrolling researcher) ===
T3-graph  who->who adoption graph for the selected slot in patient_zero.html (self-contained).
T3-a11y   keyboard tabs, focus states, reduced-motion, Lighthouse a11y >= 90.
T3-ci     GitHub Action running the gate on push.

=== T-FINALIZE (run after all tiers; produces the final page+results end-to-end) ===
1. python -m swarmtrace                      # refresh claims/cascades/metrics
2. regenerate outputs/page_data.json from the latest outputs (top contested slots +
   correction-lag + the verified Maryland->Montana case + any new cleared findings)
3. rebuild patient_zero.html embedding the refreshed page_data.json
4. open-check: page loads with no console errors, self-contained (no external JS)
5. run the GATE once more; everything green
6. print: live-page path, repo status, ticked packages, and the exact FINDINGS numbers

## HARD RULES (unchanged)
Public redacted data only; never contact the live wiki; never un-redact IDs; no
secrets; engine reports structure, correctness is hand-checked and sourced
(correct_value stays null in code).

## WHEN DONE
Human pushes to GitHub, enables Pages (or drops patient_zero.html on Netlify), and
fills the Airtable form IN THEIR OWN WORDS (Pangram checks form text only; code and
video may be AI-built).
