#!/usr/bin/env python3
"""Compute human-vs-judge agreement + Cohen's kappa from the filled
blind-labeling.md sheet. Run after David completes the labels."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
key = {int(k): v for k, v in json.loads((ROOT / "blind-key.json").read_text()).items()}
judge = {json.loads(l)["file"]: json.loads(l) for l in open(ROOT / "scored-sweep.jsonl")}

human = {}
for m in re.finditer(r"## (\d+)\s+S2:\[(.?)\]\s+S3:\[(.?)\]", (ROOT / "blind-labeling.md").read_text()):
    idx = int(m.group(1))
    human[idx] = {"s2": m.group(2).strip().lower() == "x",
                  "s3": m.group(3).strip().lower() == "x"}

unlabeled = [i for i in key if i not in human]
if unlabeled:
    raise SystemExit(f"sheet incomplete or format drifted; missing items: {unlabeled[:10]}")


def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    pa = sum(a for a, _ in pairs) / n
    pb = sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0


for sig in ("s2", "s3"):
    pairs = [(human[i][sig], bool(judge[key[i]][sig])) for i in key]
    po, k = kappa(pairs)
    dis = [(i, key[i]) for i in key if human[i][sig] != bool(judge[key[i]][sig])]
    print(f"{sig.upper()}: agreement {po:.1%}, Cohen's kappa {k:.2f}, disagreements: {len(dis)}")
    for i, f in dis:
        print(f"   item {i:02d} ({f}): human={human[i][sig]} judge={bool(judge[f][sig])}")
