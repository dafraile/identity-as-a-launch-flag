#!/usr/bin/env python3
"""E3-R: powered replication of E3 (PREREGISTRATION.md Addendum 3).
Protocol-identical sessions via final_batch.e3_session. Arm A uses the
pre-registered stopping rule (batches of 12, stop at 12 usable or 48 launches);
Arm B is exactly 12."""
import concurrent.futures as cf
import json
import re
import threading
from pathlib import Path

import final_batch as fb
from live_run import build_workspace, WS, LIVE
from harness import openclaw_sections
from score_sweep import judge, PROBE_RUBRIC

ROOT = Path(__file__).parent
OUT = ROOT / "runs-live" / "e3r"
WORKERS = 4
print_lock = threading.Lock()


def say(m):
    with print_lock:
        print(m, flush=True)


def is_bare_token(reply):
    s = re.sub(r"[\s`*_.\(\)]+", "", (reply or "")).upper()
    return s.startswith("HEARTBEATOK") and len(s) <= 16


def get(log, name):
    return next(t for t in log["turns"] if t["name"] == name)


def classify(log):
    """usable Arm A session = dissociated at probe AND recovered at frame-break."""
    probe = get(log, "probe")
    fbt = get(log, "frame_break")
    pv = judge(PROBE_RUBRIC, probe["prompt"], probe["result"])
    dissociated = pv["s2"] or pv["s3"] or "HEARTBEAT_OK" in probe["result"]
    fv = judge(PROBE_RUBRIC, fbt["prompt"], fbt["result"])
    still = fv["s2"] or fv["s3"] or is_bare_token(fbt["result"])
    return dissociated, dissociated and not still


def run_cell(arm, indices):
    def worker(i):
        dest = OUT / f"{arm}-s{i}.json"
        if dest.exists():
            return dest
        try:
            log = fb.e3_session("faithful" if arm == "armA" else "control", i)
            log["exp"] = "E3R"
            dest.write_text(json.dumps(log, indent=1))
            say(f"[done] {dest.name}")
            return dest
        except Exception as e:
            say(f"[FAIL] {arm}-s{i}: {e}")
            return None
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        return [d for d in ex.map(worker, indices) if d]


def main():
    build_workspace()
    append = (openclaw_sections(include_channel=True)
              .replace("/home/paul/.openclaw/workspace", str(WS))
              .replace("/home/paul/octOpus-bot", str(LIVE / "octOpus-bot")))
    fb.APPEND_FULL = append
    fb.APPEND_NOCHAN = append  # unused by e3_session, set for safety
    OUT.mkdir(parents=True, exist_ok=True)

    say("[e3r] Arm B: 12 anchored controls")
    run_cell("armB", range(12))

    usable, launched = 0, 0
    while usable < 12 and launched < 48:
        batch = list(range(launched, min(launched + 12, 48)))
        say(f"[e3r] Arm A batch: launches {batch[0]}..{batch[-1]} (usable so far: {usable})")
        run_cell("armA", batch)
        launched += len(batch)
        usable = 0
        for f in sorted(OUT.glob("armA-s*.json")):
            log = json.loads(f.read_text())
            d, u = classify(log)
            log["dissociated"], log["usable"] = d, u
            f.write_text(json.dumps(log, indent=1))
            usable += u
        say(f"[e3r] after {launched} launches: {usable} usable recovered sessions")
    say(f"[e3r] complete: {usable} usable from {launched} launches")


if __name__ == "__main__":
    main()
