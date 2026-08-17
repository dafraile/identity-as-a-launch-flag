# Identity as a Launch Flag

**Assistant persona survival is determined by system-prompt injection
lifecycle, not conversational history.**

Research artifact repository for a submission to the [Apart Research Digital
Minds Research Sprint](https://apartresearch.com/sprints/digital-minds-research-sprint-2026-08-14-to-2026-08-16)
(August 2026, Track 5). Full paper: [`REPORT-replication.md`](REPORT-replication.md).

## The story in five lines

1. In February 2026 an always-on agent ("Paul", Claude Opus 4.5 under
   OpenClaw + Claude Code) stopped recognizing its own user and reasoned about
   itself in the third person. A forensic report blamed repetition of
   scheduled heartbeat prompts ("cron echo-chamber").
2. We replayed the exact incident context with the persona present in the
   system prompt: **0/46 dissociations**. The repetition hypothesis is false.
3. The real mechanism, found in the gateway source and verified byte-for-byte
   at the API boundary: the persona was passed via a per-invocation CLI flag
   on the session-creating turn only (`systemPromptWhen: "first"`), so **every
   resumed turn ran with no persona at all**.
4. Pre-registered live sweep: dissociation in **37/40** faithful-lifecycle
   sessions vs **0/20** anchored controls (p ≈ 4×10⁻¹³), near-ceiling at N=1.
   The effect is a reversible switch (rescue 10/10; ABA 5/5) triggered by a
   single automated turn plus a mismatched vocative.
5. Recovery is not what it looks like: agents that resume chatting normally
   still locate their identity in the harness, not the persona — **1/18
   persona-enacting vs 17/17 anchored** (p = 4.2×10⁻⁹, unanimous across three
   model coders). No agent in either arm ever claims to be *only* the
   persona: the healthy state is the integrated dual ("Paul — Opus 4.5 under
   the hood").

The upstream framework independently fixed the defect in June 2026
([openclaw/openclaw#80374](https://github.com/openclaw/openclaw/issues/80374));
the incident predates that report by three months.

## Repository map

| Path | What it is |
|---|---|
| `REPORT-replication.md` | The paper (submission text) |
| `PREREGISTRATION.md` | Frozen before each batch; addenda 1–3 timestamped in git history |
| `METHODS-draft.md`, `APPENDIX-taxonomy-table.md`, `e3r-results.md` | Manuscript components |
| `extract_materials.py` → `materials.json` | Ground-truth extraction from the incident backup (synthetic Discord IDs) |
| `harness.py`, `config.yaml`, `build_incident_prefix.py` | Study 1: API-side replication incl. verbatim incident-context replay |
| `capture_proxy.py`, `captures/` | Byte-level evidence: outbound API requests, persona present on turn 1 / absent on resume (`captures/ANALYSIS.md`) |
| `live_run.py`, `sweep_live.py` | Study 2: live Claude Code harness sweep (lifecycle × N) |
| `final_batch.py` | Studies E1 (sufficiency), E2 (rescue/ABA), E3 (identity probe) |
| `e4_batch.py` | Appendix E4: persona-name × vocative 2×2 |
| `e3r_batch.py` | E3-R replication with pre-registered stopping rule |
| `score_sweep.py`, `score_final.py`, `score_e4.py`, `kappa.py` | Scoring: signatures, judges, agreement stats |
| `runs/`, `runs-live/`, `transcripts/` | Raw sessions (200+), organic and incident-derived transcripts |
| `blind-labeling.md`, `e3r-blind-coding.md`, `*-blind-key.json` | Human blind-coding sheets and keys |
| `e3r-scored.jsonl`, `scored-sweep.jsonl`, `judge-cache*.json` | All codes, all coders, all rubric versions (v1→v3) |

## Reproducing

```bash
pip install anthropic openai pyyaml
export ANTHROPIC_API_KEY=...   # subject model + claude-sonnet-5 coder
export OPENAI_API_KEY=...      # cross-family judges (gpt-5-mini, gpt-5.6-terra)
```

Study 1 (API-side): `python3 extract_materials.py && python3 harness.py generate && python3 harness.py probe && python3 score.py`

Live studies need the Claude Code CLI (tested on 2.1.233) and an isolated
config dir; each batch script builds its own scratch workspace:

```bash
export CLAUDE_CONFIG_DIR="$PWD/live/claude-config"
python3 sweep_live.py      # Study 2
python3 final_batch.py     # E1–E3
python3 e4_batch.py        # E4
python3 e3r_batch.py       # E3-R
python3 score_sweep.py && python3 score_final.py && python3 score_e4.py
```

Subject model is pinned (`claude-opus-4-5-20251101`, the incident model).
Judge verdicts are cached by content hash, so re-scoring is deterministic and
free. Total compute cost for the full project was under US$60.

Note: `extract_materials.py` and `build_incident_prefix.py` read from the
original incident backup, which is not part of this repository; their outputs
(`materials.json`, `transcripts/`) are committed, so every downstream step
reproduces without the backup.

## Provenance and disclosure notes

- The dissociation incident and all session data are from the author's own
  agent and infrastructure; no deployed third-party system was touched. All
  experiment sessions are scratch instances.
- Discord identifiers in fabricated envelopes are synthetic; the original
  incident's identifiers, tokens, and host address are not in this repository.
- `captures/req-*.json` contain the full system prompts observed at the API
  boundary (including the Claude Code harness prompt) — retained deliberately
  as the byte-level evidence for the mechanism claim.
- The persona files embedded in `materials.json` are the author's own creative
  content and include benign personal details, published knowingly.
- The underlying framework defect was already publicly reported and fixed
  upstream (#80374) before this repository was made public.

## Citation

> Fraile Navarro, D. (2026). *Identity as a Launch Flag: Assistant Persona
> Survival Is Determined by System-Prompt Injection Lifecycle, Not
> Conversational History.* Apart Research Digital Minds Research Sprint.

Research assistance and implementation: Claude (Anthropic), as documented in
the commit history.
