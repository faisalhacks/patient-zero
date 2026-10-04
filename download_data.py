#!/usr/bin/env python3
"""Fetch the public, redacted collusion.wiki export and verify checksums.
Usage: python download_data.py [--swarmtraces]
Downloads to ./data/ . This is the same data the write-up was built on; no
login, and no contact with the live wiki. --swarmtraces also fetches the public
SwarmTraces redacted export (15 MB) used by `python -m swarmtrace --source swarmtraces`."""
import hashlib, pathlib, sys, urllib.request, zipfile
URL = "https://collusion.wiki/explorer/download/full-wiki-logs.zip"
SUMS = {  # sha256 of the expanded files, from collusion.wiki/explorer/download
 "revisions.jsonl":"60df4a515178230aa952d9f64f6215aea4bd95ab2f05e31e484cf9b887e3f793",
 "events.jsonl":"588584295f1c4a7c3d90b04075ab151504f165ff069534d935cda08853ec28b1",
 "pages.jsonl":"92b296170b496b836cdf5ef783bed9465d2d75db7e1a0becec1c36c8b7c42cfd",
 "labels.jsonl":"d94aecd84baecda46344f5b8726a95a9c81e7e41a1c0969fc89a90c8906f0388"}
SWARMTRACES_URL = "https://swarmtraces.org/data/final/redacted.jsonl.gz"
SWARMTRACES_FILE = "swarmtraces_redacted.jsonl.gz"
# sha256 pinned at first fetch (2026-10-04); a mismatch means the upstream file changed and the
# cross-incident numbers in FINDINGS.md §9 must be re-derived before they are quoted again.
SWARMTRACES_SHA256 = "7b66ab21674de52fcd3f557652f68b1801170c998e2f266862124e6edf283488"

def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    d = pathlib.Path("data"); d.mkdir(exist_ok=True)
    z = d/"full-wiki-logs.zip"
    print("downloading", URL)
    urllib.request.urlretrieve(URL, z)
    zipfile.ZipFile(z).extractall(d)
    ok = True
    for name, want in SUMS.items():
        got = _sha(d/name)
        tick = "ok" if got == want else "MISMATCH"
        if got != want: ok = False
        print(f"  {tick}  {name}")
    if "--swarmtraces" in sys.argv:
        g = d/SWARMTRACES_FILE
        if not (g.exists() and _sha(g) == SWARMTRACES_SHA256):
            print("downloading", SWARMTRACES_URL)
            urllib.request.urlretrieve(SWARMTRACES_URL, g)
        got = _sha(g); tick = "ok" if got == SWARMTRACES_SHA256 else "MISMATCH"
        if got != SWARMTRACES_SHA256: ok = False
        print(f"  {tick}  {SWARMTRACES_FILE}")
    sys.exit(0 if ok else 1)
if __name__ == "__main__":
    main()
