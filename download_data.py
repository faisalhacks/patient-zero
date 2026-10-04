#!/usr/bin/env python3
"""Fetch the public, redacted collusion.wiki export and verify checksums.
Usage: python download_data.py
Downloads to ./data/ . This is the same data the write-up was built on; no
login, and no contact with the live wiki."""
import hashlib, pathlib, sys, urllib.request, zipfile
URL = "https://collusion.wiki/explorer/download/full-wiki-logs.zip"
SUMS = {  # sha256 of the expanded files, from collusion.wiki/explorer/download
 "revisions.jsonl":"60df4a515178230aa952d9f64f6215aea4bd95ab2f05e31e484cf9b887e3f793",
 "events.jsonl":"588584295f1c4a7c3d90b04075ab151504f165ff069534d935cda08853ec28b1",
 "pages.jsonl":"92b296170b496b836cdf5ef783bed9465d2d75db7e1a0becec1c36c8b7c42cfd",
 "labels.jsonl":"d94aecd84baecda46344f5b8726a95a9c81e7e41a1c0969fc89a90c8906f0388"}
def main():
    d = pathlib.Path("data"); d.mkdir(exist_ok=True)
    z = d/"full-wiki-logs.zip"
    print("downloading", URL)
    urllib.request.urlretrieve(URL, z)
    zipfile.ZipFile(z).extractall(d)
    ok = True
    for name, want in SUMS.items():
        got = hashlib.sha256((d/name).read_bytes()).hexdigest()
        tick = "ok" if got == want else "MISMATCH"
        if got != want: ok = False
        print(f"  {tick}  {name}")
    sys.exit(0 if ok else 1)
if __name__ == "__main__":
    main()
