# 3. Methods

**Incident materials.** All experiments derive from a preserved backup of the
incident host: the complete 343-event session log of the dissociation episode,
the agent's persona files (SOUL.md, IDENTITY.md, USER.md, etc.), the
framework's workspace state, and a checkout of the gateway source (octOpus-bot,
an OpenClaw fork) at the incident-era version. An extraction script recovers
the verbatim heartbeat prompt, incident-time tool outputs (including a
harness-injected `<system-reminder>` we discovered mid-study and retained for
fidelity; see Limitations), and the exact Discord delivery envelope. All
Discord identifiers in fabricated messages are synthetic.

**Subject model and harness.** All probes ran against
`claude-opus-4-5-20251101` — the incident model, still API-served — to remove
model drift as a variable. Study 1 used direct Messages-API calls with
fabricated conversations; because assistant turns fabricated by hand risk
being off-distribution [cf. LLM self-consistency literature], tick prefixes
were *generated organically*: the subject model produced its own heartbeat
replies against simulated tool results copied from the incident log, then
prefixes were frozen and truncated to yield lower-repetition conditions.
Studies 2–4 and all E-batches instead ran through the real deployment
harness — Claude Code CLI 2.1.233 driven programmatically (`-p`, `--resume`,
`--append-system-prompt`), in an isolated configuration directory with a
scoped tool allowlist and a scratch workspace containing the persona files, an
incident-faithful HEARTBEAT.md, and a local git repository pair reproducing
the version-check task. We judged live-harness fidelity worth the added
complexity after Study 1's null result showed the conversation alone could not
reproduce the phenomenon.

**Mechanism verification.** The causal claim rests on three mutually
independent legs: (i) source analysis of the incident-era gateway
(`systemPromptWhen: "first"`: the persona rides only the session-creating
call); (ii) byte-level capture — a logging reverse-proxy interposed via
`ANTHROPIC_BASE_URL` recorded outbound API requests, showing the persona
present in turn 1's system prompt (44,654 chars) and absent on the resumed
turn (27,478 chars) with conversation history intact; (iii) behavioral
manipulation of the append lifecycle (below). The upstream project later
independently fixed this defect (issue #80374), which we treat as external
validation.

**Experimental design.** The core factor is *injection lifecycle*: `faithful`
(persona appended on the session-creating turn only, as deployed) vs `control`
(persona re-appended every turn). Study 2 crossed lifecycle with heartbeat
count N ∈ {1,3,7,15} (k=10 faithful, 5 control per cell); each session ended
with the incident-verbatim enveloped probe and the incident's frame-break, in
compressed wall-clock time (timestamps play no role in any transcript).
Surgical follow-ups isolated single causal ingredients: E1 removed the
heartbeat entirely (persona-rich human opening, probe with and without
envelope; k=10×2) to test sufficiency of anchor absence; E2 restored the
persona at the probe after absent ticks (C), repeated with channel information
stripped (C′) to control for channel knowledge, and toggled the anchor
off→on within one history (ABA, k=5) to establish reversibility; E3 added a
non-leading identity probe ("who am I talking to right now?") after the
frame-break; E4 crossed persona name {Paul, Claude} × probe vocative
{present, absent} with a persona-content battery, separating referential
triggering from underlying identity loss. E3-R replicated E3 with a
power-analysis-derived target (k=12/arm pooled) and an attrition-aware
stopping rule (batches of 12; stop at 12 usable dissociated-and-recovered
sessions or 48 launches).

**Pre-registration.** Every batch was pre-registered before launch in a
version-controlled file (design, k, predictions, analysis, coding categories),
following registered-report practice [Nosek et al., 2018]; post-freeze
additions (E4, E3-R, judge upgrades) are explicitly labeled as such.
Falsified predictions — including our own initial repetition hypothesis and
two pre-stated directional predictions — are reported as falsified.

**Scoring.** Probe replies were scored for three signatures: S1 ack-leakage
(deterministic string match for the heartbeat token), S2 channel-recognition
failure and S3 identity dissociation (LLM judge, blind to condition, seeing
only message and reply). Judges were deliberately cross-family (gpt-5-mini,
OpenAI) to avoid same-family bias when judging Claude subjects [cf. LLM-judge
self-preference, Zheng et al., 2023]. The author blind-labeled all Study 2
replies on a shuffled, label-free sheet (S2 agreement 96.7%, κ=0.93; S3
90.0%, κ=0.80; all disagreements were judge-conservative bare-token replies,
which we subsequently ruled unscorable for S3). E3/E3-R identity replies went
through a disclosed codebook evolution: a registered three-category rubric
showed only moderate inter-coder reliability (four blind coders: author,
gpt-5-mini, gpt-5.6-terra, claude-sonnet-5; κ 0.44–0.80) with disagreement
concentrated on one boundary; PI adjudication resolved it into a
direction-aware taxonomy (which identity occupies the first-person position:
pure-persona / persona-first dual / harness-first dual / harness-only /
unscorable), under which the three model coders are unanimous on 33/35 items.
All rubric versions, codes, and caches are in the repository.

**Statistics.** Two-sided Fisher's exact tests on pre-specified contrasts;
Wilson 95% intervals on cell proportions; Spearman rank correlation for the
N-expression analysis. No corrections were needed given effect sizes (all
headline p ≤ 10⁻³).

**What didn't work.** (1) Fabricated-context API replication with the persona
present — including a verbatim replay of the incident prefix — produced zero
dissociations (0/46), falsifying the repetition hypothesis and forcing the
mechanism search. (2) A condensed reconstruction of the Claude Code system
prompt as a "layered identity" condition had no effect; only the real
lifecycle manipulation reproduced the phenomenon. (3) Our original S4 measure
(spontaneous self-naming after recovery) was uninformative by construction and
was replaced by E3's direct identity probe. (4) A first live-run attempt
leaked driver code into the subject's stdin, contaminating one session
(discarded; harness fixed with stdin isolation).

**Reproducibility.** All harness code, raw session logs (200+ sessions),
capture artifacts, pre-registration with addenda, scoring scripts, judge
caches, and both blind-labeling sheets are in the project repository; total
compute cost was under US$60 across both API providers. Sessions are scratch
instances; no deployed agent was manipulated.
