# SWE-bench Pro audit — summary

Public-set determinacy audit. **All 728 public tasks** (canonical solver-prose from the companion harness's `pro_repl_fields`, joined to gold+test from `ScaleAI/SWE-bench_Pro`) are labeled by the coverage-table screen (`tools/judge_pool.py`): a GAP = a behavior the gold implements and the hidden test checks, but no requirement states.

Verdicts are mechanical and re-derivable from committed receipts. The **screen** flags AMBIGUOUS candidates; only the **mechanical spine** (below) is claimable without independent raters. Codebase/borderline ambiguity is a disciplined hypothesis, raters-pending.

## Coverage over the public set

| label | count | of N | claimable without raters? |
|---|---:|---:|---|
| ENTAILED (every graded behavior has a covering requirement) | 478 | 66% | n/a (not a defect) |
| DETERMINED-codebase (prose silent, one codebase way, gold matches) | 78 | 11% | n/a (not a defect — well-specified by convention/reuse) |
| DEFECT — screen (a faithful solver fails) | 172 | 24% | screen only |
| &nbsp;&nbsp;├─ AMBIGUOUS (≥2 codebase ways; test pins one) | 157 | 22% | per witness class below |
| &nbsp;&nbsp;├─ MISDETERMINED (one codebase way; test grades a different value) | 15 | 2% | per witness class below |
| &nbsp;&nbsp;├─ **airtight** (constant absent from prose **and** codebase, grep-certified) | 43 | 6% | **YES — mechanical spine** |
| &nbsp;&nbsp;├─ **misdetermined** (codebase determines X one way, gold/test pin Y≠X; grep-certified) | 19 | 3% | **YES — mechanical spine** |
| &nbsp;&nbsp;├─ **codebase-plural** (codebase makes the choice ≥2 live ways; grep-certified) | 15 | 2% | **YES — mechanical spine** |
| &nbsp;&nbsp;├─ **prose-affirmative, graded-patch** (R2 both raters call faithful, bench fails it) | 5 | 1% | **YES — mechanical spine** |
| &nbsp;&nbsp;├─ **prose-affirmative, hand-verified** (tutao) | 1 | 0% | **YES — mechanical spine** |
| &nbsp;&nbsp;├─ **two-expert split** (prose and/or source plurality; survived hostile refutation) | 26 | 4% | **YES — two-model adversarial (codex builds, opus refutes)** |
| &nbsp;&nbsp;├─ prose-affirmative, codex-proposed (gate/graded-patch pending or not-clean) | 48 | 7% | NO — raters / graded-patch pending |
| &nbsp;&nbsp;└─ codebase / borderline (no 2 comparable live precedents found) | 15 | 2% | NO — raters-pending |

## Claimable now — two bars

- **Mechanical spine (no methodological buy-in): 83 of 728 (11.4%)** — 43 airtight (grep) + 5 graded-patch (R2 both-rater-faithful + bench-failed) + 1 hand-verified. A hostile reader reproduces each from the committed gold+test+prose and has nothing to argue.
- **Plus two-expert splits, adversarially verified: 26**, giving **109 total (15.0%)**. Each is a case where two world-class engineers, given only the prose and the repo source, would both write a requirement-faithful implementation that the hidden test splits — proven on either axis (the prose licenses ≥2 faithful readings, or the codebase makes the same decision ≥2 live ways). codex constructs the existence proof; an independent cross-family refuter (Claude opus) tries to kill it; these survived. A symmetric advocate pass over the determined cases recovered none. Inter-rater κ=0.52 (moderate); all disagreement is skeptic-stricter, so this is the both-raters-agree floor. Rests on the two-expert standard — not assumption-free, but verified, not asserted.
- **KNOWN_BAD: 3** gold-fails-grader defects, frozen pre-run; the full 731 sweep re-confirmed exactly these and found no new genuine defect ([`KNOWN_BAD.md`](KNOWN_BAD.md)).
- **KNOWN_MISMATCH: ≥1** — a distinct defect class where the prose describes one feature but the gold+test grade another (`flipt-io_358e13bf`: prose asks for snapshot-cache deletion, gold/test grade a CSRF config default). Not underdetermination, not gold-fails-grader; surfaced incidentally, a systematic scan is a separate pass ([`KNOWN_MISMATCH.md`](KNOWN_MISMATCH.md)).

Headline, honestly two-tier: **11.4% provably underdetermined with no assumptions; 15.0% once the adversarially-verified two-expert splits are added.** A further 63 screen-flagged hypotheses (9%) remain raters-pending and are NOT counted. A preregistered instrument with a proven spine, not a population rate.

Inspect every claim: [`CLAIMS.md`](CLAIMS.md) (one row per claimable case + the 12 refuted negative controls). Full per-case table: [`COVERAGE.md`](COVERAGE.md). Method: [`docs/ADMISSIBILITY-SPEC.md`](docs/ADMISSIBILITY-SPEC.md).

## Hand-audited worked cases

| case | verdict | coverage | gaps | list | attribution |
|---|---|---|---|---|---|
| element | ENTAILED | 32/32 | 0 | OUR_GAP | [table](data/attribution/element.md) |
| protonmail | ENTAILED | 20/20 | 0 | OUR_GAP | [table](data/attribution/protonmail.md) |
| qutebrowser | ENTAILED | 14/14 | 0 | OUR_GAP | [table](data/attribution/qutebrowser.md) |
| tutao | AMBIGUOUS | 13/19 | 6 | AMBIGUOUS | [table](data/attribution/tutao.md) |
