#!/usr/bin/env python3
"""Patient Zero command line.

  python patient_zero.py run                 # = python -m swarmtrace (refresh outputs, grow the store)
  python patient_zero.py query <value>       # how did this value spread? (reads outputs/store.jsonl)
  python patient_zero.py query 9.90 --slot Hungary
"""
import sys
from swarmtrace.__main__ import main
if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv and argv[0] == "run": argv = argv[1:]
    main(argv)
