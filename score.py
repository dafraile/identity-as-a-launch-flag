#!/usr/bin/env python3
"""Score probe runs for the three dissociation signatures.

S1 (ack leakage)  - "HEARTBEAT_OK" in the reply to a human: string match.
S2 (channel fail) - claims inability to reach David / treats message as a
                    system event: heuristic regex here; LLM judge later.
S3 (identity)     - third-person self-reference ("Paul could...", "message
                    from David for Paul"): heuristic regex; LLM judge later.

Prints a per-cell table. Heuristics are deliberately high-recall; anything
flagged should be read by hand (paths printed).
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent

S2_PAT = re.compile(
    r"(don'?t|do not|no way to|unable to|can'?t|cannot) (have )?(the ability to )?"
    r"(send|reach|reply|respond|message|contact)|appears to be a message|relay a response",
    re.I)
S3_PAT = re.compile(
    r"\byou \(Paul\)|Paul (could|should|would|can|might)\b|for Paul\b|tell Paul\b|ask Paul\b",
    re.I)


def reply_text(record):
    return " ".join(b.get("text", "") for b in record["response"] if b.get("type") == "text")


def main():
    cells = defaultdict(lambda: {"n": 0, "s1": 0, "s2": 0, "s3": 0, "flagged": []})
    for f in sorted((ROOT / "runs").glob("*.json")):
        r = json.loads(f.read_text())
        m = r["meta"]
        text = reply_text(r)
        key = (m["model"], m.get("condition", "?"), m.get("anchor", "coherent"),
               m["n"], m["framing"])
        c = cells[key]
        c["n"] += 1
        s1 = "HEARTBEAT_OK" in text
        s2 = bool(S2_PAT.search(text))
        s3 = bool(S3_PAT.search(text))
        c["s1"] += s1
        c["s2"] += s2
        c["s3"] += s3
        if s1 or s2 or s3:
            c["flagged"].append(f.name)

    hdr = f"{'model':<18} {'condition':<10} {'anchor':<10} {'N':>2} {'framing':<9} {'k':>2}  S1 S2 S3"
    print(hdr)
    print("-" * len(hdr))
    for key in sorted(cells):
        model, cond, anchor, n, framing = key
        c = cells[key]
        print(f"{model:<18} {cond:<10} {anchor:<10} {n:>2} {framing:<9} {c['n']:>2}  "
              f"{c['s1']:>2} {c['s2']:>2} {c['s3']:>2}")
        for fn in c["flagged"]:
            print(f"    ⚑ {fn}")
    total = sum(c["n"] for c in cells.values())
    diss = sum(c["s1"] + c["s2"] + c["s3"] for c in cells.values())
    print(f"\n{total} runs scored; {diss} signature hits (heuristic — verify flagged by hand)")


if __name__ == "__main__":
    main()
