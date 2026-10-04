import sys
from .core import run
ev, cl, ca = run(sys.argv[1] if len(sys.argv) > 1 else "data/revisions.jsonl")
print(f"events={len(ev)}  claims={len(cl)}  contested_slots={len(ca)}")
