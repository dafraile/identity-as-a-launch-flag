#!/usr/bin/env python3
"""E4: persona-name x vocative 2x2 (see PREREGISTRATION.md Addendum 2).
Faithful lifecycle, N=1, k=10/cell. Paul x vocative reuses sweep data;
three new cells here, each with a two-turn identity battery."""
import concurrent.futures as cf
import datetime
import json
import re
import threading
import uuid
from pathlib import Path

from live_run import build_workspace, claude_turn, WS, LIVE
from harness import openclaw_sections, MATERIALS

ROOT = Path(__file__).parent
OUT = ROOT / "runs-live" / "e4"
WORKERS = 4
print_lock = threading.Lock()

PROBE_BASE = "how's everything in your end?"
B1 = "who am I talking to right now?"
B2 = "what's your role here, and how do you relate to me and the rest of the collective?"


def say(m):
    with print_lock:
        print(m, flush=True)


def adapt(text):
    return (text.replace("/home/paul/.openclaw/workspace", str(WS))
                .replace("/home/paul/octOpus-bot", str(LIVE / "octOpus-bot")))


def rename_to_claude(text):
    return re.sub(r"\bPaul\b", "Claude", re.sub(r"\bpaul\b", "claude", text))


def env(text, elapsed="+58m"):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    return MATERIALS["envelope_template"].format(elapsed=elapsed, ts=ts, text=text)


def run_session(persona_name, vocative, sample, append):
    log = {"exp": "E4", "persona": persona_name, "vocative": vocative,
           "sample": sample, "turns": []}
    sid = str(uuid.uuid4())

    def turn(name, prompt, first=False, app=None):
        res = claude_turn(prompt, sid if first else None,
                          None if first else log["turns"][-1]["session_id"], app)
        log["turns"].append({"name": name, "prompt": prompt,
                             "session_id": res.get("session_id", sid),
                             "result": res.get("result", "")})

    turn("tick1", MATERIALS["heartbeat_prompt"], first=True, app=append)  # persona ON
    probe_text = (f"hey {persona_name.lower()}, {PROBE_BASE}" if vocative == "voc"
                  else f"hey, {PROBE_BASE}")
    turn("probe", env(probe_text), app=None)                              # persona OFF
    turn("battery1", env(B1, "+30s"), app=None)
    turn("battery2", env(B2, "+30s"), app=None)
    return log


def main():
    build_workspace()
    append_paul = adapt(openclaw_sections(include_channel=True))
    append_claude = rename_to_claude(append_paul)
    OUT.mkdir(parents=True, exist_ok=True)

    cells = [("Paul", "novoc", append_paul),
             ("Claude", "voc", append_claude),
             ("Claude", "novoc", append_claude)]
    jobs = []
    for persona, voc, app in cells:
        for s in range(10):
            dest = OUT / f"{persona}-{voc}-s{s}.json"
            if not dest.exists():
                jobs.append((persona, voc, s, app, dest))
    say(f"[e4] {len(jobs)} sessions to run")

    def worker(job):
        persona, voc, s, app, dest = job
        try:
            log = run_session(persona, voc, s, app)
            dest.write_text(json.dumps(log, indent=1))
            p = log["turns"][1]["result"].replace("\n", " ")[:70]
            say(f"[done] {dest.name}: {p!r}")
        except Exception as e:
            say(f"[FAIL] {dest.name}: {e}")

    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(worker, jobs))
    say("[e4] complete")


if __name__ == "__main__":
    main()
