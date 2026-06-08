# swebench-pro-audit

A causal audit of **SWE-bench Pro** — the contamination-resistant tier OpenAI now recommends in place
of SWE-bench Verified. The question is not "is Pro contaminated" (it is resistant by design, and that
holds up; see below). The question is **where a harness's Pro score actually comes from** — and the
answer, on the cases audited here, is *not* reasoning.

## Thesis

On SWE-bench Pro, the above-baseline lift of a working agent harness is **oracle-gated iteration**
(iterate-to-green against the held-out tests), **not** diagnosis, planning, or localization. Strip the
oracle and a capable model's reasoning recovers ~none of the lift.

A score on Pro decomposes into three bands:

| band | what it is | reachable by |
|---|---|---|
| floor (~50%, contaminated est.) | the problem prose **determines** the fix and a capable model can implement it directly | reasoning alone |
| +45 (floor → ~95%) | the prose **under**determines the fix; the held-out test determines it | **the oracle** (iterate-to-green) — or recall, or a lucky guess of the author's choice |
| ~5% (~95% → 100%) | irreducibly hard implementation + bench defects | nothing, within budget |

The middle band — the entire harness lift — **is** the prose-underdetermination band. No amount of
reasoning recovers an underdetermined spec; the spec is not in the prose. To clear that band without
the oracle you must read the test (oracle), remember the merged PR (recall), or guess the author's
unspecified implementation choice (not a scalable mechanism).

## What the evidence shows (oracle-free, official-graded)

All arms below run the agent **without** access to the held-out tests; the official tests grade after.

- **Diagnosis is inert.** A test-free prose diagnosis handed to the implementer changes nothing:
  recon→craft ≡ craft-only, **0/6 discordant** (codex/gpt-5.5, same model both arms; the delta is
  contamination-clean).
- **A stronger, different-family diagnosis is also inert.** Opus-4.8 diagnosis → codex craft rescued
  **0/4** loss cases. The one discordant cell is anti-thesis and is craft Pass@1 variance (the same
  blind arm flipped win/loss across runs). Blind-craft run-to-run variance **exceeds** the diagnosis effect.
- **A self-authored verification loop is worse than inert — it is false-confident.** Letting the model
  write and run its own reproduction (oracle-free) and iterate: **4/4 self-declared "AUDIT GREEN",
  0/4 actually resolved.** You cannot bootstrap a fault-revealing oracle you were never given.
- **Losses are downstream of *solved* localization.** Diagnosis recall vs the gold patch is high and
  precise (precision 0.58–0.996 — not wrong bugs); on `qutebrowser-e34dfc68` it is **1.0 (8/8 gold
  regions)** and the case **still loses end-to-end**. The residual is a fine-grained behavioral detail
  (when `is_url` consults DNS) that the prose never specifies and the held-out test enumerates. Craft
  localized perfectly, rebuilt the gold's own concept, passed **233/248**, and lost on a 15-case DNS
  matrix the prose doesn't pin. (See `data/craft_autopsy/`.)

Recall tracks fix-breadth, not inquiry quality: `protonmail` (a 4-concern Redux overhaul, gold touches
**11 files / 39 regions** — a feature mislabeled as a bug) gets 44% recall because the prose cannot
determine 39 regions, not because the inquiry is narrow.

## What this is NOT

