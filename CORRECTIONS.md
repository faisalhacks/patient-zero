# Corrections log

Every number that changed because a correctness fix changed the truth, with the old
and new value and why. The gate (`tests/test_reproduces.py`) is updated to the new
true value at the same time — never forced green on a stale number.

Format: `step · what moved · old → new · why`.

## Gap-closing pass, 2026-10-04

(entries are appended below as each step lands)

### STEP B — answer slots keyed by (task, word) instead of the bare word
Why: a bare word merged different questions ("Business 5,269" on the cashiers-with-masters
task vs "Business 54,544" on the cashiers-with-bachelors task; generic words such as
"Expected" merged values from every task). The task is the export's own `page_family`
for the page the post is on (the publishers' classification from page name and body); a
post on a coordination / link-list / unclassified page inherits the one task family in
which the same (word, value) pair appears on task pages, else "unassigned". A page-name
regex (OECD*, Cashier*, ...) was rejected because it cannot separate masters from
bachelors pages and misses OECD evidence pages without "OECD" in the name
(Mar30TooltipEvidence). Five (word, value) pairs with >=2 labels spanned two task
families before the fix; none do after it.

- STEP B · claims extracted · 741 → 746 · pairs that were one claim across two tasks are now one claim per task
- STEP B · contested slots flagged · 42 → 27 · generic-word slots that only looked contested because they merged tasks no longer qualify
- STEP B · named contested slots / artifacts · 28 / 14 → 16 / 11 · same reason; artifacts are now listed as task/word
- STEP B · precision on contested slots (EVALUATION.md) · 28/42 = 0.667 → 16/27 = 0.593 · denominator and numerator both shrank; the remaining artifacts are STEP E's target
- STEP B · risk score: values scored / zero-source / label-adoptions · 122 / 86 / 662 → 69 / 45 / 502 · only task-scoped contested values are scored now
- STEP B · relay scouts: claims with scout first post / relayed by >=2 / downstream / first-person · 24 / 5 / 19 / 0 → 28 / 9 / 32 / 4 · a task-scoped claim can have a different first post than the merged bare-word claim had
- STEP B · OECD false consensus, correction lag, Maryland→Montana, hidden channel, simultaneous answers, identity · unchanged (65/21 labels, 12/12/14/3, 20 labels/21 posts, 0 candidates, 1 s, 3103/191) · every OECD and grocery post resolves to its task page family or inherits it unambiguously
