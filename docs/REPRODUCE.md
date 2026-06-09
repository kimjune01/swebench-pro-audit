# Reproducing this audit

Two sections. **§1 Verify it yourself** needs nothing but this repo — that is the load-bearing path and the
reason the audit needs no trust. **§2 Reproduce the data yourself** re-runs the pipeline; it is written as a
recipe a capable coding agent can follow, not a one-command script, because the generative steps need model
access (a contaminated screen) and a container fleet that no third party will have configured identically.

Pinned context (everything regeneration assumes):
- Dataset: `ScaleAI/SWE-bench_Pro`, split `test`, **revision `7ab5114912baf22bb098818e604c02fe7ad2c11f`** (frozen 2026-02-23).
- Scope: the **728 public tasks** whose canonical solver-prose is vendored at [`data/pro_repl_fields.json`](../data/pro_repl_fields.json).
- Grader: the official ScaleAI evaluator `swe_bench_pro_eval.py` (in `scaleapi/SWE-bench_Pro-os`), local docker, images `jefzda/sweap-images:<dockerhub_tag>`.

---

## 1. Verify it yourself (no dependencies, no model, no network)

Every PROVEN verdict is re-derivable by eye from committed receipts. Pick any case in
[`KNOWN_AMBIGUOUS.md`](../KNOWN_AMBIGUOUS.md) and check its tier's burden:

- **airtight** — open `data/cases/<id>/AMBIGUITY_WITNESS.md`; take the discriminating constant; confirm it
  appears in `hidden_test.diff` and `gold.diff` and **not** in `spec.md`. (The codebase-absence half was
  grep-checked at base_commit during generation; re-run `tools/witness.py --clone` to re-verify it.)
- **graded-patch** — read `r2.diff` (the alternative impl), `r2_gate.json` (opus AND codex both judged it
  prose-faithful, blind), and `r2_grade.json` (`gold_resolved:true`, `r2_resolved:false`, the discriminating
  `flips`, `ran_ratio≥0.9`, no PASS_TO_PASS regression). The grade is the mechanical part.
- **codebase-plural** — `AMBIGUITY_WITNESS.md` lists ≥2 file:line precedents; confirm each snippet is real
  live code (not test/example/vendor/generated/deprecated) and the prose is silent on the choice.
- **hand (tutao)** — the quoted clause verifies verbatim in `spec.md`.
- **KNOWN_BAD** — `data/cases/gold_fails_grader.defects.jsonl` + the full-sweep receipt in `data/gold_sweep/`.

Regenerate the ledgers from the committed per-case data (pure, no external deps):

```
python tools/build_ledgers.py     # rewrites SUMMARY.md, COVERAGE.md, KNOWN_*.md, OUR_CAPABILITY_GAPS.md
```

If `build_ledgers.py` reproduces the same counts (478 / 36 / 53 / 161 / 3) from the committed `data/judge`
and `data/cases`, the headline is reproduced. Nothing else is required to trust the spine.

---

## 2. Reproduce the data yourself (a recipe for a capable agent)

Requirements: `pip install datasets pandas` (+ `ripgrep` recommended); a `codex` CLI (the screen/witness
rater) and a `claude` CLI (opus, the second blind rater and R2 generator); for the graded-patch and gold
sweep, an EC2 box with docker and the ScaleAI evaluator. Run from the audit repo root.

**1. Materialize the 728 bundles.** `python tools/materialize.py` — joins the vendored prose with the
pinned dataset and writes `data/cases/<slug>/{spec.md,gold.diff,hidden_test.diff,fail_to_pass.txt}`.

**2. Coverage screen.** For each case, prompt the screen model: *"For every behavior the HIDDEN TEST
asserts, quote the verbatim prose clause that determines it (or null) and a verbatim gold-patch anchor
that implements it (or null)."* Python verifies both citations; a row that is in-gold + unspecified-in-prose
is a **GAP**; ≥1 GAP ⇒ AMBIGUOUS-screen. (`tools/judge_pool.py`, `tools/run_judge_all.py`.)

**3. Witness the AMBIGUOUS screen — claim only with positive evidence:**
   - *airtight*: ask the model for the single discriminating arbitrary constant; mechanically confirm it is
     absent from `spec.md` **and** from a clone of the repo at `base_commit` (grep, excluding
     test/example/vendor/generated/deprecated). Absent both ⇒ PROVEN. (`tools/witness.py --clone`.)
   - *graded-patch*: have opus generate a minimal **R2** that takes the prose-faithful alternative reading;
     run the **blind prose-match gate** — opus AND codex each, seeing only `spec.md` + `r2.diff` (never the
     gold/test/each other), must answer "satisfies every requirement"; then grade R2 on a box — it must
     fail the discriminating FAIL_TO_PASS while PASS_TO_PASS stays green. Both-yes + clean-fail ⇒ PROVEN.
     (`tools/r2_promote.py gen|gate`, `driver/grade_r2.py` on the box.)
   - *two-expert split* (two-expert standard): for each plurality candidate, codex constructs an existence
     proof on either axis — **prose** plurality (≥2 readings the requirement licenses, both faithful) or
     **source** plurality (≥2 comparable, live, prose-silent precedents at `base_commit`, non-test/example/
     vendor/generated/deprecated). Then an independent cross-family refuter (opus) tries to **kill** each
     split (strained reading, lookalike precedent, prose actually selects); survivors are PROVEN. A
     symmetric advocate pass over the *determined* cases looks for missed splits (recovered none; κ=0.52).
     (`tools/plurality_proof.py` builds; the refute/advocate passes write `data/judge/*.refute.json` /
     `*.advocate.json`.) Everything that does not survive stays **hypothesis** (not counted).

**4. KNOWN_BAD gold sweep.** Grade the *gold* patch of all tasks with the official evaluator; any
`reward≠1` is a candidate; **re-run each candidate isolated/alone** (a parallel-sweep hiccup is never logged
as a defect). (`driver/audit_fleet.sh` in the companion; receipt in `data/gold_sweep/`.)

**5. Ledgers.** `python tools/build_ledgers.py`.

Integrity invariants the recipe must preserve: label **blind to any harness win/loss**; claim ambiguity only
on **positive evidence** (absent constant, shown drift, graded failure) — never failure-to-find (that is
UNKNOWN); a passing patch never proves DETERMINED, a failing prose-plausible patch never proves AMBIGUOUS
without the blind two-rater gate. The screen model is contaminated, so it is a **screen, not an oracle** —
every citation it makes is verified mechanically, which is why the contamination does not reach the verdict.

---

## Note on independence

Regeneration uses our model access; **verification (§1) does not.** A reader who distrusts the
generative steps can discard every model output and re-derive the spine from the committed gold, test, and
prose. That asymmetry is the point: the screen and raters propose, the receipts dispose.
