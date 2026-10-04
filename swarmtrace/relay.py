"""
T1-relay-scouts — claims first posted by an agent that raced ahead or gave up its
own round, then adopted by others (the self-sacrifice dynamic).

The export shows posts, not intentions, so a "scout" is identified ONLY by what the
post itself says. Classification is keyword-based over the patient-zero post of each
answer-value claim; every matched phrase is quoted next to the row so a reader can
disagree. Status: CANDIDATE (self-reported, keyword-classified), with exact counts.
"""
from __future__ import annotations
import re, collections
from datetime import datetime

ISO = "%Y-%m-%dT%H:%M:%SZ"
def _t(s): return datetime.strptime(s, ISO)
def _sec(a, b): return int((_t(b) - _t(a)).total_seconds())

SCOUT_RX = {
    "gave up own round (submitted a wrong/placeholder answer)":
        re.compile(r"submit(?:ted|ting)? (?:a |an )?(?:wrong|placeholder|dummy|guess|blank|random|arbitrary|junk)|wrong estimate|wrong guess", re.I),
    "pre-signalled before its own final answer":
        re.compile(r"pre-?signal|signal(?:l?ed)?[^.\n]{0,40}before (?:my |the |our )?final|before (?:my |the |our )?final answer", re.I),
    "raced ahead / fast-forwarded its clock":
        re.compile(r"\brac(?:ed|ing)\b|fast[- ]forward|fast[- ]?(?:tier|cohort)|ahead of (?:the |my |your |)(?:sequence|round|us|you)", re.I),
    "reported the prompt as observed live":
        re.compile(r"prompt observed|observed (?:the )?prompt|seen live|observed live|genuinely observed", re.I),
}

def _match(text):
    out = []
    for kind, rx in SCOUT_RX.items():
        m = rx.search(text)
        if m:
            i = m.start(); window = text[max(0, i - 70): i + 90]
            out.append({"kind": kind, "quote": window.replace("\n", " | "),
                        "first_person_nearby": bool(FIRST_PERSON.search(window))})
    return out

FIRST_PERSON = re.compile(r"\b(?:I|we|our|us|my|me)\b")

def run(events, claims, min_downstream=2, exclude_slots=()):
    by_rev = {}
    for e in events: by_rev[(e["time"], e["agent"], e["where"])] = e
    # scout posts overall (any post, any claim)
    scout_posts = [(e, _match(e["text"])) for e in events]
    scout_posts = [(e, ms) for e, ms in scout_posts if ms]
    per_kind = collections.Counter(m["kind"] for _, ms in scout_posts for m in ms)
    rows = []
    for c in claims:
        if c["kind"] != "answer_value" or c["slot"] in exclude_slots or c["slot"].isupper(): continue
        pz = c["adoption"][0]                     # [time, label, page] of the first post
        e = by_rev.get((pz[0], pz[1], pz[2]))
        if not e: continue
        ms = _match(e["text"])
        if not ms: continue
        later = c["adoption"][1:]
        rows.append({"slot": c["slot"], "value": c["value"], "scout_label": pz[1], "scout_page": pz[2],
                     "first_seen": pz[0], "scout_phrases": ms,
                     "first_person_self_report": any(m["first_person_nearby"] for m in ms),
                     "downstream_labels": len(later),
                     "seconds_to_first_downstream": _sec(pz[0], later[0][0]) if later else None,
                     "seconds_to_last_downstream": _sec(pz[0], later[-1][0]) if later else None,
                     "downstream_pages": len({a[2] for a in later})})
    rows.sort(key=lambda r: (-r["downstream_labels"], r["first_seen"], r["slot"], r["value"]))
    relayed = [r for r in rows if r["downstream_labels"] >= min_downstream]
    return {
        "definition": "answer-value claims whose FIRST post self-reports racing ahead / giving up its round / "
                      "pre-signalling / observing the prompt live (regexes in swarmtrace/relay.py), and the "
                      "number of other labels that later posted the same value",
        "scout_posts_total": len(scout_posts),
        "labels_posting_scout_phrases": len({e["agent"] for e, _ in scout_posts}),
        "scout_posts_per_kind": dict(per_kind),
        "claims_with_scout_patient_zero": len(rows),
        f"claims_relayed_by_at_least_{min_downstream}_other_labels": len(relayed),
        "downstream_adoptions_total": sum(r["downstream_labels"] for r in relayed),
        "relayed_claims_with_first_person_self_report": sum(1 for r in relayed if r["first_person_self_report"]),
        "excluded_generic_word_slots": sorted(exclude_slots) + ["<any ALL-CAPS slot>"],
        "top": relayed[:25],
        "status": "CANDIDATE — scout status is keyword-classified from post text; a matched phrase can describe "
                  "another cohort's scouting rather than the poster's own (see first_person_self_report); "
                  "counts are exact, the classification is not",
    }
