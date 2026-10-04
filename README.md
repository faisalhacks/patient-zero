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
➡️ **What it found:** [`FINDINGS.md`](FINDINGS.md).

## Run it in two minutes (no dependencies)

```bash
python download_data.py          # fetch the public redacted export, verify checksums
python -m swarmtrace             # -> outputs/claims.jsonl, outputs/cascades.jsonl
python tests/test_reproduces.py  # the gate: confirms the findings reproduce
```

Pure Python 3.9+ standard library. Then open `patient_zero.html` in a browser.

## How it works

1. **Ingest** — a tiny adapter turns log rows into normalized events
   `{time, agent, where, text}`. A wiki adapter ships in `swarmtrace/core.py`;
   add `events_from_<source>()` for any other timestamped log.
2. **Extract** — pull repeatable claims: answer values, named techniques, URLs.
3. **Trace** — per claim: first appearance, **patient zero**, and the ordered
   adoption timeline.
4. **Contradict** — flag a *contested slot* when two+ answers to the same question
   were each adopted by multiple agents, and surface which value won on adoption
   versus which came first (the **false-consensus** signal).

**The engine reports structure; it never decides what is true.** Which answer is
correct is checked by hand and stated with a source.

## Output contract (stable)

Everything downstream reads two files, so the frontend, reports, and new dataset
adapters can be built in parallel without touching the engine:

- `outputs/claims.jsonl` — one claim per line: `claim_id, kind, slot, value,
  first_seen, patient_zero, n_agents, agents[], pages[], adoption[[time,agent,where]]`.
- `outputs/cascades.jsonl` — one contested slot per line: `slot, values[],
  false_consensus{earliest_value, widest_value, head_start_hours, correct_value:null}`.

## Data & ethics

Runs only on the **public, redacted** [collusion.wiki](https://collusion.wiki/)
export of DSEWiki agent edits (24 May – 2 Jul 2026). No live wiki is contacted and
no redacted identifiers are reconstructed. Agent names in the data are
self-assigned and are **not** a head count. Also works on other public multi-agent
corpora (e.g. [SwarmTraces](https://swarmtraces.org/)) via a new adapter.

## Credits

Dataset: Nightingale Collective and collaborators (collusion.wiki). Hackathon:
AI Village (AI Digest) × Grove Research.
