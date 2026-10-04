#!/usr/bin/env python3
"""Guard against stale numbers in what judges see first (index.html, patient_zero.html,
README.md). Every pattern below is a figure from a superseded version of the write-up; the
gated values live in FINDINGS.md / outputs/metrics.json. Exit 1 on any hit."""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = ["index.html", "patient_zero.html", "README.md"]
STALE = {
    "42 as the contested-slot count": r"\b42\b[^<\n]{0,30}\b(?:contested|slots)\b|\b(?:contested|slots)\b[^<\n]{0,30}\b42\b|\"contested_slots\":\s*42\b",
    "741 claims": r"\b741\b",
    "62-hour head start": r"\b62[- ]?(?:hour|h\b)",
    "'six hours' (Maryland span)": r"six hours",
    "'6 seconds' (simultaneity)": r"\b6 seconds",
    "86 of 122 (risk score)": r"86 of 122",
    "the word 'agents' used as a count": r"\b(?:\d[\d,]*|thousands of|hundreds of|dozens of|many|several)\s+(?:autonomous\s+|OpenAI\s+)?agents\b",
}

def main():
    bad = 0
    for fn in FILES:
        p = ROOT / fn
        if not p.exists(): print(f"{fn}: missing"); bad += 1; continue
        s = p.read_text(encoding="utf-8")
        hits = []
        for name, rx in STALE.items():
            for m in re.finditer(rx, s, re.I):
                i = m.start(); hits.append((name, s[max(0, i - 60): i + 60].replace("\n", " ")))
        print(f"{fn}: {'OK, no stale numbers' if not hits else str(len(hits)) + ' stale hit(s)'}")
        for name, ctx in hits: print(f"   [{name}] ...{ctx}..."); bad += 1
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
