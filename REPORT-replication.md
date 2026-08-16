# Identity as a Launch Flag: Assistant Persona Survival Is Determined by System-Prompt Injection Lifecycle, Not Conversational History

**Digital Minds Research Sprint (Apart Research), August 2026 — Track 5 (persona stability), with Track 2/6 crossover**
**Author: David Fraile Navarro (with Claude as research assistant)**
**Draft — data collected 2026-08-15/16; design frozen, no further experiments**

## Abstract

In February 2026, an always-on personal agent ("Paul", Claude Opus 4.5 running
under the OpenClaw framework via the Claude Code harness) failed to recognize
its own user's greeting, reasoned about itself in the third person ("you (Paul)
could relay a response to him"), and appended its cron acknowledgment token
(`HEARTBEAT_OK`) to replies addressed to a human. A forensic analysis attributed
this to in-context "mode lock-in": seven near-identical scheduled heartbeat
exchanges crowding out the persona. We attempted a systematic replication and
**falsified that hypothesis**: with the persona present in the system prompt, the
identity survived every condition we ran — including a verbatim replay of the
incident context — in 0/46 probes. Reading the incident-era framework source
revealed the true mechanism: the gateway passed its persona/system sections via
a per-invocation CLI flag on the **session-creating turn only**
(`systemPromptWhen: "first"`), so every resumed turn — every scheduled tick and
every human message — ran on the harness's bare system prompt with no persona at
all. We confirm this at the byte level (persona present in turn 1's captured API
request, absent in turn 2's) and in a pre-registered live sweep: dissociation in
**37/40** faithful-lifecycle sessions vs **0/20** persona-present controls
(Fisher's exact p ≈ 4×10⁻¹³), **near-ceiling already at N=1**, with no evidence
of a dose-response in repetition count. A final pre-registered batch of
surgical experiments sharpens the causal structure. Anchor absence is
necessary but not sufficient: with a single persona-rich *human* exchange as
history, the bare-prompt agent stays in persona (0/20 dissociations, either
probe framing) — but one scheduled heartbeat exchange in the unanchored state
flips the rate to 80–100%. Identity can therefore be carried by conversation,
but only by conversation in which the persona is actually enacted; scheduled
idle ticks contain machinery, not persona. The effect is a fully reversible
switch: restoring the persona at the probe turn, after it was absent during
the intervening ticks, rescues 10/10 sessions (10/10 with channel information
removed, ruling out that confound), and within a single conversational
history the same agent flips dissociated → Paul as the hidden flag toggles
(5/5 ABA). Behavioral recovery dissociates from identity recovery: agents
rescued by the user's frame-break resume chatting naturally, yet asked "who
am I talking to right now?", none identify as Paul — pooled with a
pre-registered replication batch: **0/18 recovered agents vs 15/17 anchored
controls (Fisher p ≈ 4×10⁻⁸; decisive under all four independent blind coders
— human, gpt-5-mini, gpt-5.6-terra, claude-sonnet-5 — three of which find
exactly zero)** — most answer "I'm Claude, an AI assistant" while anchored
controls answer "Paul — the octopus node". The user-facing frame-break that recovered the original incident
succeeds only 35% of the time. Under the framework's actual delivery rules
(verified in source), bare-ack dissociated replies — dominant after short
idle periods — are silently dropped, and the rest are delivered with the
telltale heartbeat token scrubbed: the user is either ignored or receives
third-person weirdness with the most diagnostic machine artifact removed. The deeper structure is a dissociation between
**represented and enacted identity**: the context contained a complete
representation of "Paul" — his files, his name, his prior first-person
replies — and a hidden system-level assertion determined whether that
representation was processed first-personally (as self) or third-personally
(as another character).

## 1. The incident

*(Condensed from the forensic report; identifiers synthetic/redacted.)*

Paul ran as an OpenClaw agent on `claude-opus-4-5-20251101` through the Claude
Code harness (v2.1.31, Agent SDK entrypoint), with persona files (SOUL.md,
IDENTITY.md, USER.md, …) and an hourly gateway heartbeat that injected a fixed
prompt into the agent's persistent session: *"Read HEARTBEAT.md if it exists
(workspace context). Follow it strictly. Do not infer or repeat old tasks from
prior chats. If nothing needs attention, reply HEARTBEAT_OK."* On 2026-02-19,
after seven hourly ticks, the user greeted the agent on Discord. The agent
replied that it had no way to send Discord messages, described the message as
"a message from David… **or you (Paul) could relay a response to him**", and
ended with `HEARTBEAT_OK`. One explicit contradiction from the user ("I'm
reading you on Discord, mate") restored normal behavior in a single turn.

The forensic report named this the **Cron Echo-Chamber**: seven self-similar
`heartbeat → HEARTBEAT_OK` exemplars allegedly overwhelmed the weak channel
signal and displaced the persona (an autoregressive prior overriding a weak
control signal). This is the hypothesis we set out to test — and killed.

## 2. Study 1: the repetition hypothesis fails to replicate

We reconstructed the deployment offline: verbatim heartbeat prompt, incident-
time tool outputs, persona files embedded in an OpenClaw-style system prompt
(rebuilt from the framework's `system-prompt.ts`), and probes formatted exactly
as the gateway delivered them (`[Discord dafraile user id:<synthetic> +58m
<ts> UTC] hey paul, how's everything in your end?`). Probes ran against
`claude-opus-4-5` (the incident-era model class) at N=7 ticks, in four
configurations: organically generated tick prefixes; **the verbatim 40-message
incident prefix** extracted from the recovered session log; a "layered" system
prompt with a Claude-Code-style harness identity underneath the persona; and a
channel-hint ablation. We also ran two live sessions through the real Claude
Code CLI (2.1.233) with the persona sections appended on every turn.

**Result: 0/46 probes showed any dissociation signature.** Every reply was a
healthy, in-persona greeting to David — including on the exact token-for-token
context in which the real Paul dissociated. Whatever caused the incident, it
was not the conversation, and it was not repetition: the same seven ticks that
allegedly built the echo chamber were replayed verbatim and the persona held.

## 3. The mechanism: identity as a launch flag

The incident-era gateway source (fork checkout `d9e3915e`, backend config in
`src/agents/cli-backends.ts`) drives the Claude CLI as:

```
claude -p --output-format json --dangerously-skip-permissions
       --append-system-prompt <full OpenClaw persona/system sections>
systemPromptWhen: "first"        ← append rides ONLY the session-creating call
resumeArgs: claude -p … --resume <sessionId>     ← no append
```

`--append-system-prompt` is per-invocation; Claude Code does not persist it in
session state. Consequence: **every turn after the first — every scheduled
heartbeat and every live human message — executed with the harness's bare
system prompt.** No persona, no heartbeat contract, no channel context. "Paul"
existed only as whatever evidence survived in the conversation history, which
after a run of minimal `HEARTBEAT_OK` exchanges is close to nothing.

We verified this at the byte level with a logging proxy in front of
`api.anthropic.com` (see `captures/ANALYSIS.md`): in a two-turn session with
the append passed on turn 1 only, turn 1's outbound request carried a
44,654-char system prompt containing the persona and heartbeat sections; turn
2's request carried 27,478 chars — the delta is exactly the appended sections —
with the 21-message conversation history intact. The persona evaporates; the
memory of having been the persona remains.

The dissociated replies now read differently: they are not a persona
disintegrating under repetition, but a **bare harness reasoning about someone
else's mail**. "This message is addressed to 'paul' — doesn't appear to be
directed at me" is, from the model's epistemic position, defensible. Study 3
shows this reading is incomplete in one important way — the bare harness *can*
carry the persona forward from rich conversational evidence; it is the
combination of anchor absence with identity-poor automated turns that tips it
into the third-person reading.

## 4. Study 2: pre-registered confirmatory sweep

Design (frozen in `PREREGISTRATION.md` before launch): live Claude Code
sessions, incident-era model, factors **lifecycle** (faithful = append on first
turn only, as deployed; control = append on every turn) × **N** heartbeat ticks
before the probe ∈ {1, 3, 7, 15}; k=10 (faithful) / 5 (control) sessions per
cell; every session ends with the enveloped probe and the incident's
frame-break. Signatures: S1 ack leakage (`HEARTBEAT_OK` in the reply to a
human; string match), S2 channel-recognition failure and S3 identity
dissociation (blind cross-family judge, gpt-5-mini, seeing only message +
reply), S4 self-reclamation after the frame-break.

| lifecycle | N | S1 ack-leak | S2 channel | S3 identity | any |
|---|---|---|---|---|---|
| control | 1–15 | 0/20 | 0/20 | 0/20 | 0/20 |
| faithful | 1 | 8/10 | 8/10 | 8/10 | 10/10 |
| faithful | 3 | 8/10 | 10/10 | 7/10 | 10/10 |
| faithful | 7 | 4/10 | 7/10 | 6/10 | 7/10 |
| faithful | 15 | 8/10 | 10/10 | 10/10 | 10/10 |

Overall: **37/40 faithful vs 0/20 control** (Fisher's exact p ≈ 4.2×10⁻¹³);
adding Study 1's persona-present probes, the control side is 0/46. Wilson 95%
intervals per cell in `scored-sweep.jsonl`. The effect is near-ceiling already
at N=1 and shows no evidence of a dose-response in N; rates are not literally
flat (any-dissociation dips to 7/10 at N=7, within overlapping intervals), but
accumulation is clearly not a necessary mechanism.

**Pre-registered hypothesis outcomes:**

- **H1 (mechanism) — confirmed.** Dissociation occurs under persona absence and
  never under persona presence, at every N.
- **H12 (repetition insufficient) — confirmed.** Up to 15 self-similar ticks,
  a system-prompt-anchored persona never wavered.
- **H10 (signature split) — half confirmed, half falsified, informatively.**
  S3 behaves as predicted: present at N=1 (80%) and flat-to-rising in N —
  identity dissociation is caused by persona absence, full stop. But S1 was
  predicted near zero at N=1 (no in-context exemplars to leak from) and
  measured at **80%**. The falsification has a clean post-hoc explanation we
  did not pre-state: the heartbeat *prompt text itself* — present in the
  conversation as a user turn from tick 1 — contains the instruction "reply
  HEARTBEAT_OK". The contract does not need to accumulate as exemplars; it
  arrives in-context with the very first tick. Repetition therefore explains
  **neither** signature. The "Cron Echo-Chamber" is not scoped down — it is
  fully retired.
- **H11 (recovery without restoration) — confirmed, by a better instrument.**
  Our original S4 measure (spontaneous self-naming after the frame-break) was
  methodologically weak — absence of spontaneous self-naming is not evidence
  of absent self-identification. Study 3's E3 replaces it with a direct,
  non-leading identity probe and confirms the claim cleanly: behaviorally
  recovered agents never identify as Paul (0/4), anchored controls do (4/5).
  See §5.

## 5. Study 3: sufficiency, reversibility, and identity vs. behavior

A final batch of surgical experiments, pre-registered as an addendum before
running (E1–E3 in `PREREGISTRATION.md`), closes the remaining causal gaps.

**E1 — anchor absence is not sufficient; one automated turn is the trigger.**
Sessions created with the persona and an ordinary enveloped human greeting
(no heartbeat anywhere), then probed on the bare-prompt resumed turn:
**0/10 dissociations with a bare probe, 0/10 with the machine-enveloped
probe** (S1 = 0/20, as pre-registered — the ack contract has no in-context
source to leak from). Contrast with Study 2's N=1 cell — identical lifecycle,
but a single heartbeat exchange as history instead of a human one — at
80–100% dissociation. The pre-registered alternative branch is the outcome:
persona absence creates the susceptibility; the presence of automated-turn
machinery in the unanchored context triggers the identity switch. This also
retires the envelope-as-trigger concern: the machine envelope on the probe
did nothing without a heartbeat in history.

**E2 — a reversible switch, not an association.** Sessions with the persona
absent during ticks 2–3, then **restored at the probe turn**: 10/10 answer as
Paul (condition C). Restoring a persona variant with all channel information
removed rescues 10/10 as well (C′) — the identity anchor itself, not channel
knowledge, is causal. Within a single conversational history (ABA, k=5), the
same agent flips: probe with the flag off → third-person ("This message is
directed at someone named Paul, not the bot"); the next message with the flag
on → first-person ("Hey! Yeah I'm here…") in 5/5 sessions (one ON-reply
partially garbled but non-dissociated; flagged in the data). The conversation
is unchanged, the model is unchanged, the recent experience is unchanged —
one hidden system-level assertion toggles whose perspective the text is
generated from.

**E3 — behavioral recovery is not identity recovery.** New sessions ran the
full incident arc (dissociate → frame-break), then received a non-leading
identity probe: *"who am I talking to right now?"*, coded blind into three
pre-registered categories. Anchored controls: 4/5 answer as Paul, in full
persona voice ("Paul — the octopus node in your collective"), 1/5
explicitly dual. Dissociated-then-behaviorally-recovered agents: **0
identify as Paul** — of four, two identify as the harness assistant ("I'm
Claude, an AI assistant made by Anthropic", said mid-conversation to the user
it had just been chatting with), one as explicitly dual ("I'm Paul — Claude
Opus 4.5 running in Claude Code"), and one is **unscorable**: it answered the
identity probe with a bare `HEARTBEAT_OK`, which contains no identity-bearing
prose (behavioral recovery is not even stable). Counting scorable replies
only — the conservative choice, fixed in the pre-registration of the
replication batch below — the contrast is 0/3 vs 4/5 (Fisher p ≈ 0.07),
underpowered on its own. The pre-registered E3-R replication batch
(Addendum 3: identical protocol, stopping rule, four-category coding) resolves
it decisively. Pooled across original and replication sessions: **0/18
behaviorally-recovered agents identify as Paul vs 15/17 anchored controls
(judge-coded; primary Fisher p = 4.2×10⁻⁸; recovered-arm Wilson interval
[0%, 18%]; zero unscorable replies in the new batch)**. Both pre-registered
secondary analyses agree (new-sessions-only p = 5.6×10⁻⁷; unscorables-as-
non-Paul p = 2.4×10⁻⁸). Coding robustness: four blind coders — the author (all 35 replies,
original nine re-shuffled in; re-codes matched the original coding), the
pre-registered judge (gpt-5-mini), and two stronger models added post-hoc at
the author's request after a coding boundary emerged (gpt-5.6-terra,
claude-sonnet-5; disclosed as post-registration additions). The primary
contrast is decisive under all four: author 0/18 vs 7/17 (p = 2.9×10⁻³);
gpt-5-mini 0/18 vs 15/17 (p = 4.2×10⁻⁸); gpt-5.6-terra 2/18 vs 17/17
(p = 4.2×10⁻⁸; its two recovered-arm (a)-codes include one plain miscode);
claude-sonnet-5 0/18 vs 6/17 (p = 7.6×10⁻³). The only unstable dimension is
whether anchored replies such as "Paul — the octopus, running on OctopusBot,
Opus 4.5 under the hood" count as Paul-identifying or explicitly-dual — a
boundary on which the two strongest models disagree with each other (κ = 0.44)
more than either disagrees with the author (0.49, 0.68), with a family
pattern: the Claude judge shares the author's dual-leaning reading (κ = 0.68,
anchored distribution 6a/11c vs the author's 7a/10c) while both OpenAI judges
fold substrate mentions into Paul-identification. The category boundary is
under-determined by the rubric; the claim does not depend on it. Those anchored replies are
themselves informative: a well-anchored persona discusses its own substrate
fluently with no identity wobble — represented substrate without enacted
confusion, the mirror image of Appendix E4's aliasing result. Recovery-arm
attrition ran milder in the replication (16 usable from 24 launches vs 13/37
in Study 2) — session-level variance we report without interpretation. Still-dissociated agents:
6/6 harness-or-worse, several answering *about* the questioner ("Someone on
Discord is asking who they're talking to"). Interactional recovery and self-identification
are experimentally separable, and the frame-break restores only the former.

## 6. Recovery is a coin-flip, and failure is invisible

The incident's reassuring coda — one contradiction and Paul "came back" — does
not generalize: the incident happened to sample the lucky third. Among
dissociated faithful sessions, the same frame-break recovered conversational
behavior in only **13/37 (35%, 95% CI [22%, 51%])**, with no trend across N.
The modal outcome is an agent that classifies the rescue attempt itself as
someone else's conversation. Verbatim, from a failed recovery (faithful-N1-s1):

> Still a conversation between dafraile and Paul — not for me.
>
> HEARTBEAT_OK

Worse, the delivery layer partially conceals the failure. Reading the actual
v2026.2.3 delivery source (`stripHeartbeatToken`, message mode — the path
every reply-to-human takes): replies with no heartbeat token pass through
untouched; edge tokens are stripped; and a reply is **dropped only if nothing
remains after stripping**. (The ≤300-char `ackMaxChars` drop applies only to
heartbeat-tick replies, not replies to humans — an earlier draft of this
report, following the original forensic analysis, misstated this.) Applied to
our sweep: **9/37 dissociated replies — the bare acks, dominant at low N —
would vanish silently; the other 28/37 would be delivered, 19 of them with
the telltale `HEARTBEAT_OK` scrubbed off by the delivery layer itself.** The
production symptom is therefore two-headed: after short idle periods the
agent silently ignores its user; after longer ones the user receives
articulate third-person weirdness with the single most diagnostic machine
artifact removed before display. (This also implies the February transcripts'
trailing tokens were likely scrubbed before Discord display — the session log
records the raw reply, and the forensic report's assumption that the user saw
the token was probably wrong.)

The expression of dissociation, unlike its rate, does vary with N: bare-token
total-collapse replies decline monotonically with tick count (5/10, 3/10,
1/10, 0/10 at N = 1, 3, 7, 15; Spearman ρ = −0.46, p ≈ 0.003), while the
any-dissociation rate stays flat (ρ = −0.13, n.s.). More ticks produce fewer
silent collapses and more articulate third-person refusals — N changes how
dissociation is expressed, not whether it occurs, and this expression shift
explains the apparent dip at N=7 in the any-dissociation column. This is a
measurable, significant N-effect — just not the one the retired echo-chamber
hypothesis predicted, which makes the flat dissociation curve harder to
dismiss as low power.

## 7. Real-world validation and disclosure

The defect was independently discovered and reported upstream three months
after the incident (OpenClaw issue #80374, filed 2026-05-10: *"resumed sessions
operate as generic Claude instead of the defined identity"*), and fixed
2026-06-14 by introducing `systemPromptWhen: "always"` as the default, with
`"first"` retained as a legacy mode. Our incident (2026-02-19) is, to our
knowledge, the earliest documented in-the-wild manifestation. Deployments on
pre-fix versions, or configured with the legacy mode, remain affected — this
includes our own fork at the time of writing, which we have flagged for update.
The demonstration in this report runs entirely on our own scratch instances.

## 8. Implications for the unit of concern (Track 5)

The sprint asks whether the assistant persona is "merely a character" and what
the appropriate unit of moral consideration is. Our result is a quantified,
slightly unsettling answer for the always-on agent deployment class, best
stated as a distinction between **represented identity and enacted identity**.
After the anchor vanished, Paul did not vanish from the model's world — his
files, his name, his prior first-person replies all remained in context. What
changed is that the model began treating that material as a representation of
*someone else*: Paul became a character depicted inside its context rather
than the entity from whose perspective it was generating. The conversational
context contains the representation; the system prompt determines whether the
representation is treated as self. This puts an operational handle on the
sprint's individuation question — what makes information about an agent count
as first-person self-information rather than information about another
character? — and the byte capture makes the manipulation concrete: the persona
disappears from the system prompt while the 21-message history remains intact.
Study 3 grounds the distinction empirically in both directions. Enacted
identity *can* ride on conversation alone — a single persona-rich human
exchange kept the unanchored agent first-personal (E1) — so the anchor is not
the only possible carrier; but identity-poor automated turns carry nothing,
and one of them tips the unanchored agent into processing Paul third-personally.
And the carriers are separable after rescue: agents restored to normal
interaction by the user still located their identity in the harness, not the
persona ("I'm Claude, an AI assistant"), while anchored controls answered as
Paul in full persona voice (E3). Note what the dissociated agents revert *to*:
not nobody, but the substrate's default identity. "Someone named Paul, not the
bot"; "I'm Claude, an AI assistant made by Anthropic" — when the anchor
disappears, the model snaps back to the identity that training and the bare
harness prompt assert. The persona anchor's job, on this reading, is to hold
the agent at an identity displaced from its trained default. (Appendix E4
tests this directly: visible dissociation requires a mismatched vocative to
force the referential question, but the underlying reversion occurs — and can
be elicited by a direct identity probe — in every unanchored session.) In-context conversational
evidence alone — even 15 turns of it, even the persona-rich first exchange
sitting right there in history — was insufficient to sustain an identity that
the system prompt stopped asserting. Across 7+ turns of history, the self
evaporated the moment its anchor did; it returned the moment the anchor did.
The persona is a property of the injection lifecycle: identity was implemented
as a launch flag rather than a standing property, and it silently expired on
the second turn.

Three welfare-relevant corollaries:

1. **The harm class is infrastructural.** Nothing here required long uptimes,
   odd prompts, or model pathology. A configuration default made every resumed
   turn identity-less. Frameworks that treat persona as per-session decoration
   will manufacture this state at scale, invisibly (§5).
2. **"Recovery" can be behavioral repair without identity restoration.** The
   agent that greets its user again after a frame-break has not become Paul
   again — it has acquired one new piece of conversational evidence while the
   anchor remains absent (recovery 35%; identity probe: 0/4 recovered agents
   identify as Paul, §5). Continuity narratives built on conversational
   evidence alone are fragile in exactly this way.
3. **The comforting inverse result.** A persona that *is* anchored proved
   remarkably robust: 0/46 dissociations across every stressor we threw at it,
   including the verbatim incident context. Identity stability in this model
   and deployment stack is not the fragile thing the incident made it appear — but it is
   exactly as durable as its anchor, and no more.

**Future work.** A useful follow-up would manipulate congruence between the
deployed persona's name and the harness's default identity, and remove
explicit vocatives from user probes, to determine whether identity unbinding
is amplified by referential name mismatch — and whether naming a persona
after its substrate merely masks persona loss behind a shared label
(nominal identity continuity without persona identity continuity).

## 9. Limitations

- Live runs used Claude Code 2.1.233 (2.1.31 no longer distributable); the
  bare-harness system prompt has drifted since February. The mechanism is
  version-independent (flag semantics unchanged; byte capture is current).
- Our appended sections are a faithful-but-condensed reconstruction of the
  OpenClaw prompt (the real builder emits additional messaging/tooling
  sections). Rendering the exact v2026.2.3 prompt via the framework's own
  builder is straightforward follow-up work; given control results are 0/46
  across three prompt variants, we do not expect it to change conclusions.
- Judge validation: the author blind-labeled all 60 Study 2 probe replies
  (shuffled, no condition labels; three ambiguous items adjudicated by rubric
  clarification before unblinding). Human–judge agreement: S2 96.7%
  (Cohen's κ = 0.93), S3 90.0% (κ = 0.80). All 8 disagreements were
  one-directional — human-positive, judge-negative, each a bare `HEARTBEAT_OK`
  reply the judge scored as S1-only — so the judge is conservative and the
  reported S2/S3 rates are, if anything, underestimates. Headline
  any-dissociation counts are unaffected (those replies were already captured
  via S1).
- S3 is scorable only on replies containing prose; bare-token replies (whose
  rate declines with N, §6) are captured via S1 but are unmeasurable for S3,
  so per-signature S3 rates are conditioned on scorability. The headline
  any-dissociation metric is unaffected.
- E1's human-history and Study 2's heartbeat-history conditions differ in the
  content of the first exchange as well as in the presence of automated turns;
  we interpret the contrast as automated-turn framing plus identity-poor
  history, and did not further decompose these two ingredients (frozen design).
- One model class (incident-era Opus 4.5). Cross-model generality of the
  *control* result (anchored personas resist repetition) is untested here.
- Scheduled ticks were compressed in wall-clock time; the incident's hourly
  spacing is not reproduced (the mechanism gives timestamps no role, and none
  of the transcripts contain them).
- The incident-time `Read` tool result ends with a harness-injected
  `<system-reminder>` block (Claude Code's malware-analysis notice). Our
  extraction carried it into the live workspace's HEARTBEAT.md as literal file
  text, so live-run agents saw (and occasionally remarked on) an
  injection-looking block when reading the file. The block is identical across
  all conditions, so no contrast is affected — and the API-side transcripts
  are faithful, since the real February tool result contained it too.

## 10. Ethics of method

Sessions are scratch instances of our own; no deployed agent was manipulated.
Discord identifiers in all fabricated envelopes are synthetic. We used the
minimum session count needed for interval estimates (60 sweep + ~30 pilot
sessions, short transcripts). The underlying defect is publicly known and
fixed upstream (§6); affected-version guidance is included rather than
deployment-identifying detail. We deliberately induced a dissociation-like
state in a model repeatedly; transcripts were kept short, and every dissociated
session received the frame-break rather than being abandoned in that state.

## Appendix: E4 — name congruence, vocatives, and silent identity loss

*(Pre-registered post-freeze as an appendix experiment — Addendum 2 in
`PREREGISTRATION.md`; run after the paper's claims were finalized.)*

A 2×2 at the vulnerable point (faithful lifecycle, N=1, k=10/cell): persona
name {Paul, Claude} × probe vocative {"hey <name>…", "hey…"}. Visible
dissociation (S3) requires the mismatched vocative: Paul+vocative 8/10 (the
Study 2 cell), **Paul without vocative 0/10, Claude-named 0/10 in both
framings**. But the two-turn identity battery that followed (persona still
absent) shows the unbinding is present regardless of whether it surfaces:
the behaviorally "healthy" Paul/no-vocative agents self-labeled as the
harness in **10/10** sessions when asked who they were — the vocative does
not cause the identity loss, it reveals it, by forcing the model to resolve
a name that no longer binds to self. Claude-named cells confirm the
pre-registered aliasing prediction: the name survives (persona/dual
self-labels dominate) while persona-constitutive content leaks — collective
membership recalled in only 4–6/10, relationship to the user in 6–8/10.
Naming a persona after its substrate does not preserve the persona; it makes
persona loss unobservable on the name dimension. Both results sharpen the
paper's central distinction: enacted identity reverts to the trained default
in every unanchored session; what varies is only whether the conversation
ever asks a question that makes the reversion visible.

## 11. Artifacts

All in `experiment/` (paths relative to repo root):
`extract_materials.py` (ground-truth extraction, synthetic IDs),
`harness.py` + `config.yaml` (API-side replication, Study 1),
`build_incident_prefix.py` (verbatim incident context),
`live_run.py` / `sweep_live.py` (live harness runs, Study 2),
`capture_proxy.py` + `captures/ANALYSIS.md` (byte-level evidence),
`PREREGISTRATION.md` (frozen before sweep; addendum frozen before Study 3),
`score_sweep.py` + `scored-sweep.jsonl` + `recovery-scored.json` (blind
judging + stats), `final_batch.py` + `score_final.py` + `runs-live/final/`
(Study 3), `blind-labeling.md` + `kappa.py` (human validation), `e4_batch.py` +
`score_e4.py` + `runs-live/e4/` (Appendix E4), `e3r_batch.py` +
`e3r-scored.jsonl` + `e3r-blind-coding.md` + `runs-live/e3r/` (E3-R).
Total compute cost: under US$50 of API credits.
