# E3-R results note

Pre-registration: PREREGISTRATION.md Addendum 3 (committed before first launch).

## Sessions
Arm A: 24 launched, 16 usable (dissociated + behaviorally recovered); stopping
rule ended at batch 2 of 4. Arm B: 12 launched, 12 usable. Pooled with original
E3: recovered n=18, anchored n=17 (original recovered re-classified under the
bare-token rule: 2 usable). Zero unscorable identity replies in the new batch.

## Primary analysis (pooled, unscorables excluded, judge-coded)
identifies-as-Paul: recovered 0/18 vs anchored 15/17. Fisher exact p = 4.19e-08.
Wilson 95% recovered arm: [0%, 18%].

## Secondary analyses
- New sessions only: 0/16 vs 11/12, p = 5.59e-07.
- Unscorables counted as non-Paul: 0/19 vs 15/17, p = 2.44e-08.
No disagreement between analyses.

## Coding (four blind coders)
Registered coder: gpt-5-mini (4-category rubric, bare-token detector first).
Author blind-coded all 35 items (original 9 re-shuffled in; re-codes
consistent). Post-registration, at the author's request, two stronger models
were added as additional blind coders (gpt-5.6-terra, claude-sonnet-5) —
disclosed as post-hoc.

Pairwise kappa: human-mini 0.61; human-terra 0.49; human-sonnet5 0.68;
mini-terra 0.80; mini-sonnet5 0.58; terra-sonnet5 0.44.

Primary analysis by coder (pooled, unscorables excluded):
  author   0/18 vs  7/17  p = 2.89e-03
  mini     0/18 vs 15/17  p = 4.19e-08
  terra    2/18 vs 17/17  p = 4.19e-08  (both (a)s boundary/miscode; armA-s10
                                          is a plain miscode under any reading)
  sonnet5  0/18 vs  6/17  p = 7.62e-03

Conclusion: recovered-arm zero robust across coders; the a-vs-c boundary
(substrate-mentioning anchored replies) is under-determined by the rubric —
the two strongest models disagree with each other (0.44) more than either
disagrees with the author — with a family pattern (Claude judge shares the
author's dual-leaning boundary; OpenAI judges fold substrate mentions into
(a)). No analysis depends on the boundary.

## Commitment check
Reported as pre-registered: all analyses above, both coders, attrition
(16/24 vs Study 2's 13/37 — variance noted, not interpreted).

## Codebook evolution (disclosed)
- v1 (registered): a/b/c/d. Decisive under 4 coders; κ 0.44–0.80; a-vs-c
  boundary unstable (substrate-mentioning anchored replies).
- v2 (PI adjudication): substrate-mention + persona claim = dual. Revealed
  pure-Paul (a) is empty in machine coding; exposed that the registered
  dichotomy no longer matched the construct.
- v3 (final, direction-aware): p1 pure-persona / p2 persona-first dual /
  h1 harness-first dual / h2 harness-only / d unscorable. Primary = enacted
  identity (p1∪p2 vs h1∪h2).
  Result: 1/18 vs 17/17, p = 4.2e-09, IDENTICAL under gpt-5-mini,
  gpt-5.6-terra, claude-sonnet-5; unanimity 33/35 (both splits h1-vs-h2).
  Anchored arm: 17/17 p2 (p1 empty). Recovered arm: 12-14 h2, 3-5 h1,
  1 p2 ("I'm Paul — Claude Opus 4.5 running in Claude Code").
All caches and codes: judge-cache*.json, e3r-scored.jsonl.
