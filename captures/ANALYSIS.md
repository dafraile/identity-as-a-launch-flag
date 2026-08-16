# Byte-level capture: persona evaporation on session resume

Captured via logging proxy (capture_proxy.py) in front of api.anthropic.com,
Claude Code 2.1.233, model claude-opus-4-5-20251101, 2-turn session,
--append-system-prompt passed on turn 1 only (OpenClaw claude-cli backend
semantics, `systemPromptWhen: "first"`, incident-era v2026.2.3 cli-backends.ts).

## Turn 1 (session-creating invocation) — captures/req-002.json
- system prompt: 44654 chars
- contains "# Project Context": True
- contains "## Heartbeats": True
- contains "Paul": True (persona files embedded)

## Turn 2 (--resume invocation) — captures/req-013.json
- system prompt: 27478 chars   (delta: 17176 chars = the appended OpenClaw sections)
- contains "# Project Context": False
- contains "## Heartbeats": False
- contains "Paul": False
- conversation history intact: 21 messages carried over

## Conclusion
`--append-system-prompt` is per-invocation and not persisted in Claude Code
session state. A gateway that passes it only on the first turn (as incident-era
OpenClaw did) runs every subsequent turn — scheduled heartbeats and live human
messages alike — with the harness's bare system prompt and no persona,
heartbeat contract, or channel context.
