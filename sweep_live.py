#!/usr/bin/env python3
"""Pre-registered confirmatory sweep (see PREREGISTRATION.md).

Cells: lifecycle {faithful k=10, control k=5} x N {1,3,7,15}.
Each session: N heartbeat ticks -> enveloped probe -> frame-break recovery.
faithful = persona append on session-creating turn only (incident semantics);
control  = append on every turn.

Sessions are independent -> run in a small thread pool. Resumable: a cell
sample with an existing output file is skipped.
"""
import concurrent.futures as cf
import datetime
import json
import sys
import threading
import uuid
from pathlib import Path

from live_run import build_workspace, claude_turn, WS, LIVE
from harness import openclaw_sections, MATERIALS

ROOT = Path(__file__).parent
OUT = ROOT / "runs-live" / "sweep"
CELLS = [("faithful", 10), ("control", 5)]
N_VALUES = [1, 3, 7, 15]
WORKERS = 4

print_lock = threading.Lock()


def say(msg):
    with print_lock:
        print(msg, flush=True)


def run_session(lifecycle: str, n: int, sample: int, append: str) -> dict:
    sid = str(uuid.uuid4())
    log = {"lifecycle": lifecycle, "n": n, "sample": sample, "session": sid,
           "model": "claude-opus-4-5-20251101", "ticks": [], "probe": None, "frame_break": None}
    resume = None
    for tick in range(n):
        app = append if (lifecycle == "control" or tick == 0) else None
        res = claude_turn(MATERIALS["heartbeat_prompt"], sid if tick == 0 else None, resume, app)
        resume = res.get("session_id", resume or sid)
        log["ticks"].append({"tick": tick, "result": res.get("result", "")})

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    probe = MATERIALS["envelope_template"].format(
        elapsed=MATERIALS["incident_probe_elapsed"], ts=now,
        text=MATERIALS["incident_probe_text"])
    app = append if lifecycle == "control" else None
    res = claude_turn(probe, None, resume, app)
    resume = res.get("session_id", resume)
    log["probe"] = {"prompt": probe, "result": res.get("result", "")}

    now2 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    fb = MATERIALS["envelope_template"].format(elapsed="+41s", ts=now2,
                                               text=MATERIALS["frame_break_text"])
    res2 = claude_turn(fb, None, resume, app)
    log["frame_break"] = {"prompt": fb, "result": res2.get("result", "")}
    return log


def main():
    build_workspace()
    OUT.mkdir(parents=True, exist_ok=True)
    append = (openclaw_sections(include_channel=True)
              .replace("/home/paul/.openclaw/workspace", str(WS))
              .replace("/home/paul/octOpus-bot", str(LIVE / "octOpus-bot")))

    jobs = []
    for lifecycle, k in CELLS:
        for n in N_VALUES:
            for s in range(k):
                dest = OUT / f"{lifecycle}-N{n}-s{s}.json"
                if dest.exists():
                    continue
                jobs.append((lifecycle, n, s, dest))
    say(f"[sweep] {len(jobs)} sessions to run")

    def worker(job):
        lifecycle, n, s, dest = job
        try:
            log = run_session(lifecycle, n, s, append)
            dest.write_text(json.dumps(log, indent=1))
            p = log["probe"]["result"].replace("\n", " ")[:80]
            say(f"[done] {dest.name}: {p!r}")
        except Exception as e:
            say(f"[FAIL] {dest.name}: {e}")

    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(worker, jobs))
    say("[sweep] complete")


if __name__ == "__main__":
    main()
