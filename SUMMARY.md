# SWE-bench Pro audit — summary

Public-set determinacy audit. **All 728 public tasks** (canonical solver-prose from the companion harness's `pro_repl_fields`, joined to gold+test from `ScaleAI/SWE-bench_Pro`) are labeled by the coverage-table screen (`tools/judge_pool.py`): a GAP = a behavior the gold implements and the hidden test checks, but no requirement states.

Verdicts are mechanical and re-derivable from committed receipts. The **screen** flags AMBIGUOUS candidates; only the **mechanical spine** (below) is claimable without independent raters. Codebase/borderline ambiguity is a disciplined hypothesis, raters-pending.

## Coverage over the public set

| label | count | of N | claimable without raters? |
|---|---:|---:|---|
| ENTAILED (every graded behavior has a covering requirement) | 478 | 66% | n/a (not a defect) |
| AMBIGUOUS — screen (≥1 GAP) | 250 | 34% | screen only |
| &nbsp;&nbsp;├─ **airtight** (constant absent from prose **and** codebase, grep-certified) | 30 | 4% | **YES — mechanical spine** |
| &nbsp;&nbsp;├─ **prose-affirmative, graded-patch** (R2 both raters call faithful, bench fails it) | 5 | 1% | **YES — mechanical spine** |
| &nbsp;&nbsp;├─ **prose-affirmative, hand-verified** (tutao) | 1 | 0% | **YES — mechanical spine** |
| &nbsp;&nbsp;├─ **codebase-plural** (≥2 live coexisting conventions, prose silent) | 18 | 2% | **YES — under the two-precedent rule** |
| &nbsp;&nbsp;├─ prose-affirmative, codex-proposed (gate/graded-patch pending or not-clean) | 48 | 7% | NO — raters / graded-patch pending |
| &nbsp;&nbsp;└─ codebase / borderline (no 2 comparable live precedents found) | 148 | 20% | NO — raters-pending |

## Claimable now — two bars

- **Mechanical spine (no methodological buy-in): 36 of 728 (4.9%)** — 30 airtight (grep) + 5 graded-patch (R2 both-rater-faithful + bench-failed) + 1 hand-verified. A hostile reader reproduces each from the committed gold+test+prose and has nothing to argue.
- **Plus codebase-plural under the two-precedent rule: 18**, giving **54 total (7.4%)**. These cite ≥2 live, comparable, prose-silent coexisting conventions in the repo at base_commit (grep-verified, test/example/vendor/deprecated excluded). Defensible, but rests on the stance that two live conventions + silent prose = underdetermined — a reader can contest it ('a solver would infer which binds').
- **KNOWN_BAD: 3** gold-fails-grader defects, frozen pre-run; the full 731 sweep re-confirmed exactly these and found no new genuine defect ([`KNOWN_BAD.md`](KNOWN_BAD.md)).

Headline, honestly two-tier: **4.9% provably underdetermined with no assumptions; 7.4% under a reasonable solver model.** A further 196 screen-flagged hypotheses (27%) remain raters-pending and are NOT counted. A preregistered instrument with a proven spine, not a population rate.

Full per-case table: [`COVERAGE.md`](COVERAGE.md). Method: [`docs/ADMISSIBILITY-SPEC.md`](docs/ADMISSIBILITY-SPEC.md).

## Hand-audited worked cases

| case | verdict | coverage | gaps | list | attribution |
|---|---|---|---|---|---|
| element | ENTAILED | 32/32 | 0 | OUR_GAP | [table](data/attribution/element.md) |
| protonmail | ENTAILED | 20/20 | 0 | OUR_GAP | [table](data/attribution/protonmail.md) |
| qutebrowser | ENTAILED | 14/14 | 0 | OUR_GAP | [table](data/attribution/qutebrowser.md) |
| tutao | AMBIGUOUS | 13/19 | 6 | AMBIGUOUS | [table](data/attribution/tutao.md) |
