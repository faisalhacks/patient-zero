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

### STEP D — correction lag reframed as page locality
Why: "N labels adopted the wrong value after the correction" invited the reading that
agents ignored a visible correction. The in-pipeline check (`metrics.json page_locality`)
looks at the previous published revision of the page each late adopter edited, with the
same extractor, and asks whether the correct value was already displayed there.

- STEP D · late wrong adoptions on a page that already showed the correct value (Hungary / Poland / Slovak / Czech) · (new) → 0 / 0 / 0 / 0 of 12 / 12 / 14 / 3 · the correction stayed on the pages it was posted to
- STEP D · late wrong adoptions on a page where the correct value had ever been posted earlier · (new) → 0 / 0 / 0 / 0
- STEP D · pages carrying the wrong / the correct / both values · (new) → Hungary 52 / 23 / 8, Poland 49 / 33 / 11, Slovak 52 / 51 / 21, Czech 11 / 13 / 1
- STEP D · FINDINGS §4 and the page's results section now use the page-locality framing and no longer imply that anyone ignored a visible correction; the 12 / 12 / 14 / 3 counts are unchanged

### STEP E — generic tokens stopped in the extractor; precision stated
Why: the extractor keyed slots by any capitalised word before a number, so status words
(Answered, Expected, CONFIRMED, Correct, Matching), format tokens (SDMX, XLSX), fragments of
real names (Performing, Sciences, Primary) and similar were counted as contested slots.
They are now in `core.STOP`. One ambiguous slot remains and is listed as an artifact
instead of hidden: `oecd-equity/United` merges United Kingdom 38.3 and United States 24.2
(a truncated multi-word name).

- STEP E · claims extracted · 746 → 561 · stopped tokens no longer produce claims
- STEP E · contested slots flagged · 27 → 16 · all 11 generic-word artifacts gone
- STEP E · named slots / artifacts · 16 / 11 → 15 / 1 · `United` reclassified from named to artifact (truncated multi-word name)
- STEP E · precision on contested slots · 16/27 = 0.593 → 15/16 = 0.938
- STEP E · risk score: values scored / zero-source / label-adoptions · 69 / 45 / 502 → 39 / 22 / 430 · only values of the 16 remaining contested slots are scored
- STEP E · relay scouts: claims with scout first post · 28 → 25 · three stopped-token claims dropped; relayed / downstream / first-person unchanged at 9 / 32 / 4
- STEP E · OECD false consensus, correction lag, page locality, Maryland→Montana, hidden channel, simultaneous answers, identity, recall · unchanged
- STEP E · SwarmTraces adapter claims (cross-incident, FINDINGS §9) · 363 (338 protocol-string "answer values") → 357 (332) · the same stop list applies to that corpus; url 21 and technique 4 claims unchanged, blob-host bypass still does not recur, NO_PROXY=* still 3 records

### T-FINALIZE (gap-closing) — final state, 2026-10-04
Gate green on the new truth (tests/test_reproduces.py, tests/test_tier2.py, build_page.py --check,
build_findings.py --check, tests/check_page.py). Final headline numbers, labels / ip16:
Hungary 9.90 65 / 52 vs 9.91 21 / 27; Poland 16.40 47 / 34 vs 16.38 29 / 34; Slovak 14.60 60 / 46 vs
14.59 51 / 51; Czech 9.70 19 / 19 vs 9.69 18 / 16; late wrong adopters 12 / 6, 12 / 7, 14 / 6, 3 / 3, of
which 0 on a page already showing the correct value; Maryland relays 20 / 13 (21 posts), Montana posts
7 / 9; recall 6/8 automatic, 8/8 with hand-written patterns; precision 15/16 on 16 contested
(task, slot) pairs; risk 22 of 39 values with zero cited sources (430 label-adoptions); relay scouts
25 claims, 9 relayed by >= 2 others, 32 / 32 downstream; hidden channel 0 unexplained candidates.
