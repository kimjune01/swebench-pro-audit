# The determinacy axis: design-level divergence

A second axis, orthogonal to the per-behavior coverage screen. The coverage screen asks, behavior by
behavior, *does a prose clause cover this?* This axis asks the admission-standard question directly:
**would competent engineers, from the prose plus ordinary engineering convention, converge on the
test-passing solution — or do faithful readings diverge and the held-out test pin one?**

A task can be per-behavior ENTAILED yet **divergent** (the coverage screen's blind spot), and a task can
be broad yet **determinate** (a uniform 106-file rename converges). Breadth is a triage pre-filter, never
the label.

## Method (rater form, blind to gold + test)

Each rater sees only the prose and answers: `determined?` + two concrete incompatible faithful
implementations `design_A` / `design_B` + the `selecting_clause` that would force one (or null). A task is
called divergent only with `determined=false`, concrete incompatible A/B, and no selecting clause.
Non-labels (insufficient on their own): many files, new API/module, large LOC, feature-shaped, model
failure, auditor surprise.

## Result (n = 728) and the rater asymmetry

Run blind by two raters (opus, codex). The raw split is the load-bearing finding, so it is reported in
full rather than hidden behind an AND-gate:

| measure | rater | count | of N | what it is |
|---|---|---:|---:|---|
| **design-level divergence** | opus | **118** | **16.2%** | won't converge *even with ordinary convention* — the admission-standard question |
| prose-literal silence | codex | 505 | 69.4% | ≥1 prose-silent discrete choice; a looser diagnostic that **overlaps convention-resolved tasks** |
| AND-gate | both | 115 | 15.8% | **opus-anchored**, not two-rater concurrence |

**The AND-gate is not two-rater concurrence.** codex's positive rate is so broad (~69%) that its
agreement on an opus positive means only "not filtered by the loose rater," not independent confirmation
— κ would be near zero. So the headline is the opus number under the convergence-with-convention
standard, reported as a **single-rater, disciplined-hypothesis** estimate, *not* a concurrence.

This converged with codex by discussion (it concurred): *report design-level divergence at the
convergence-with-convention granularity; report prose-literal silence separately as a looser upper bound.*

## Honest caveats (both directions)

- **Over-flag (codex):** prose-literal silence counts every micro-choice (a `0755` dir perm, a default
  bool) the prose doesn't spell out — most of which ordinary convention resolves. That is why ~69% is a
  diagnostic upper bound, not a divergence rate.
- **Under-flag (opus):** the convergence standard lets a rater resolve a choice by convention. That is
  correct only for **ordinary** convention any engineer shares. Where a choice is resolvable only by
  **repo-specific** convention the blind-prose rater cannot see, calling it determined would under-count —
  that case belongs to the codebase-plurality axis, not "determinate." The 16% carries this risk.
- **Not PROVEN.** The rigorous instrument is the panel: k decontaminated from-prose attempts; divergent
  iff low lenient convergence **and** attempts split across incompatible readings. That is EC2-pending.
  Until it runs, 16% is a disciplined hypothesis, single-rater.

## Relation to the per-behavior spine (no double-counting)

Reported as a **separate** number, never merged into the per-behavior 4.9% / 12.2%. Measured overlap:

- per-behavior PROVEN spine = 89; opus-divergent = 118; **union = 180 (24.7%)**, overlap = 24.
- Of the 118 divergent, **46 are per-behavior ENTAILED** — tasks the coverage screen called covered but
  whose *design* is underdetermined. That ~6% is divergence's genuine net-new contribution; the rest is
  the same underdetermination the per-behavior screen already saw, viewed at design granularity.

So the determinacy-failing union, overlap-corrected and tier-honest: **~12% per-behavior PROVEN + ~6%
net-new design-divergent (single-rater hypothesis) ≈ ~18%**, with a looser prose-literal-silence
diagnostic at ~69%. Not a sum; not a concurrence; not yet panel-proven.

## Scoring implication: float, not pass/fail

Divergence is *why binary scoring misleads.* A `resolved` boolean throws the whole instance away over a
single missed pluralistic convention: a patch that satisfies 11 of 12 graded behaviors scores the same as
one that fixed nothing. Recommended instead, per instance:

> **score = clamp₀₁( (FAIL_TO_PASS passed − PASS_TO_PASS regressed) / FAIL_TO_PASS introduced )**

computable today from the grader's per-test `_output.json`. It decouples the determinate majority from the
divergent minority — a divergent assertion costs only its `1/N` share instead of the whole instance.
**Imperfect** (it weights all assertions equally and does not *resolve* the underdetermination — mitigation,
not cure), but strictly **less** imperfect than binary. Canonical case: `qutebrowser-e34dfc68` passes
233/248 and loses on a 15-case DNS matrix the prose never specifies — binary `0`, float ≈ the determinate
work done. Report the determinacy-weighted mean of these per-instance floats, and publish the divergent
set so consumers can score on the determinate subset when they want a reasoning signal.
