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

### STEP C — every headline count reported two ways (labels / ip16 prefixes)
Why: neither the self-assigned label nor the redacted ip16 prefix is an agent identity,
so each headline number is now given as "N labels / M ip16", both from the same
extraction (claims.jsonl carries `n_ip16`, `ip16_first_seen`, and the ip16 of each
adoption record). No existing number moved; the ip16 figures are additions:

- STEP C · Hungary 9.90 (wrong) / 9.91 (correct) · 65 / 21 labels → 65 labels / 52 ip16 and 21 labels / 27 ip16 · a label can post from several prefixes, so ip16 can exceed labels
- STEP C · Poland 16.40 / 16.38 · 47 / 29 labels → 47 / 34 ip16 and 29 / 34 ip16
- STEP C · Slovak 14.60 / 14.59 · 60 / 51 labels → 60 / 46 ip16 and 51 / 51 ip16
- STEP C · Czech 9.70 / 9.69 · 19 / 18 labels → 19 / 19 ip16 and 18 / 16 ip16
- STEP C · new wrong adopters after the correction (Hungary / Poland / Slovak / Czech) · 12 / 12 / 14 / 3 labels → 6 / 7 / 6 / 3 ip16 prefixes whose first post of the wrong value came after the correction
- STEP C · Maryland relays · 20 labels → 20 labels / 13 ip16; Montana posts 7 labels / 9 ip16
- STEP C · risk top five · 69 / 67 / 66 / 61 / 51 labels → 56 / 59 / 59 / 54 / 51 ip16
- STEP C · relay-scout downstream adoptions · 32 labels → 32 labels / 32 ip16
