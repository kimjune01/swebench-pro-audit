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

Reported as a **separate** axis, never merged into the per-behavior 4.9% / 8.9% spine. Measured overlap
(these union/overlap counts predate the two-expert re-grounding that took the per-behavior spine 54→65;
the ~20% candidate ceiling is unchanged in magnitude, exact union pending a refresh):

- per-behavior PROVEN spine = 65 (was 54); opus design-divergent = 118; **union ≈ 147 (~20%)**.
- Of the 118 divergent, **46 are per-behavior ENTAILED** — tasks the coverage screen called covered but
  whose *design* is underdetermined. That ~6% is divergence's genuine net-new contribution; the rest is
  the same underdetermination the per-behavior screen already saw, viewed at design granularity.

### Can we publish the 20%?

The **20.2% union is the candidate ceiling, but it is tier-mixed and most of its mass is not yet
receipt-grade**, so it is publishable only with the tiers shown, not as one flat number:

- **~36 (4.9%) carry mechanical receipts** a skeptic checks without trusting us: airtight (grep), graded
  patch (official grade), tutao (prose clause). This is the receipt-defensible floor today.
- **29 (4.0%) rest on the two-expert standard** — codex constructs an existence proof (prose plurality or
  source plurality), an independent cross-family refuter (opus) tries to kill it and fails (29/41 survive),
  and a symmetric advocate pass recovers no missed splits (κ=0.52, all disagreement skeptic-stricter);
  two-model verified, but the standard itself is a disclosed stance.
- **~93 rest on single-rater opus design-divergence** — a disciplined hypothesis whose "receipt" is one
  model's design pair, not a checkable artifact. **This is the mass that makes 20% not yet defensible.**

To publish 20% with receipts, the divergent tier must be upgraded from single-rater opinion to a checkable
artifact, two options:
1. **Panel** — k decontaminated from-prose attempts; divergent iff they scatter / few pass. Receipt = the
   attempts themselves (the disagreement is the artifact). EC2, the canonical PROVEN instrument.
2. **Graded-patch-for-divergence** — produce the alternative design R2, have two blind raters call it
   prose-faithful, run the official grader, show it fails. Receipt = `r2.diff` + grade. Same machinery
   that proved the 5 prose-affirmative cases, pointed at the design grain; the strongest receipt (a real
   prose-faithful patch the bench rejects).

Until one of those runs, the honest published numbers are: **4.9% receipt-mechanical, 8.9% granting the
two-expert tier (two-model verified, κ=0.52), ~20% candidate union (single-rater divergent, panel-pending)**,
with a looser prose-literal-silence diagnostic at ~69%. Not a sum; not a concurrence; not yet panel-proven.

## Scoring: the aspiration, what binary measures, what we propose

**The aspiration, for a harness, is full automation.** The point of an agent harness is to resolve an
issue end to end with no human in the loop. Underspecified prose is the structural ceiling on that goal.
Where the prose determines the fix, automation can in principle reach it, and the residual is a capability
gap that shrinks as models improve. Where the prose does not determine it, no model closes the gap from the
prose alone, because the missing choice is not information the agent can derive; it has to come from a
human. So the divergent fraction is not a capability gap better agents erase. It is the part of the
benchmark that cannot be fully automated by construction, because the specification is not there to
automate against. A score should make that distinction visible, not bury it under a boolean.

**What the binary score measures today.** SWE-bench Pro collapses the question to a coin flip: an instance
counts as resolved only if the patch reproduces one maintainer's opinionated choices closely enough that
every held-out assertion fires. Three moves hide inside that boolean. It treats a merged commit as ground
truth, when a merge is one fallible opinion shaped by taste, time pressure, and the occasional plain
mistake, and the bench has no channel to notice when the maintainer was wrong. It is all or nothing, so a
patch that satisfies eleven of twelve graded behaviors scores the same as one that fixed nothing. And it
fabricates a finish line at one hundred percent that the maintainer's own workflow never contains, since a
careful reviewer reads even a fully passing PR for everything the tests did not check. Together these
amplify the specification lottery: a single underdetermined assertion, where the maintainer's unstated
preference might itself be the worse option, sends an otherwise correct fix to zero.

**What we propose.** Score each instance as a float in [0, 1], the fraction of the new behaviors a task
introduces that the patch achieves, net of regressions:

> score = clamp₀₁( (FAIL_TO_PASS passed − PASS_TO_PASS regressed) / FAIL_TO_PASS introduced )

computable today from the grader's per-test `_output.json`. Read one minus the score as residual work: how
much a maintainer must still do to reach a mergeable state, which is the production value the agent
provided. For a harness builder the residual splits in the way that matters most: on a determinate task it
is **capability residual**, which a better model erases; on a divergent task it is **specification
residual**, which no model erases, because the spec is missing and a human must supply the choice. The
float together with the divergence label tells you which wall you are against. The reading stays honest
about its limits. It is a lower bound, since it counts only the residual the tests can see and a careful
review survives even a perfect score (one hundred percent means "no test caught anything," not "correct").
It weights every assertion equally, though a regression can cost more than an un-done behavior and a
divergent gap can cost only a one-line clarification. It does not resolve the underdetermination, so it is
mitigation, not cure. But it is strictly less imperfect than a binary that discards the determinate
majority over one pluralistic convention, and it matches the workflow it models: the maintainer reviews
regardless, and their effort falls continuously with the gap instead of dropping to zero at a finish line
the binary invents. Canonical case: `qutebrowser-e34dfc68` passes 233/248 and loses on a 15-case DNS matrix
the prose never specifies; binary reads `0`, the float reads the determinate work done. Report the
determinacy-weighted mean of these per-instance floats, and publish the divergent set so consumers can
score on the determinate subset, or at least know which residual is spec-missing rather than
capability-missing.

**What the score actually measures: automation afforded.** Put the pieces together and the float reads as
one quantity, the level of automation a task admits, which factors as *the determinacy the prose affords
times the capability of the model and harness.* A fully determinate task has an automation ceiling of one,
so the score is pure capability. A divergent task has a ceiling below one, so even a perfect harness tops
out short of full automation, and the remainder is not failure but **elicitation**. The natural, correct
behavior of an automated agent against underspecified prose is to implement everything the spec determines
and leave the unstated choice for the maintainer to resolve at review time. An incomplete implementation
there is the specification working as written, surfacing its own gap for human elicitation, not the agent
falling short. So the score measures how far prose-times-capability got, and the divergence label says
whether the gap that remains is waiting on a better model or on a human to finish specifying. That is the
right target for anyone building a harness: full automation is the aspiration, and this number reports the
fraction of it the prose actually permitted.

**And you cannot factor it from the score alone.** Automation-afforded is a product, and a product hides
its factors. A low float could be an underspecified task or an underpowered harness, and the number by
itself cannot tell you which. Separating them requires measuring one factor independently, which is what a
determinacy audit does: the per-instance determinacy label supplies the prose term, so the score's
shortfall can be attributed to the prose or to the harness. Without it, every reported Pro number conflates
the two, crediting the harness with whatever determinacy the prose happened to supply and faulting it for
whatever the prose withheld. That confound, unfactorable from the leaderboard and visible only once the
audit is done, is the reason this repo exists.
