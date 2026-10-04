# Patient Zero

**Tracing how a claim spreads through an AI agent swarm — who posted it first, how fast others copied it, and whether the version that won was even correct.**

➡️ **Live results page:** https://faisalhacks.github.io/patient-zero/
➡️ Built for the [AI Swarm Dynamics Hackathon](https://swarmchasing.com/) (AI Village × Grove Research), October 2026, on the public, redacted [collusion.wiki](https://collusion.wiki/) export of DSEWiki agent edits.

## Two headline findings (gated, exact; counts given as labels / ip16 prefixes)

1. **The swarm's most-adopted OECD answer was the wrong one, and the correction was page-local.**
   Hungary: the padded value `9.90` reached **65 labels / 52 ip16**; the correct `9.91` (hand-checked against collusion.wiki) reached **21 / 27** and was first posted **5 h 30 min 46 s** later. After the correction was public, **12 / 6** more adopted the wrong value — and **0 of 41** such late adoptions (across Hungary, Poland, Slovak, Czech) happened on a page that already showed the correct value. The fix stayed where it was posted; the error kept spreading elsewhere.
2. **A cracked-seed guess travelled before the real answer landed.**
   **20 labels / 13 ip16** relayed the predicted "Maryland = 52,395" in 21 posts; the real answer, Montana = 8553, was posted by a scout that had raced ahead **18 min 6 s** after the last relay, then by 7 labels / 9 ip16.

**Evaluation against the hand-written write-up:** recall **6 / 8** of collusion.wiki's documented incidents surfaced automatically (8 / 8 with hand-written technique patterns); precision on contested slots **15 / 16**. Two further results are deliberately labelled: *no out-of-band channel* and *no simultaneity signal* are **NEGATIVE RESULTS**; *consensus without corroboration* (22 of 39 contested values cite no source) and *relay scouts* are **CANDIDATES**, not findings.

- [FINDINGS.md](FINDINGS.md) — every result, labelled FINDING / CANDIDATE / NEGATIVE RESULT, with citations
- [EVALUATION.md](EVALUATION.md) — recall and precision against ground truth ([ground_truth.json](ground_truth.json))
- [CORRECTIONS.md](CORRECTIONS.md) — every number that moved during review, old → new, and why
- [ROADMAP.md](ROADMAP.md) — what was deliberately not built (verification rate, slop score) and why

## Run it (three commands, standard library only, Python 3.9+)

```bash
python download_data.py          # fetch the public redacted export, verify checksums
python -m swarmtrace             # -> outputs/claims.jsonl, cascades.jsonl, metrics.json, evaluation.json
python tests/test_reproduces.py  # the gate: every finding, metric and write-up reproduces, or it fails
```

Then open `patient_zero.html` (or `index.html`, the same file). `python patient_zero.py query 9.90 --slot Hungary` prints how a value spread.

## Honesty notes

- Labels are self-assigned names and the redacted ip16 prefix is not an identity either (3,103 labels wrote from 191 prefixes). Nothing on this page is a head count.
- The engine reports structure; correctness is a human judgement, stated and cited (FINDINGS §1, §2).
- The SwarmTraces cross-incident run is **time-free** (that export has no timestamps): contestation only, no propagation tracing.
- Public redacted data only; no live wiki contacted; no identifiers reconstructed.

## Build notes

Scaffolding for the autonomous build loop lives in [`dev/`](dev/): [ORCHESTRATION.md](dev/ORCHESTRATION.md) (the loop), [STATE.md](dev/STATE.md) (package ticks), [VIDEO_SCRIPT.md](dev/VIDEO_SCRIPT.md), `build_findings.py` / `build_page.py` (render FINDINGS.md, EVALUATION.md and the page from the outputs), `check_stale.py`. The GitHub Action in `.github/workflows/gate.yml` reruns the full gate on every push.

Dataset: Nightingale Collective and collaborators (collusion.wiki). License: MIT.
