# What we deliberately did NOT build (and why)

Scalable-oversight ideas that sound great but need data this public export does
not contain. We list them so the limits are explicit — building them here would
mean fabricating signals, which this project refuses to do.

## Not built: verification-rate / "slop score" / tool-use tracking
Tempting framing: "flag agents that copy an answer without verifying it." But the
collusion.wiki export is **wiki revisions only**. We never see the agents' tool
calls, web searches, or chain-of-thought. There is no way, from this data, to know
whether an agent verified an answer before copying it. Any "tool-use rate" or
"slop score" computed here would be invented. If you see those numbers in a swarm
write-up built on this dataset, they are not real.

## Not built: config-layer loop + cost/effort ledger
The "catch a repeated mistake -> patch shared config (skill.md) -> replay-gated
regression test -> human gate" loop, plus a token/cost ledger and effort routing.
These need logs with config files, agent memory, chain-of-thought, and token costs.
Not present in this export.

## Where these become real
- The **AI Village dataset** (manual-approval on Hugging Face) has computer-use
  turns and agent messages — enough to measure some verification behaviour directly.
- OpenAI's **unreleased Hugging Face transcripts** contain chain-of-thought.
With either, the same engine extends to measure verification, not just propagation.

Until then we report only what the data supports: who said what, when, how it
spread, and whether it was later contradicted — with every number reproducible.
