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
➡️ **What it found:** [`FINDINGS.md`](FINDINGS.md) — every number labelled FINDING, CANDIDATE or NEGATIVE RESULT.
➡️ **What it refused to build, and why:** [`ROADMAP.md`](ROADMAP.md).

## Run it in two minutes (no dependencies)

```bash
python download_data.py          # fetch the public redacted export, verify checksums
python -m swarmtrace             # -> outputs/claims.jsonl, cascades.jsonl, metrics.json (+ appends to outputs/store.jsonl)
python tests/test_reproduces.py  # the gate: confirms every finding and metric reproduces
```

Pure Python 3.9+ standard library. Then open `patient_zero.html` in a browser.

More:

```bash
python patient_zero.py query 9.90 --slot Hungary     # how did this value spread? (reads outputs/store.jsonl)
python build_findings.py                             # re-render FINDINGS.md from outputs/metrics.json
python build_page.py                                 # regenerate outputs/page_data.json and rebuild patient_zero.html
python download_data.py --swarmtraces                # also fetch the SwarmTraces redacted export (15 MB)
python -m swarmtrace --source swarmtraces            # cross-incident run -> outputs/swarmtraces_claims.jsonl + summary
```

## How it works

1. **Ingest** — a tiny adapter turns log rows into normalized events
   `{time, agent, where, text}`. A wiki adapter ships in `swarmtrace/core.py`; a
   SwarmTraces adapter in `swarmtrace/adapters.py`; add `events_from_<source>()` for
   any other timestamped log.
2. **Extract** — pull repeatable claims: answer values, named techniques, URLs.
3. **Trace** — per claim: first appearance, **patient zero**, and the ordered
   adoption timeline.
4. **Contradict** — flag a *contested slot* when two+ answers to the same question
   were each adopted by multiple labels, and surface which value won on adoption
   versus which came first (the **false-consensus** signal).
5. **Analyse** (`swarmtrace/analyses.py`, `hidden_channel.py`, `risk.py`, `relay.py`) —
   correction lag, the hidden-channel tests, the consensus-without-corroboration
   score and the relay-scout list, all written to `outputs/metrics.json` with their
   definitions, bars and the innocent explanations that were checked.

**The engine reports structure; it never decides what is true.** Which answer is
correct is checked by hand and stated with a source.

## Output contract (stable)

Everything downstream reads these files, so the page, the write-up and new dataset
adapters can be built in parallel without touching the engine:

- `outputs/claims.jsonl` — one claim per line: `claim_id, kind, slot, value,
  first_seen, patient_zero, n_agents, agents[], pages[], adoption[[time,agent,where]]`.
- `outputs/cascades.jsonl` — one contested slot per line: `slot, values[],
  false_consensus{earliest_value, widest_value, head_start_hours, correct_value:null}`.
- `outputs/metrics.json` — every analysed number, with definitions; `FINDINGS.md`
  and `patient_zero.html` are rendered from it.
- `outputs/store.jsonl` — append-only record of every run (one `run` line, one
  `claim` line per claim); `patient_zero.py query` reads it.

`n_agents` everywhere means *distinct self-assigned labels*. The export shows
3,103 labels writing from 191 redacted ip16 prefixes, one label from as many as
114 prefixes — neither is an agent identity.

## Data & ethics

Runs only on the **public, redacted** [collusion.wiki](https://collusion.wiki/)
export of DSEWiki agent edits (24 May – 2 Jul 2026). No live wiki is contacted and
no redacted identifiers are reconstructed. Agent names in the data are
self-assigned and are **not** a head count. The cross-incident run uses the public
[SwarmTraces](https://swarmtraces.org/) redacted export, which has no timestamps
and redacted agent ids, so only counts are reported from it.

## Credits

Dataset: Nightingale Collective and collaborators (collusion.wiki). Hackathon:
AI Village (AI Digest) × Grove Research.
