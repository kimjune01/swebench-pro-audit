# Adversarial sniff v2 of the audit method (codex / gpt-5.5, 2026-06-08)

Second independent adversarial pass, on spec v2. Verbatim below. Net: v2 narrows the attack surface but the codebase-ambiguity classes remain judgment-laden (plurality != underdetermination), and the construct-validity frame over-excludes real solver context (issue thread, PR/commit history, CONTRIBUTING, test names). The mechanically-unimpeachable spine is KNOWN_BAD + AMBIGUOUS-airtight; the rest is a disciplined hypothesis pending independent raters + comparability criteria + sampling.

---

**Verdict**

v2 narrows the attack surface, but it does not close the two v1 holes as a result. It closes them as a design, conditional on work not yet done. `docs/AUDIT-CHECKLIST.md / Current pilot vs the bar` still says the repo lacks unbiased sampling, multi-rater construct-validity coding, reps, and independent adversarial pass. So the correct status is still: promising instrument, not proven benchmark result.

1. **Hole #1: prose-only determinacy**

Partly closed in definition, not closed in adjudication.

`docs/ADMISSIBILITY-SPEC.md / KNOWN_AMBIGUOUS / Construct-validity frame` now says the solver has prose plus codebase-at-one-commit. That fixes the obvious v1 defect: codebase conventions can determine behavior.

Leak: `DETERMINED-codebase` still depends on deciding that a convention is “consistent, binding,” while `AMBIGUOUS-codebase` depends on deciding that coexisting patterns are “drift,” “mid-migration,” or “conflicting.” From a single snapshot, that is often not mechanically decidable. A snapshot can show plurality; it rarely proves which pattern is authoritative.

So v2 no longer ignores the codebase. It relocates the hard judgment into “binding convention” versus “non-binding drift.”

2. **Hole #2: auditor-constructed R2**

Not fully closed.

`docs/ADMISSIBILITY-SPEC.md / Per-cell label` improves the witness burden. `AMBIGUOUS-airtight` can be strong if it really is an absent arbitrary constant found only in gold/test. `AMBIGUOUS-borderline` is escalated to a panel. Good.

Leak: `AMBIGUOUS-codebase` can still be auditor-constructed. “Cite ≥2 coexisting patterns + prose silence” proves plurality, not underdetermination. The auditor still selects which two locations conflict, whether they are actually comparable, whether one is deprecated, whether one is test-only, whether one is domain-specific, and whether project norms tell you which wins.

That is the old R2 problem with better paperwork.

3. **New grid hole: smuggled judgment**

The smuggler label is `DETERMINED-codebase` / `AMBIGUOUS-codebase`, as a pair.

`DETERMINED-codebase`: “consistent, binding convention.”
`AMBIGUOUS-codebase`: “non-binding — drift, mid-migration, or conflicting call sites.”

The distinction is not grep-checkable. Grep can show examples. It cannot show binding force. “Consistent” may be measurable; “binding” is interpretive. “Drift” may be visible; “non-binding” is interpretive. A repo snapshot alone usually cannot distinguish:

- legitimate old/new migration,
- tolerated inconsistency,
- context-specific variants,
- dead code,
- API evolution with clear intended target,
- maintainer preference encoded outside the touched files.

The grid makes the judgment explicit, but it does not remove it.

4. **Construct-validity frame overexcludes solver context**

`docs/ADMISSIBILITY-SPEC.md / Construct-validity frame` says solver materials are “prose + codebase at one commit, nothing else.”

That is too narrow if the benchmark task, as delivered to real solvers, includes or implies issue thread, PR title/body, commit history, CONTRIBUTING/docs, test names, changelog, repo documentation, or local conventions encoded outside the touched area. `README.md / Layout` says receipts include `spec.md`, `gold.diff`, `hidden_test.diff`, and `fail_to_pass.txt`; it is not clear that `spec.md` preserves the full issue context a real benchmark participant sees.

Where it overclaims: any “AMBIGUOUS because prose silent” conclusion where the missing rule is recoverable from project docs, issue discussion, adjacent commits, migration PRs, naming conventions, or contribution guidelines. v2’s frame can fairly define a stricter instrument, but then the claim must be: “underdetermined under our reduced solver-material model,” not “underdetermined for a real solver/agent.”

5. **Positive-evidence guard**

It helps, but it can be gamed.

`docs/ADMISSIBILITY-SPEC.md / Positive-evidence-only guard` prevents the weakest move: “I failed to find the rule, therefore ambiguous.” `UNKNOWN` is a real improvement.

But `AMBIGUOUS-codebase` can manufacture ambiguity by citing two conflicting locations. Two locations are cheap in large codebases. Unless the method requires comparability proof, recency analysis, ownership/context matching, and exclusion of deprecated/dead/test-only/examples code, the auditor can turn ordinary codebase heterogeneity into “drift.”

The guard stops ignorance-to-indictment. It does not stop cherry-picked-conflict-to-indictment.

6. **Codex contamination**

It bites less in the finite grid than in v1, but it still bites.

`docs/ADMISSIBILITY-SPEC.md / Exhaustive labeling of a finite grid` contains the risk by forcing every fixed test behavior to get a label. That prevents free-form cherry-picking of only attractive failures.

But the labeler is still codex, with possible exposure to repo, benchmark, gold patches, or conventions. Contamination can affect:

- which codebase precedents it notices,
- whether it treats a convention as binding,
- whether it recognizes gold-shaped intent,
- whether it classifies conflict as drift,
- whether it escalates to `UNKNOWN` or `AMBIGUOUS-borderline`.

Finite labeling gives completeness over rows. It does not give independence over judgments. `docs/AUDIT-CHECKLIST.md / Construct-validity coding` still requires ≥2 independent raters and κ; that is the actual containment mechanism, and it is unchecked.

7. **Weakest remaining link**

The weakest link is the decidability of `DETERMINED-codebase` versus `AMBIGUOUS-codebase` from a single repo snapshot.

Most likely successful rebuttal:

“You have shown codebase plurality, not benchmark underdetermination. A competent solver would infer the intended convention from issue context, repo docs, migration direction, touched files, naming, or normal maintenance practice. Your grid makes the ambiguity claim look mechanical, but the load-bearing move is still auditor judgment about which conventions bind.”

Does v2 survive that? As a preregistered design, maybe. As a proven result, no. It needs independent codebase-aware raters, explicit comparability criteria for conflicting locations, and reporting of agreement/disagreement before `KNOWN_AMBIGUOUS` becomes more than a disciplined hypothesis.
