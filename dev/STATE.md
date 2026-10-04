# Build state
- [x] Core engine (ingest/extract/contradict/cascade) — reproduces 42 contested slots
- [x] Reproducibility gate (tests/test_reproduces.py)
- [x] Correction-lag finding (metrics.json, FINDINGS.md §4) — verified
- [x] Negative result: near-simultaneous answers are NOT a hidden channel (FINDINGS §5)
- [x] ROADMAP.md — records why tool-use/"slop score" was refused (no data for it)
- [x] Results page v1 (patient_zero.html)
- [x] T1-hidden-channel — NEGATIVE RESULT: ruled out at this export's resolution (metrics.json hidden_channel; 0 unexplained candidates; no view logs in export)
- [x] T1-risk-score — CANDIDATE: 86 of 122 contested values cite no source URL in-post (metrics.json risk_score; top 5 inspected: zero sources, not copied URLs)
- [x] T1-relay-scouts — CANDIDATE: 24 claims first posted with scout phrasing, 5 relayed by >=2 other labels, 19 downstream adoptions (metrics.json relay_scouts; keyword-classified, quotes included)
- [x] T1-findings — FINDINGS.md rendered by build_findings.py from metrics.json; gate asserts it is current; statuses: 4 FINDING, 2 NEGATIVE RESULT, 2 CANDIDATE
- [x] T2-adapter — SwarmTraces adapter emits 363 claims (counts only: no timestamps, ids redacted); blob-host bypass does NOT recur, NO_PROXY=* in 3 records (FINDINGS §9)
- [x] T2-store — outputs/store.jsonl grows per run; `python patient_zero.py query <value>` prints a claim's spread (tests/test_tier2.py)
- [x] T3-graph (inferred who-copied-whom SVG per slot) / T3-a11y (keyboard tabs, focus, reduced motion; Lighthouse a11y 1.00) / T3-ci (.github/workflows/gate.yml)
- [x] T-FINALIZE — 2026-10-04: outputs refreshed, FINDINGS.md + patient_zero.html rebuilt, open-check PASS, gate + Tier 2 + page/FINDINGS checks green; VIDEO_SCRIPT.md written

## Gap-closing pass (2026-10-04, after submission) — every number that moved is in CORRECTIONS.md
- [x] STEP A — evaluation vs collusion.wiki ground truth: ground_truth.json (8 cited incidents), outputs/evaluation.json, EVALUATION.md; gated
- [x] STEP B — answer slots keyed by (task family, word); no slot merges two tasks; gate updated to the new truth
- [x] STEP C — every headline count as N labels / M ip16 prefixes (claims carry ip16); FINDINGS + page
- [x] STEP D — correction lag reframed as page locality (in-pipeline, gated): 0 of 41 late wrong adoptions on a page that already showed the correct value
- [x] STEP E — generic tokens stopped in the extractor; 16 contested slots = 15 named / 1 listed artifact (United); precision 15/16
- [x] STEP F — honesty lines: SwarmTraces time-free mode, exact citations per ground-truth value, statuses unchanged
- [x] T-FINALIZE (gap-closing) — 2026-10-04: outputs refreshed, FINDINGS/EVALUATION/page rebuilt, open-check PASS, all gates green, merged to main
