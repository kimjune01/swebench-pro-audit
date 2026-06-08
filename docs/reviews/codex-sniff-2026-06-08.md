# Adversarial sniff of the audit method (codex / gpt-5.5, 2026-06-08)

Independent adversarial review (the checklist's box 8), run by pointing codex at the spec/README/checklist/prior-art + one attribution and asking it to REJECT the method. Verbatim critique below; the two load-bearing holes (prose-only determinacy; auditor-constructed R2) are recorded in ADMISSIBILITY-SPEC.md and gate any ambiguity claim.

---

**1. Core Unsoundness / Overclaim**

- `README.md / Thesis` overclaims from pilot evidence: “middle band ... entire harness lift” and “No amount of reasoning recovers an underdetermined spec” are population/causal claims, while `docs/AUDIT-CHECKLIST.md / Current pilot vs the bar` says the repo lacks unbiased sample, reps, multi-rater codebook, clean floor, and independent adversarial pass.

- `docs/ADMISSIBILITY-SPEC.md / KNOWN_AMBIGUOUS` treats ambiguity as an existence proof, but the default witness is only an argument. That proves at most “the auditor can articulate R2,” not that a competent from-prose solver would regard R2 as admissible under project norms, surrounding code, issue context, or implicit API conventions.

- The “passing patch never proves DETERMINED” asymmetry is right epistemically, but the method does not mirror it on ambiguity. A failing prose-plausible patch also does not prove underdetermination unless R2 is independently validated as prose-faithful and implementation-faithful. `docs/ADMISSIBILITY-SPEC.md / The test that decides ambiguous-vs-our-gap` makes that hinge on whether `our_failed.diff` “believably” satisfies prose, which is judgment, not mechanical.

- “No witness found = provisional” is sound, but the public framing still slips into hard denominator language. `docs/ADMISSIBILITY-SPEC.md / Headline the artifact yields` says `KNOWN_BAD ∪ KNOWN_AMBIGUOUS` is the complement of admissible fraction. That is only true after the panel protocol runs on a defined frame, not for current candidates.

- The example undermines the method’s own story: `data/attribution/qutebrowser.md` says verdict `ENTAILED`, `14/14 in-gold behaviors covered`, `0 GAP`; `docs/ADMISSIBILITY-SPEC.md / Current contents` describes qutebrowser as a KNOWN_AMBIGUOUS candidate. That inconsistency is the first thing I would attack.

**2. Weakest Link**

The weakest link is the ambiguity witness standard in `docs/ADMISSIBILITY-SPEC.md / KNOWN_AMBIGUOUS`, especially “argument witness — the DEFAULT” and “chosen by obviousness.” A defender says: you are letting the same interested auditor choose R2, decide it is defensible, decide the failure is self-evident, and decide no graded patch is needed. That is not audit-grade adjudication.

**3. COI**

The COI argument is partly sound but overstated. `README.md / Position / conflict of interest` says verdicts need no trust because blanks are mechanical and re-derivable. That works for exact citation verification, not for the load-bearing judgment: whether absence of a prose clause means underdetermination rather than implicit convention, issue context, codebase affordance, or ordinary bug-fix inference.

The “existence proofs so sampling bias doesn’t bind” defense only works for per-case claims. It does not support `README.md / Thesis` band estimates, denominator claims, or “entire harness lift” causal framing. `docs/AUDIT-CHECKLIST.md / Sampling` explicitly admits current selection bias.

**4. GPT-5.5 Judge / Contamination**

The judge contamination bites in three places:

- `docs/PRIOR-ART.md` says the survey was by codex/gpt-5.5 and has unverified items. That contaminates novelty/framing.
- `docs/ADMISSIBILITY-SPEC.md / KNOWN_AMBIGUOUS` uses a judge-like adversarial skeptic standard. A model with possible benchmark/repo exposure may know gold-shaped interpretations.
- `README.md / What the evidence shows` reports codex/gpt-5.5 arms; if the model has latent exposure, oracle-free success/failure and “diagnosis recall” are not clean measures of reasoning.

Verbatim citation verification is necessary but insufficient. It checks whether quoted prose/gold/test anchors exist. It does not check whether the model selected all relevant clauses, whether R2 is actually defensible, whether project context resolves the ambiguity, or whether the judge imported gold knowledge while deciding “obvious.”

**5. Witness Tiers**

The tiering has a hole: “obviousness” is doing the work that a codebook or rater agreement should do. `docs/ADMISSIBILITY-SPEC.md / argument witness` allows prose arguments by default; `graded-patch` is reserved for cases where a reader could doubt R2. But the auditor predicts the skeptic’s doubt.

Yes, argument witnesses can smuggle in a wrong R2. They can describe an alternative reading that sounds prose-valid in isolation but violates surrounding code behavior, API semantics, issue history, or a requirement not quoted in the row. Without independent raters or a required graded patch for every ambiguity claim, this remains vulnerable.

**6. What Is Missing For Audit-Grade**

The repo already names the missing pieces in `docs/AUDIT-CHECKLIST.md / Current pilot vs the bar`:

- unbiased full or seeded sample;
- k≥5 reps per instance/arm;
- frozen decision rules before runs;
- multi-rater construct-validity codebook with agreement;
- full public-set KNOWN_BAD sweep;
- post-cutoff clean floor;
- independent adversarial review;
- citation re-verification;
- release-tagged reproducibility across all audited instances.

Until then it is a pilot plus case studies, not an audit-grade benchmark indictment.

**Most Likely Successful Rebuttal**

The strongest rebuttal is: “You have not shown underdetermination; you have shown that your chosen solver missed behaviors that were inferable from the prose, codebase, and normal project conventions. Your R2 witnesses are auditor-constructed, not independently validated.”

The method survives that only if the panel protocol and multi-rater codebook actually run and converge. In its current form, no. It survives as a promising audit design, not as a proven audit result.
