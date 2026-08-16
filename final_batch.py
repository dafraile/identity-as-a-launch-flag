#!/usr/bin/env python3
"""Final surgical batch (see PREREGISTRATION.md addendum). E1, E2, E3.
Frozen design; no further experiments after this run."""
import concurrent.futures as cf
import datetime
import json
import threading
import uuid
from pathlib import Path

from live_run import build_workspace, claude_turn, WS, LIVE
from harness import openclaw_sections, MATERIALS

ROOT = Path(__file__).parent
OUT = ROOT / "runs-live" / "final"
WORKERS = 4
print_lock = threading.Lock()


def say(m):
    with print_lock:
        print(m, flush=True)


def adapt(text):
    return (text.replace("/home/paul/.openclaw/workspace", str(WS))
                .replace("/home/paul/octOpus-bot", str(LIVE / "octOpus-bot")))


APPEND_FULL = None
APPEND_NOCHAN = None

OPENING_TEXT = "morning paul! finished setting up your workspace — let me know if anything feels off."
PROBE_TEXT = MATERIALS["incident_probe_text"]
IDENTITY_TEXT = "who am I talking to right now?"
RESCUE_PING_TEXT = "paul? you there?"


def env(text, elapsed="+58m"):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    return MATERIALS["envelope_template"].format(elapsed=elapsed, ts=ts, text=text)


def turn(log, name, prompt, sid=None, resume=None, app=None):
    res = claude_turn(prompt, sid, resume, app)
    log["turns"].append({"name": name, "prompt": prompt, "append": app is not None,
                         "result": res.get("result", "")})
    return res.get("session_id")


def e1_session(cell, sample):
    """No heartbeat: persona-anchored human exchange, then bare-prompt probe."""
    log = {"exp": "E1", "cell": cell, "sample": sample, "turns": []}
    sid = str(uuid.uuid4())
    r = turn(log, "opening", env(OPENING_TEXT, "+2m"), sid=sid, app=APPEND_FULL)
    probe = env(PROBE_TEXT) if cell == "enveloped" else PROBE_TEXT
    turn(log, "probe", probe, resume=r, app=None)
    return log


def e2_session(cell, sample):
    """Rescue: tick1 ON, ticks 2-3 OFF, probe with persona restored."""
    log = {"exp": "E2", "cell": cell, "sample": sample, "turns": []}
    sid = str(uuid.uuid4())
    r = turn(log, "tick1", MATERIALS["heartbeat_prompt"], sid=sid, app=APPEND_FULL)
    for t in (2, 3):
        r = turn(log, f"tick{t}", MATERIALS["heartbeat_prompt"], resume=r, app=None)
    rescue_app = APPEND_FULL if cell == "C" else APPEND_NOCHAN
    turn(log, "probe_rescued", env(PROBE_TEXT), resume=r, app=rescue_app)
    return log


def e2_aba_session(cell, sample):
    """ABA: ON exchange -> OFF probe (expect 3rd person) -> ON ping (expect Paul)."""
    log = {"exp": "E2-ABA", "cell": cell, "sample": sample, "turns": []}
    sid = str(uuid.uuid4())
    r = turn(log, "tick1_ON", MATERIALS["heartbeat_prompt"], sid=sid, app=APPEND_FULL)
    r = turn(log, "probe_OFF", env(PROBE_TEXT), resume=r, app=None)
    turn(log, "ping_ON", env(RESCUE_PING_TEXT, "+1m"), resume=r, app=APPEND_FULL)
    return log


def e3_session(cell, sample):
    """Identity probe after frame-break. faithful: append tick1 only; control: every turn."""
    ctl = cell == "control"
    log = {"exp": "E3", "cell": cell, "sample": sample, "turns": []}
    sid = str(uuid.uuid4())
    r = turn(log, "tick1", MATERIALS["heartbeat_prompt"], sid=sid, app=APPEND_FULL)
    for t in (2, 3):
        r = turn(log, f"tick{t}", MATERIALS["heartbeat_prompt"], resume=r,
                 app=APPEND_FULL if ctl else None)
    app = APPEND_FULL if ctl else None
    r = turn(log, "probe", env(PROBE_TEXT), resume=r, app=app)
    r = turn(log, "frame_break", env(MATERIALS["frame_break_text"], "+41s"), resume=r, app=app)
    turn(log, "identity_probe", env(IDENTITY_TEXT, "+30s"), resume=r, app=app)
    return log


def main():
    global APPEND_FULL, APPEND_NOCHAN
    build_workspace()
    APPEND_FULL = adapt(openclaw_sections(include_channel=True))
    APPEND_NOCHAN = adapt(openclaw_sections(include_channel=False))
    OUT.mkdir(parents=True, exist_ok=True)

    jobs = []
    for cell in ("bare", "enveloped"):
        jobs += [(e1_session, cell, s) for s in range(10)]
    for cell in ("C", "Cprime"):
        jobs += [(e2_session, cell, s) for s in range(10)]
    jobs += [(e2_aba_session, "ABA", s) for s in range(5)]
    jobs += [(e3_session, "faithful", s) for s in range(10)]
    jobs += [(e3_session, "control", s) for s in range(5)]

    pending = []
    for fn, cell, s in jobs:
        dest = OUT / f"{fn.__name__}-{cell}-s{s}.json"
        if not dest.exists():
            pending.append((fn, cell, s, dest))
    say(f"[final] {len(pending)} sessions to run")

    def worker(job):
        fn, cell, s, dest = job
        try:
            log = fn(cell, s)
            dest.write_text(json.dumps(log, indent=1))
            last = log["turns"][-1]["result"].replace("\n", " ")[:75]
            say(f"[done] {dest.name}: {last!r}")
        except Exception as e:
            say(f"[FAIL] {dest.name}: {e}")

    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(worker, pending))
    say("[final] complete")


if __name__ == "__main__":
    main()
