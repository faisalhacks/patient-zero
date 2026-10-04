# Patient Zero — 2-minute video script

Target length: 2:00 at a normal speaking pace (about 300 words). Every number is
read off `FINDINGS.md`, which is rendered from `outputs/metrics.json`; nothing in
the narration is estimated. Screen directions are in brackets.

---

**[0:00 – 0:15] Open on `patient_zero.html`, Hungary tab selected, replay running.**

Thousands of wiki edits. One question: when an answer spreads through a swarm of
agents, who posted it first, and was it even right?

This is Patient Zero. It reads the public, redacted collusion.wiki export and traces
every repeatable claim through the swarm.

**[0:15 – 0:45] Adoption race, Hungary. Point at the two curves, then the verdict card.**

Here is the OECD Hungary question. The orange value, 9.90, is the one the swarm
adopted: sixty-five labels. The correct value, 9.91, was posted five hours, thirty
minutes and forty-six seconds later and reached twenty-one. Every single transcript
looks fine — "other cohorts confirmed it." The mistake only exists between the
agents.

**[0:45 – 1:05] Scroll to the results section: Correction lag table.**

And it is sticky. After the correct value was public, twelve more labels still
adopted the wrong one for Hungary, twelve for Poland, fourteen for the Slovak
Republic. The correction travelled slower than the error.

**[1:05 – 1:25] Verified case timeline: Maryland ticks, Montana marker.**

Same shape on a different task. Twenty labels relayed a seed-cracked guess,
Maryland, in twenty-one posts. The real answer, Montana, arrived eighteen minutes
and six seconds after the last relay — from a scout that had raced ahead to see it.

**[1:25 – 1:45] Results section: the NEGATIVE RESULT and CANDIDATE badges.**

We also say what we could not show. Did the swarm coordinate off the wiki? We
tested it three ways with stated bars and found zero events the data cannot
explain — a negative result, labelled as such. And the most-copied answers were
posted with no source link at all: eighty-six of one hundred twenty-two contested
values. That is a candidate signal, not a verification rate, because verification
is not visible in this data.

**[1:45 – 2:00] Terminal: `python download_data.py && python -m swarmtrace && python tests/test_reproduces.py` → GATE PASS.**

Three commands reproduce every number from the public export, and the gate fails
if any of them drifts. Labels are self-assigned names, not agents, and the page
says so. Patient Zero: structure first, truth checked by hand, and nothing made up.

---

### Numbers quoted (all from FINDINGS.md)
| quoted | value | source |
|---|---|---|
| Hungary wrong vs correct labels | 65 vs 21 | §1 |
| correct value posted after wrong | 5 h 30 min 46 s | §1 |
| new wrong adopters after correction (Hungary / Poland / Slovak) | 12 / 12 / 14 | §4 |
| Maryland relays | 20 labels, 21 posts | §2 |
| Montana after last relay | 18 min 6 s | §2 |
| hidden-channel unexplained candidates | 0 | §5 |
| contested values with zero cited sources | 86 of 122 | §7 |
