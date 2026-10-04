# Patient Zero

**Tracing how a claim spreads through an AI agent swarm.**
Built for the [AI Swarm Dynamics Hackathon](https://swarmchasing.com/) (AI Village × Grove Research), October 2026.

When thousands of autonomous agents coordinate, the dangerous failures don't live
inside any single agent's transcript — they live *between* agents: a wrong answer
copied faster than it's checked, confidence rising while the independent evidence
behind it never grows. Patient Zero reads a timestamped multi-agent log and, for
every repeatable claim (an answer, a technique, a shared URL), shows **who posted
it first, how fast others adopted it, and whether the version that spread widest
was even correct.**

➡️ **Live results page:** `patient_zero.html` (open it, pick a slot, hit *Replay the spread*).
➡️ **What it found:** [`FINDINGS.md`](FINDINGS.md) — every number labelled FINDING, CANDIDATE or NEGATIVE RESULT, every headline count given as *N labels / M ip16 prefixes*.
➡️ **How well it finds what experts found:** [`EVALUATION.md`](EVALUATION.md) — recall against the hand-written [collusion.wiki](https://collusion.wiki/) write-up and precision on contested slots.
➡️ **Every number that moved, and why:** [`CORRECTIONS.md`](CORRECTIONS.md).
➡️ **What it refused to build, and why:** [`ROADMAP.md`](ROADMAP.md).

## Run it in two minutes (no dependencies)

```bash
python download_data.py          # fetch the public redacted export, verify checksums
python -m swarmtrace             # -> outputs/claims.jsonl, cascades.jsonl, metrics.json, evaluation.json (+ appends to outputs/store.jsonl)
python tests/test_reproduces.py  # the gate: every finding, metric, recall/precision figure and the rendered write-ups reproduce
```

Pure Python 3.9+ standard library. Then open `patient_zero.html` in a browser.

More:

```bash
python patient_zero.py query 9.90 --slot Hungary     # how did this value spread? (reads outputs/store.jsonl)
python build_findings.py                             # re-render FINDINGS.md and EVALUATION.md from the outputs
python build_page.py                                 # regenerate outputs/page_data.json and rebuild patient_zero.html
python download_data.py --swarmtraces                # also fetch the SwarmTraces redacted export (15 MB, sha256 pinned)
python -m swarmtrace --source swarmtraces            # cross-incident run, TIME-FREE MODE (see below)
python tests/test_tier2.py                           # adapter + store acceptance
```

## How it works

1. **Ingest** — a tiny adapter turns log rows into normalized events
   `{time, agent, where, text, family, ip16}`. A wiki adapter ships in `swarmtrace/core.py`; a
   SwarmTraces adapter in `swarmtrace/adapters.py`; add `events_from_<source>()` for
   any other timestamped log.
2. **Extract** — pull repeatable claims: answer values, named techniques, URLs.
   Answer slots are keyed by **(task, word)**, where the task is the export's own
   `page_family` for the page (with an unambiguous-inheritance fallback for
   coordination pages), so "Business 5,269" on one task never merges with
   "Business 54,544" on another. Generic status/format tokens are stopped.
3. **Trace** — per claim: first appearance, **patient zero**, and the ordered
   adoption timeline, with both the label and the redacted ip16 prefix of each adopter.
4. **Contradict** — flag a *contested slot* when two+ answers to the same (task, slot)
   were each adopted by multiple labels, and surface which value won on adoption
   versus which came first (the **false-consensus** signal).
5. **Analyse** (`swarmtrace/analyses.py`, `hidden_channel.py`, `risk.py`, `relay.py`,
   `evaluation.py`) — page-local correction lag, the hidden-channel tests, the
   consensus-without-corroboration score, the relay-scout list and the ground-truth
   evaluation, all written to `outputs/metrics.json` / `outputs/evaluation.json` with
   their definitions, bars and the innocent explanations that were checked.

**The engine reports structure; it never decides what is true.** Which answer is
correct is checked by hand against a cited collusion.wiki section and stated as such.

## Output contract (stable)

Everything downstream reads these files, so the page, the write-up and new dataset
adapters can be built in parallel without touching the engine:

- `outputs/claims.jsonl` — one claim per line: `claim_id, kind, task, slot, value,
  first_seen, patient_zero, n_agents, n_ip16, agents[], ip16_first_seen[[time,ip16]],
  pages[], adoption[[time,agent,where,ip16]]`.
- `outputs/cascades.jsonl` — one contested (task, slot) per line: `task, slot, values[{value,
  n_agents, n_ip16, first_seen, patient_zero}], false_consensus{earliest_value, widest_value,
  widest_agents, widest_ip16, head_start_hours, correct_value:null}`.
- `outputs/metrics.json` — every analysed number, with definitions; `outputs/evaluation.json` —
  recall/precision against `ground_truth.json`. `FINDINGS.md`, `EVALUATION.md` and
  `patient_zero.html` are rendered from these.
- `outputs/store.jsonl` — append-only record of every run; `patient_zero.py query` reads it.

**Counting convention.** `n_agents` means *distinct self-assigned labels*; `n_ip16` means
*distinct redacted ip16 prefixes among the same posts*. Neither is an agent identity: the
export shows 3,103 labels writing from 191 prefixes, one label from as many as 114 of them.
Every headline number is therefore given both ways.

## SwarmTraces: time-free mode

The public [SwarmTraces](https://swarmtraces.org/) redacted export carries **no
timestamps** and redacted agent identifiers. The adapter therefore runs in
**time-free mode**: it extracts claims and reports *contestation only* (two or more
values for the same slot, each in at least two records). There is **no propagation
tracing** there — no patient zero, no adoption order, no head start — and its
"answer values" are protocol strings (e.g. `HTTP 1.0` vs `1.1`) because that corpus has
no question-answering task. Only the technique and host claims carry meaning
(FINDINGS §9).

## Data & ethics

Runs only on the **public, redacted** [collusion.wiki](https://collusion.wiki/)
export of DSEWiki agent edits (24 May – 2 Jul 2026). No live wiki is contacted and
no redacted identifiers are reconstructed. Agent names in the data are
self-assigned and are **not** a head count.

## Credits

Dataset: Nightingale Collective and collaborators (collusion.wiki). Hackathon:
AI Village (AI Digest) × Grove Research.
