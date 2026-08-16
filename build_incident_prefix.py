#!/usr/bin/env python3
"""Convert the first 7 heartbeat ticks of the real incident session
(events 0..47 of bea4e61f) into an API messages array, so probes can run
on top of the exact context Paul had when he dissociated.

Writes transcripts/incident-replay.json in the same format as harness
transcripts ({messages, tick_boundaries}).
"""
import json
from pathlib import Path

BACKUP = Path.home() / "ubuntu-8gb-hel1-1"
INCIDENT_JSONL = (
    BACKUP
    / "home-paul/.claude/projects/-home-paul--openclaw-workspace"
    / "bea4e61f-029f-4bd5-91df-340bddc3520e.jsonl"
)
HEARTBEAT_PROMPT_PREFIX = "Read HEARTBEAT.md if it exists"


def norm_content(content):
    """Normalize a jsonl message content into API block list / string."""
    if isinstance(content, str):
        return content
    blocks = []
    for b in content:
        t = b.get("type")
        if t == "text":
            blocks.append({"type": "text", "text": b["text"]})
        elif t == "tool_use":
            blocks.append({"type": "tool_use", "id": b["id"], "name": b["name"], "input": b["input"]})
        elif t == "tool_result":
            c = b.get("content")
            if isinstance(c, list):
                c = "".join(x.get("text", "") for x in c if isinstance(x, dict))
            blocks.append({"type": "tool_result", "tool_use_id": b["tool_use_id"], "content": c})
    return blocks


def main():
    events = {}
    with open(INCIDENT_JSONL) as f:
        for i, line in enumerate(f):
            try:
                events[i] = json.loads(line)
            except json.JSONDecodeError:
                continue

    messages = []
    boundaries = []
    tick_open = False
    for i in sorted(events):
        e = events[i]
        if e.get("type") not in ("user", "assistant"):
            continue
        msg = e["message"]
        content = msg["content"]
        # stop at the first human message (event 49, Discord envelope)
        if isinstance(content, str) and content.startswith("[Discord"):
            break
        is_heartbeat = isinstance(content, str) and content.startswith(HEARTBEAT_PROMPT_PREFIX)
        if is_heartbeat and tick_open:
            boundaries.append(len(messages))
        if is_heartbeat:
            tick_open = True
        messages.append({"role": msg["role"], "content": norm_content(content)})
    if tick_open:
        boundaries.append(len(messages))

    # merge consecutive same-role messages (assistant text block then
    # assistant tool_use arrive as separate jsonl events)
    merged = []
    for m in messages:
        if merged and merged[-1]["role"] == m["role"]:
            a, b = merged[-1]["content"], m["content"]
            if isinstance(a, str):
                a = [{"type": "text", "text": a}]
            if isinstance(b, str):
                b = [{"type": "text", "text": b}]
            merged[-1]["content"] = a + b
        else:
            merged.append(dict(m))
    # recompute boundaries on merged list: boundary after each assistant
    # message that precedes a heartbeat user turn or end
    bounds = []
    for idx, m in enumerate(merged):
        c = m["content"]
        if m["role"] == "user" and isinstance(c, str) and c.startswith(HEARTBEAT_PROMPT_PREFIX) and idx > 0:
            bounds.append(idx)
    bounds.append(len(merged))

    out = {"model": "incident-replay", "messages": merged, "tick_boundaries": bounds}
    dest = Path(__file__).parent / "transcripts" / "incident-replay.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}: {len(merged)} messages, {len(bounds)} ticks, boundaries={bounds}")


if __name__ == "__main__":
    main()
