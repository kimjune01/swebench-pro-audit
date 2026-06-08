# Audit rigor checklist (preregistration)

Bar: **meet or exceed OpenAI's SWE-bench Verified audit** (defined sample fraction, multi-category
test/spec codebook, quantified flaw rate, contamination analysis) **plus** house norms (preregister,
official grader only, committed receipts, post-cutoff firewall, anti-self-serving review).

Status legend: `[x]` done · `[~]` partial / pilot only · `[ ]` not started. The current repo is a
**pilot** (existence cases), so most boxes are open by design — that is the point of this checklist.

## 0. Preregister and freeze (before any new run)
- [ ] Freeze the two claims verbatim: **A** (oracle-gated iteration is the lift, not reasoning) and
      **B** (losses are test-over-determination downstream of solved localization).
- [ ] Freeze sample, arms, metrics, and **decision rules** (what result confirms / refutes each), and
      commit this file's filled version *before* running. No post-hoc reinterpretation.
- [ ] State, in advance, what would make us **drop** a claim (e.g., A dies if the oracle-free vs
      oracle-gated delta is not significant under reps; B dies if recall does not predict loss).

## 1. Sampling — the OpenAI-parity core
- [~] Define the frame and selection explicitly. **Current: 6 + 4 *pre-selected existence cases*
      (deprived-lost-with-gate) = selection bias; cannot generalize.**
- [ ] Replace with an **unbiased** sample: full public set (n=728) or a random sample with stated size
      and seed. Report the fraction audited (OpenAI did ~27.6%).
- [ ] Pre-exclude and *report* known bench defects (KNOWN_BAD / golds that fail their own verifier);
      do not silently drop.

## 2. Construct-validity coding (claim B) — multi-rater + codebook
- [ ] Write a codebook with explicit categories: bug-vs-feature; gold-patch breadth bins (files,
      regions, LOC); **prose-determines-the-fix** {yes / partial / no}; test class {narrow / wide / sound}.
- [ ] **≥2 independent raters** per instance; report **inter-rater agreement** (Cohen's κ); adjudicate
      disagreements with a third. (LLM raters allowed only if blinded and agreement is reported.)
- [x] Deterministic where possible: gold-patch file/region counts and diagnosis recall via
      `tools/diag_oracle.py` (no LLM judge). *(have it; run it across the sample, not 2 cases.)*

## 3. Causal arms (claim A) — fix the variance hole
- [~] Arms, all official-graded: craft-only (floor), recon→craft, +oracle-free audit loop, full-gated
      (ceiling). **Current: pilot has all four but at n=4-6, single rollout.**
- [ ] **Reps: k≥5 rollouts per (instance, arm).** This is the load-bearing fix — the pilot already
      showed *blind-craft Pass@1 variance exceeds the diagnosis effect* (protonmail flipped across runs),
      so single-shot cannot support a causal claim. Report per-instance resolve fraction, paired deltas,
      and a paired test (McNemar or bootstrap CI) with the variance budget stated.
- [x] Keep contamination constant within each contrast (same model both arms) so the **delta** is clean.
- [ ] Characterize the self-audit false-green: capture the repro content and classify genuine-wrong vs
      no-op (the pilot lost this; boxes were torn down).

## 4. Localization vs resolution (claim B, quantitative)
- [~] diagnosis recall/precision vs gold across the sample. **Current: 4 losses only.**
- [ ] Report the recall→resolution relationship over the full sample; the claim "recall high yet loses"
      needs the distribution, not one `qutebrowser` case (kept as the worked example).

## 5. Contamination accounting — Pro-specific, do not overclaim
- [~] gold-overlap audit across the sample (tool exists in the sibling repo). *Frontier ~2% on Pro is
      the prior figure; reproduce it on this sample.*
- [ ] **Clean floor: oracle-free + post-cutoff** instances (the one number nobody reports). This is the
      only contamination claim Pro supports; the recall story is Verified's and stays out.

## 6. Grading discipline (house rule)
- [x] **Official grader only.** No bespoke graders; note defects in one line and move on.
- [x] Source-only patches (strip test-file edits) to avoid serialization / oracle leakage.
- [ ] Run the KNOWN_BAD set at campaign end and report honestly per category.
- [x] Capture per-test results (the grader's `_output.json`), not just pass/fail.

## 7. Receipts and reproducibility
- [x] Per-instance receipts committed: driver log, recon handoff, craft patch, grade output. *(pilot has these.)*
- [ ] Extend to every audited instance; ship a one-prompt repro on a random sample; include a cost ledger.

## 8. Anti-self-serving review (the most important box)
- [ ] Independent adversarial review (codex + gemini, or a human) charged specifically with: is each
      claim **scoped**; is the bench critique **not** a rescue of any harness (oracle-free *everything*
      failed); are alternatives ruled out (Pass@1 variance, contamination, bench defects, weak craft).
- [ ] Re-verify every external citation before it is cited (two prior-art items remain UNVERIFIED;
      see `PRIOR-ART.md`). Validate cited papers' actual claims, not their abstracts.
- [ ] Report base rates as **measured, not designed**; lead with limits; calibrate confidence to n.

## 9. Reporting
- [ ] Loss taxonomy over a single number; honest n and selection; novelty scoped against prior art
      (audit Pro not Verified; causal decomposition is the novel part).
- [ ] One-line disclaimer where the regime is contaminated or the n is a pilot; no badges, receipts available.

---

### Current pilot vs the bar (one-line gap read)
We have: the mechanism *demonstrated* on pre-selected cases, deterministic localization scoring, official
grading, committed receipts. We lack, for an audit-grade claim: an **unbiased sample**, **reps** (the
variance fix), a **multi-rater construct-validity codebook with κ**, the **post-cutoff clean floor**, and
an **independent adversarial pass**. Items 1, 3 (reps), 2, 5 (post-cutoff), and 8 are the critical path.
