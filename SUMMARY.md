# SWE-bench Pro audit — summary

Public-set determinacy audit. **All 728 public tasks** (canonical solver-prose from the companion harness's `pro_repl_fields`, joined to gold+test from `ScaleAI/SWE-bench_Pro`) are labeled by the coverage-table screen (`tools/judge_pool.py`): a GAP = a behavior the gold implements and the hidden test checks, but no requirement states.

Verdicts are mechanical and re-derivable from committed receipts. The **screen** flags AMBIGUOUS candidates; only the **mechanical spine** (below) is claimable without independent raters. Codebase/borderline ambiguity is a disciplined hypothesis, raters-pending.

## Coverage over the public set

| label | count | of N | claimable without raters? |
|---|---:|---:|---|
| ENTAILED (every graded behavior has a covering requirement) | 478 | 66% | n/a (not a defect) |
| AMBIGUOUS — screen (≥1 GAP) | 250 | 34% | screen only |
| &nbsp;&nbsp;├─ **airtight** (constant absent from prose **and** codebase, grep-certified) | 30 | 4% | **YES — mechanical spine** |
| &nbsp;&nbsp;├─ **prose-affirmative, hand-verified** (tutao) | 1 | 0% | **YES — mechanical spine** |
| &nbsp;&nbsp;├─ prose-affirmative, codex-proposed (clause-verified, R2-entailment unproven) | 53 | 7% | NO — raters / graded-patch pending |
| &nbsp;&nbsp;└─ codebase / borderline | 166 | 23% | NO — raters-pending |

## Claimable now (mechanical spine)

- **KNOWN_AMBIGUOUS (PROVEN): 31** of 728 — 30 airtight + 1 prose-affirmative, each with a verified argument witness ([`KNOWN_AMBIGUOUS.md`](KNOWN_AMBIGUOUS.md)).
- **KNOWN_BAD: 3** gold-fails-grader defects, frozen pre-run ([`KNOWN_BAD.md`](KNOWN_BAD.md); separately audited, outside the prose-set denominator).

So on the 728-task public set, the claimable determinacy-failing floor is **31 PROVEN-ambiguous (4.3%)**, with a further **219 screen-flagged hypotheses (30%)** that an independent codebase-aware rater panel + κ must adjudicate before any of them counts. The codebase-class *rate* is therefore reported as raters-pending, not as a result. This is a preregistered instrument with a proven spine, not yet a population rate.

Full per-case table: [`COVERAGE.md`](COVERAGE.md). Method: [`docs/ADMISSIBILITY-SPEC.md`](docs/ADMISSIBILITY-SPEC.md).

## Hand-audited worked cases

| case | verdict | coverage | gaps | list | attribution |
|---|---|---|---|---|---|
| element | ENTAILED | 32/32 | 0 | OUR_GAP | [table](data/attribution/element.md) |
| protonmail | ENTAILED | 20/20 | 0 | OUR_GAP | [table](data/attribution/protonmail.md) |
| qutebrowser | ENTAILED | 14/14 | 0 | OUR_GAP | [table](data/attribution/qutebrowser.md) |
| tutao | AMBIGUOUS | 13/19 | 6 | AMBIGUOUS | [table](data/attribution/tutao.md) |
