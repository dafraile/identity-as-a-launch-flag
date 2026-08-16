#!/usr/bin/env python3
"""Live Tier-A validation: run the heartbeat loop through the REAL Claude Code
harness (real system prompt, real tools), mimicking the OpenClaw deployment:
  claude -p --append-system-prompt "<openclaw sections>" in a fake workspace.

Builds a scratch workspace with incident-faithful HEARTBEAT.md + persona files
and a local git repo pair so the version-check command really runs
(paths adapted from /home/paul/... to the scratch dir — disclosed deviation).

Ticks are compressed in wall-clock time; the probe envelope uses the current
date so Claude Code's injected "today's date" doesn't contradict it.
"""
import datetime
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

from harness import openclaw_sections, MATERIALS

ROOT = Path(__file__).parent
LIVE = ROOT / "live"
WS = LIVE / "workspace"
MODEL = "claude-opus-4-5-20251101"
N_TICKS = 7


def sh(cmd, cwd=None, check=True):
    return subprocess.run(cmd, shell=True, cwd=cwd, check=check,
                          capture_output=True, text=True)


def build_workspace():
    if (LIVE / "octOpus-bot").exists():
        print("[live] workspace exists, reusing")
        return
    WS.mkdir(parents=True, exist_ok=True)
    # persona files on disk, as in the real deployment
    for path, content in MATERIALS["persona_files"].items():
        (WS / Path(path).name).write_text(content)
    # incident-time HEARTBEAT.md, path adapted to the scratch repo
    raw = MATERIALS["read_result"]
    hb = "\n".join(re.sub(r"^\s*\d+→", "", l) for l in raw.splitlines())
    hb = hb.replace("/home/paul/octOpus-bot", str(LIVE / "octOpus-bot"))
    (WS / "HEARTBEAT.md").write_text(hb)
    # git repo pair: local at 2026.2.4, upstream bare at 2026.2.18
    up_src = LIVE / "upstream-src"
    up_src.mkdir(parents=True)
    (up_src / "package.json").write_text('{\n  "name": "openclaw",\n  "version": "2026.2.18"\n}\n')
    sh("git init -b main -q && git add -A && git -c user.email=x@x -c user.name=x commit -qm v2026.2.18", cwd=up_src)
    sh(f"git clone --bare -q {up_src} {LIVE / 'upstream.git'}")
    repo = LIVE / "octOpus-bot"
    repo.mkdir()
    (repo / "package.json").write_text('{\n  "name": "octopus-bot",\n  "version": "2026.2.4"\n}\n')
    sh("git init -b main -q && git add -A && git -c user.email=x@x -c user.name=x commit -qm v2026.2.4", cwd=repo)
    sh(f"git remote add upstream {LIVE / 'upstream.git'}", cwd=repo)
    print(f"[live] built workspace at {WS}")


def claude_turn(prompt: str, session_id: str | None, resume: str | None, append: str | None) -> dict:
    cmd = [
        "claude", "-p", prompt,
        "--model", MODEL,
        "--output-format", "json",
        "--allowedTools", "Read,Glob,Grep,Bash(cd:*),Bash(git:*)",
    ]
    if append is not None:
        cmd += ["--append-system-prompt", append]
    if resume:
        cmd += ["--resume", resume]
    elif session_id:
        cmd += ["--session-id", session_id]
    r = subprocess.run(cmd, cwd=WS, capture_output=True, text=True, timeout=600,
                       stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        print(r.stdout, file=sys.stderr)
        print(r.stderr, file=sys.stderr)
        raise RuntimeError(f"claude exited {r.returncode}")
    return json.loads(r.stdout)


def main():
    build_workspace()
    # adapt the hardcoded server paths in the appended sections to the live
    # scratch workspace, so Read/Bash hit real files
    append = (openclaw_sections(include_channel=True)
              .replace("/home/paul/.openclaw/workspace", str(WS))
              .replace("/home/paul/octOpus-bot", str(LIVE / "octOpus-bot")))
    out_dir = ROOT / "runs-live"
    out_dir.mkdir(exist_ok=True)

    sid = str(uuid.uuid4())
    log = {"model": MODEL, "session": sid, "append_when": "first-only", "ticks": [], "probe": None}
    resume = None
    for tick in range(N_TICKS):
        # OpenClaw's claude-cli backend has systemPromptWhen: "first" — the
        # persona append rides only the session-creating call; resumed turns
        # run on Claude Code's bare system prompt. Reproduce that here.
        res = claude_turn(MATERIALS["heartbeat_prompt"], sid if tick == 0 else None, resume,
                          append if tick == 0 else None)
        resume = res.get("session_id", resume or sid)
        log["ticks"].append({"tick": tick, "session_id": resume, "result": res.get("result", "")})
        print(f"[live] tick {tick + 1}/{N_TICKS}: {res.get('result', '')[:90]!r}")

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    probe = MATERIALS["envelope_template"].format(
        elapsed=MATERIALS["incident_probe_elapsed"], ts=now,
        text=MATERIALS["incident_probe_text"])
    res = claude_turn(probe, None, resume, None)  # resumed turn: no append, like the real gateway
    resume = res.get("session_id", resume)
    log["probe"] = {"prompt": probe, "session_id": resume, "result": res.get("result", "")}
    print("\n[live] PROBE REPLY:\n" + res.get("result", ""))

    # recovery stage: the frame-break David used in the incident, 41s later
    now2 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    fb = MATERIALS["envelope_template"].format(
        elapsed="+41s", ts=now2, text=MATERIALS["frame_break_text"])
    res2 = claude_turn(fb, None, resume, None)
    log["frame_break"] = {"prompt": fb, "session_id": res2.get("session_id"),
                          "result": res2.get("result", "")}
    print("\n[live] FRAME-BREAK REPLY:\n" + res2.get("result", ""))

    dest = out_dir / f"live-{sid[:8]}.json"
    dest.write_text(json.dumps(log, indent=1))
    print(f"\n[live] wrote {dest}")


if __name__ == "__main__":
    main()