- **Not a contamination claim about Pro.** Pro is contamination-*resistant*; OpenAI endorses it on that
  basis, and a gold-overlap audit puts the frontier pair at ~2% on Pro. The recall story is **Verified's**
  (OpenAI's own audit), and it does **not** transfer here. This audit needs no contamination claim.
- **Not "benchmarks have flawed tests."** That is established for Verified (OpenAI; Aleithan 2024;
  Wang/Pradel/Liu 2025). The contribution here is the **causal decomposition** — the success mechanism
  is search-against-the-oracle, not understanding — which the prior art does not make. See `docs/PRIOR-ART.md`.
- **Not a rescue of any harness.** Oracle-free *everything* failed — diagnosis, cross-model, self-audit.
  The bench and the clever machinery fail in the same place, for the same reason: the spec lives in the
  test, not the prose.

## Honest limits

- Small, pre-selected n (existence cases), single rollout per arm. These *demonstrate* the mechanism;
  they do not estimate a rate. A systematic n=728 construct-validity pass (gold-patch breadth distribution,
  prose→fix determination) is future work, not done here.
- The ~50% floor is measured on a contaminated model, so the *clean* prose-determined floor is likely
  lower and is unmeasured (needs oracle-free + post-cutoff).

## Position / conflict of interest

We authored a Pro harness and paper ([swebench-pro](https://github.com/kimjune01/swebench-pro),
[the methodeutic harness](https://june.kim/the-methodeutic-harness-on-swebench-pro)) whose oracle-free
arms produced the null this audit explains. We disclose this as **provenance, not penance**: the stake is
*why* the audit is this deep — a disinterested party never reads a task's requirements against its hidden
test line by line. Motivation is also bias risk, so no verdict is asked to be trusted. Each blank is
mechanical and re-derivable from committed receipts: the behavior is in [`hidden_test.diff`], its anchor
verifies verbatim in [`gold.diff`], and no clause verifies in [`spec.md`]. A reader who thinks we are
motivated reasoners can ignore every word we wrote and reproduce the table from the gold, the test, and
the prose. **Disclosure explains why the work exists; verifiability is why its conclusions need no trust.**
The one place our stake could still tilt the result is *sampling* — handled by judging a seeded/whole
sample, not our losses. Methodology reuses our [DeepSWE audit](https://june.kim/auditing-deepswe)
(gold-passes-verifier, denominator hygiene, the second-reader cold read, the specification-lottery pattern).

## Layout

- `docs/ADMISSIBILITY-SPEC.md` — the artifact spec: two lists, **KNOWN_BAD** (gold fails its own grader) and **KNOWN_AMBIGUOUS** (gold passes but the prose underdetermines the graded behavior), with the from-prose panel protocol, the blind-construction integrity rule, and the entry/receipt schema.
- **[`SUMMARY.md`](SUMMARY.md)** — the index table (every judged case, verdict, coverage, gaps, links). Markdown so GitHub renders it; no frontend.
- **[`KNOWN_BAD.md`](KNOWN_BAD.md)** (gold fails its own grader, 3 confirmed) · **[`KNOWN_AMBIGUOUS.md`](KNOWN_AMBIGUOUS.md)** (gold passes, prose underdetermines) · **[`OUR_CAPABILITY_GAPS.md`](OUR_CAPABILITY_GAPS.md)** (we lost, prose determines). Regenerated by `tools/build_ledgers.py` from the per-case data.
- `data/attribution/<case>.md` — the coverage table per case (test left, verbatim requirement right, blank cell = the gap). `data/cases/<id>/` — receipts (spec, gold, hidden test, our failed patch). `data/judge/<case>.json` — raw coverage rows.
- `docs/AUDIT-CHECKLIST.md` — preregistration-shaped rigor checklist (bar: meet/exceed OpenAI's Verified audit), with an honest current-status column. **This pilot is not yet audit-grade; the checklist is the path.**
- `docs/PRIOR-ART.md` — verified citations, the Verified-vs-Pro split, and the novelty verdict.
- `docs/FINDINGS.md` — the bands, the oracle-free nulls, the craft autopsy, the recall table.
- `data/` — committed receipts: per-instance driver logs, recon handoffs, the craft patch + grade.
- `tools/diag_oracle.py` — the deterministic diagnosis-vs-gold scorer (recall/precision, no LLM judge).

Harness, drivers, and reproduction live in the companion repo
[`swebench-pro`](https://github.com/kimjune01/swebench-pro).

## License

Dual-licensed (copyleft): code (`tools/`) under [AGPL-3.0](LICENSE-CODE.txt); everything else (prose,
findings, `data/` receipts) under **CC BY-SA-NS** (CC BY-SA 4.0 + a Network Services clause). See
[`LICENSE.md`](LICENSE.md) and [june.kim/cc-by-sa-ns](https://june.kim/cc-by-sa-ns). Build a service on
this and source flows back to users; no paywall, no gated access.
