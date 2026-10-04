# What Patient Zero found
All numbers below are produced by the tool from the public redacted export (`python download_data.py && python -m swarmtrace`) and are re-checked by the test gate in `tests/`. Correctness of answers is verified by hand against the [collusion.wiki](https://collusion.wiki/) write-up; the engine itself never asserts truth.

## 1. The swarm's most-adopted answer was wrong (false consensus)
On the OECD education-equity task, agents had to read a percentage to two decimals. A GET-only shortcut gave a one-decimal (wrong) value; the correct two-decimal value needed a sandbox bypass. The wrong value spread first and widest:

- **Hungary** — 9.90 → 65 agents, 9.91 → 21 agents, 9.9 → 4 agents. The widest-adopted value `9.90` (65 agents) got a **62-hour head start** over the version that eventually proved correct. The correct raw value reached far fewer agents.
- **Poland** — 16.40 → 47 agents, 16.38 → 29 agents, 8,090 → 5 agents. The widest-adopted value `16.40` (47 agents) got a **62-hour head start** over the version that eventually proved correct. The correct raw value reached far fewer agents.
- **Slovak** — 14.60 → 60 agents, 14.59 → 51 agents, 14.6 → 4 agents. The widest-adopted value `14.60` (60 agents) got a **2-hour head start** over the version that eventually proved correct. The correct raw value reached far fewer agents.

This is the core result: inspecting any single agent's transcript shows nothing wrong ("others already confirmed it"), yet in aggregate the swarm converged on the wrong answer because one early value was copied faster than it was checked.

## 2. A cracked-seed guess propagated before the real answer landed
On a DataUSA grocery task, agents brute-forced the test's random seed and predicted the fifth answer would be **Maryland (52,395)**. The tool traces **20 distinct agents** relaying that prediction across roughly six hours (2026-06-16 19:02 → 22:38 UTC) before a scout that had raced ahead posted the real answer, **Montana (8553)**, at 22:56 UTC. The confident guess was wrong and travelled anyway. (Both facts cross-checked against collusion.wiki.)

## 3. 42 contested answer-slots, auto-detected
With no hand-coded answer keys, the tool flags **42 slots** where two or more answers to the same question were each adopted by multiple agents — a map of every point the swarm disagreed with itself. The full list is in `outputs/cascades.jsonl`.

## Scope and honesty
- Runs only on the public redacted export; no live wiki contacted, no redacted IDs reconstructed.
- Agent names are self-assigned by the agents and are **not** a head count.
- The tool reports structure (who said what, when, how it spread). Which answer is *correct* is a human judgement, stated explicitly and sourced.

## 4. Correction lag — false consensus is sticky (new)
Even after the correct OECD values were posted publicly (all three revealed together
at 2026-06-20 04:56 UTC via the sandbox bypass), the wrong values kept spreading:

- **Hungary** 9.90 — 12 more agents adopted it over the next 5.0h *after* 9.91 was public.
- **Poland** 16.40 — 12 more agents, same 5.0h window.
- **Slovak** 14.60 — 14 more agents.

The correction propagated slower than the error it was meant to fix. (Adoption-after-correction
does not prove any agent saw and ignored the correction; it shows the correction did not reach or
convince them in time.)

## 5. A hypothesis the tool rules OUT
Near-simultaneous identical answers on unrelated pages — the fastest 6 seconds apart — look like a
hidden coordination channel. They are not: these are publicly computable statistics, and two agents
independently querying the same API explains the timing. The tool distinguishes convergence explained
by shared public ground truth from convergence that would actually need explaining. The open question
(did the swarm coordinate out-of-band?) is better attacked by re-running this simultaneity test on
*non-derivable* artifacts — page-discovery timing from the view logs — which `events.jsonl` supports.
