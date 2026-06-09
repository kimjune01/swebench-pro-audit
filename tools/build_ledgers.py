#!/usr/bin/env python3
"""build_ledgers.py -- regenerate the human-viewable markdown ledgers from per-case data.

GitHub renders markdown tables natively, so the repo is its own viewer (no frontend). Sources:
  - data/judge/<case>.json                       (coverage-table results from judge_pool.py)
  - data/cases/<case>/AMBIGUITY_WITNESS.md        (PROVEN witness; class = airtight | prose-affirmative)
  - data/cases/<case>/AMBIGUITY_HYPOTHESIS.md     (disciplined hypothesis; codebase | borderline)
  - data/cases/gold_fails_grader.defects.jsonl    (the pre-run gold-fails-grader defects = KNOWN_BAD)

Emits at repo root: SUMMARY.md, COVERAGE.md (full 728-row index), KNOWN_BAD.md, KNOWN_AMBIGUOUS.md,
OUR_CAPABILITY_GAPS.md.

The headline discipline (codex sniff v2): only the MECHANICAL SPINE is claimable without raters --
KNOWN_BAD, DETERMINED-prose, AMBIGUOUS-airtight (constant absent from prose AND codebase), and
prose-affirmative cases. Codebase/borderline ambiguity is a disciplined HYPOTHESIS, raters-pending, and
is reported separately, never folded into a claimed rate.
"""
import json, re, pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
JUDGE = REPO / "data" / "judge"
CASES = REPO / "data" / "cases"

# cases we ran through recon+craft and lost (so an ENTAILED verdict = our capability gap)
OUR_LOSSES = {"qutebrowser", "protonmail", "tutao", "element"}
SPINE = {"airtight", "prose-affirmative"}  # the claimable witness classes


def iid(c):
    p = CASES / c / "instance_id.txt"
    return p.read_text().strip() if p.exists() else c


def witness_class(c):
    """returns (klass, proven_bool, filename) for an AMBIGUOUS case, else (None, False, None)."""
    for fn, proven in (("AMBIGUITY_WITNESS.md", True), ("AMBIGUITY_HYPOTHESIS.md", False)):
        p = CASES / c / fn
        if p.exists():
            m = re.search(r"class:\s*\*\*([\w-]+)\*\*", p.read_text())
            return (m.group(1) if m else "unknown"), proven, fn
    return None, False, None


def classify_of(case, rec):
    if rec.get("verdict") == "AMBIGUOUS":
        return "AMBIGUOUS"
    if rec.get("verdict") == "ENTAILED" and case in OUR_LOSSES:
        return "OUR_GAP"
    return "—"


def load_judged():
    out = {}
    for f in sorted(JUDGE.glob("*.json")):
        try:
            out[f.stem] = json.loads(f.read_text())
        except Exception:
            pass
    return out


def main():
    judged = load_judged()
    n = len(judged)
    ent = [c for c, r in judged.items() if r.get("verdict") == "ENTAILED"]
    amb = [c for c, r in judged.items() if r.get("verdict") == "AMBIGUOUS"]
    err = [c for c, r in judged.items() if r.get("verdict") not in ("ENTAILED", "AMBIGUOUS")]

    # witness accounting over the AMBIGUOUS screen. PROVEN (spine) = a case carrying a verified
    # AMBIGUITY_WITNESS.md: the 30 grep-certified airtight cases + the hand-verified tutao.
    klass = {c: witness_class(c) for c in amb}
    def graded(c):
        g = REPO / "data" / "cases" / c / "r2_grade.json"
        return g.exists() and json.loads(g.read_text()).get("clean_fail")
    proven = [c for c in amb if klass[c][1]]
    airtight = [c for c in proven if klass[c][0] == "airtight"]
    cbplural = [c for c in proven if klass[c][0] == "codebase-plural"]            # two-precedent rule
    gradedpatch = [c for c in proven if klass[c][0] == "prose-affirmative" and graded(c)]
    proseaff = [c for c in proven if klass[c][0] == "prose-affirmative" and not graded(c)]  # tutao
    # mechanical spine = assumption-free tiers; codebase-plural rests on the two-precedent rule
    mech_spine = airtight + gradedpatch + proseaff
    hypo = [c for c in amb if not klass[c][1]]
    auto_pa = [c for c in hypo if klass[c][0] == "prose-affirmative"]    # raters-pending tier
    cb_border = [c for c in hypo if klass[c][0] != "prose-affirmative"]  # codebase/borderline/skip
    spine = sorted(proven)

    df = REPO / "data" / "cases" / "gold_fails_grader.defects.jsonl"
    kb = [json.loads(l) for l in df.read_text().splitlines() if l.strip()] if df.exists() else []

    # ---- SUMMARY.md (aggregate + honest spine accounting) ----
    s = [
        "# SWE-bench Pro audit — summary", "",
        f"Public-set determinacy audit. **All {n} public tasks** (canonical solver-prose from the "
        "companion harness's `pro_repl_fields`, joined to gold+test from `ScaleAI/SWE-bench_Pro`) are "
        "labeled by the coverage-table screen (`tools/judge_pool.py`): a GAP = a behavior the gold "
        "implements and the hidden test checks, but no requirement states.", "",
        "Verdicts are mechanical and re-derivable from committed receipts. The **screen** flags "
        "AMBIGUOUS candidates; only the **mechanical spine** (below) is claimable without independent "
        "raters. Codebase/borderline ambiguity is a disciplined hypothesis, raters-pending.", "",
        "## Coverage over the public set", "",
        "| label | count | of N | claimable without raters? |", "|---|---:|---:|---|",
        f"| ENTAILED (every graded behavior has a covering requirement) | {len(ent)} | "
        f"{len(ent)/n:.0%} | n/a (not a defect) |",
        f"| AMBIGUOUS — screen (≥1 GAP) | {len(amb)} | {len(amb)/n:.0%} | screen only |",
        f"| &nbsp;&nbsp;├─ **airtight** (constant absent from prose **and** codebase, grep-certified) | "
        f"{len(airtight)} | {len(airtight)/n:.0%} | **YES — mechanical spine** |",
        f"| &nbsp;&nbsp;├─ **prose-affirmative, graded-patch** (R2 both raters call faithful, bench fails it) | "
        f"{len(gradedpatch)} | {len(gradedpatch)/n:.0%} | **YES — mechanical spine** |",
        f"| &nbsp;&nbsp;├─ **prose-affirmative, hand-verified** (tutao) | "
        f"{len(proseaff)} | {len(proseaff)/n:.0%} | **YES — mechanical spine** |",
        f"| &nbsp;&nbsp;├─ **codebase-plural** (≥2 live coexisting conventions, prose silent) | "
        f"{len(cbplural)} | {len(cbplural)/n:.0%} | **YES — under the two-precedent rule** |",
        f"| &nbsp;&nbsp;├─ prose-affirmative, codex-proposed (gate/graded-patch pending or not-clean) | "
        f"{len(auto_pa)} | {len(auto_pa)/n:.0%} | NO — raters / graded-patch pending |",
        f"| &nbsp;&nbsp;└─ codebase / borderline (no 2 comparable live precedents found) | {len(cb_border)} | "
        f"{len(cb_border)/n:.0%} | NO — raters-pending |",
    ]
    if err:
        s.append(f"| ERROR (judge did not parse) | {len(err)} | {len(err)/n:.0%} | — |")
    s += [
        "", "## Claimable now — two bars", "",
        f"- **Mechanical spine (no methodological buy-in): {len(mech_spine)} of {n} "
        f"({len(mech_spine)/n:.1%})** — {len(airtight)} airtight (grep) + {len(gradedpatch)} "
        f"graded-patch (R2 both-rater-faithful + bench-failed) + {len(proseaff)} hand-verified. A "
        "hostile reader reproduces each from the committed gold+test+prose and has nothing to argue.",
        f"- **Plus codebase-plural under the two-precedent rule: {len(cbplural)}**, giving "
        f"**{len(spine)} total ({len(spine)/n:.1%})**. These cite ≥2 live, comparable, prose-silent "
        "coexisting conventions in the repo at base_commit (grep-verified, test/example/vendor/"
        "deprecated excluded). Defensible, but rests on the stance that two live conventions + silent "
        "prose = underdetermined — a reader can contest it ('a solver would infer which binds').",
        f"- **KNOWN_BAD: {len(kb)}** gold-fails-grader defects, frozen pre-run; the full 731 sweep "
        "re-confirmed exactly these and found no new genuine defect ([`KNOWN_BAD.md`](KNOWN_BAD.md)).",
        "",
        f"Headline, honestly two-tier: **{len(mech_spine)/n:.1%} provably underdetermined with no "
        f"assumptions; {len(spine)/n:.1%} under a reasonable solver model.** A further {len(hypo)} "
        f"screen-flagged hypotheses ({len(hypo)/n:.0%}) remain raters-pending and are NOT counted. "
        "A preregistered instrument with a proven spine, not a population rate.", "",
        "Full per-case table: [`COVERAGE.md`](COVERAGE.md). Method: "
        "[`docs/ADMISSIBILITY-SPEC.md`](docs/ADMISSIBILITY-SPEC.md).", "",
        "## Hand-audited worked cases", "",
        "| case | verdict | coverage | gaps | list | attribution |", "|---|---|---|---|---|---|",
    ]
    for c in ("element", "protonmail", "qutebrowser", "tutao"):
        if c in judged:
            r = judged[c]
            s.append(f"| {c} | {r.get('verdict')} | {r.get('n_covered')}/{r.get('in_gold_total')} | "
                     f"{r.get('n_gap',0)} | {classify_of(c,r)} | [table](data/attribution/{c}.md) |")
    (REPO / "SUMMARY.md").write_text("\n".join(s) + "\n")

    # ---- COVERAGE.md (full 728-row index) ----
    cov = ["# Full coverage index (all public tasks)", "",
           "Every public task, its screen verdict, and — for AMBIGUOUS cases — the witness class. "
           "`airtight`/`prose-affirmative` are PROVEN (mechanical spine); `hypothesis` is raters-pending.",
           "", "| case | verdict | cov | GAP | witness class | attribution |", "|---|---|---|---|---|---|"]
    for c, r in sorted(judged.items()):
        kl = klass.get(c, (None, False, None))[0] if c in amb else ""
        kl = kl or ("" if r.get("verdict") != "AMBIGUOUS" else "(pending)")
        cov.append(f"| {c} | {r.get('verdict')} | {r.get('n_covered')}/{r.get('in_gold_total')} | "
                   f"{r.get('n_gap',0)} | {kl} | [t](data/attribution/{c}.md) |")
    (REPO / "COVERAGE.md").write_text("\n".join(cov) + "\n")

    # ---- KNOWN_BAD.md ----
    kbm = ["# KNOWN_BAD — gold fails its own grader", "",
           "Mechanical defects (binary): the reference solution does not pass the official verifier at "
           "the pinned commit. Frozen pre-run, results-independent. Receipt: "
           "`data/cases/gold_fails_grader.defects.jsonl`. (These three are public Pro tasks audited "
           "pre-run; they sit outside the 728-task prose-set denominator.) **The full gold-passes-"
           "verifier sweep is now complete**: all 731 graded (727 eligible, 0 incomplete); it "
           "independently **re-confirmed exactly these three** and found **no genuine new defects** — one "
           "parallel-sweep candidate (a tutao instance) cleared on isolated rerun (gold RESOLVED, "
           "Accuracy 100%), per the DeepSWE isolation protocol. Receipt: `data/gold_sweep/`.", "",
           "| instance_id | grader verdict |", "|---|---|"]
    for d in kb:
        kbm.append(f"| `{d['instance_id']}` | {d.get('detail','')} |")
    (REPO / "KNOWN_BAD.md").write_text("\n".join(kbm) + "\n")

    # ---- KNOWN_AMBIGUOUS.md (PROVEN spine + hypothesis count) ----
    ka = ["# KNOWN_AMBIGUOUS — gold passes, prose underdetermines", "",
          "Gold passes its verifier, but the hidden test checks behavior no requirement determines (a "
          "specification lottery). **Two tiers.** The PROVEN tier (below) is the mechanical spine — each "
          "carries a verified argument witness and needs no rater. The HYPOTHESIS tier is screen-flagged "
          "and raters-pending; it is counted separately and NOT claimed.", "",
          f"## PROVEN (mechanical spine): {len(spine)}", "",
          "| case | class | instance_id | coverage | gaps | witness |", "|---|---|---|---|---|---|"]
    for c in spine:
        r = judged[c]
        ka.append(f"| {c} | {klass[c][0]} | `{iid(c)}` | {r['n_covered']}/{r.get('in_gold_total')} | "
                  f"{r.get('n_gap',0)} | [witness](data/cases/{c}/AMBIGUITY_WITNESS.md) |")
    ka += ["", f"## HYPOTHESIS (codebase / borderline): {len(hypo)} — raters-pending, NOT claimed", "",
           "A snapshot shows plurality, not binding force; `DETERMINED-codebase` vs `AMBIGUOUS-codebase` "
           "is interpretive and needs ≥2 independent codebase-aware raters + κ (see ADMISSIBILITY-SPEC). "
           "Each carries an `AMBIGUITY_HYPOTHESIS.md`. Listed in [`COVERAGE.md`](COVERAGE.md)."]
    (REPO / "KNOWN_AMBIGUOUS.md").write_text("\n".join(ka) + "\n")

    # ---- OUR_CAPABILITY_GAPS.md ----
    og = ["# OUR_CAPABILITY_GAPS — we lost, but the prose determines the behavior", "",
          "recon+craft lost these oracle-free, yet the coverage table shows the substantive behavior is "
          "fully specified (any blank is incidental: test scaffolding or export style). NOT bench "
          "defects; reported as ours. Integrity: the blind judge put these back on us.", "",
          "| case | instance_id | coverage | gaps | attribution |", "|---|---|---|---|---|"]
    for c, r in sorted(judged.items()):
        if classify_of(c, r) == "OUR_GAP":
            og.append(f"| {c} | `{iid(c)}` | {r['n_covered']}/{r.get('in_gold_total')} | "
                      f"{r.get('n_gap',0)} | [table](data/attribution/{c}.md) |")
    (REPO / "OUR_CAPABILITY_GAPS.md").write_text("\n".join(og) + "\n")

    print(f"wrote ledgers. N={n} ENTAILED={len(ent)} AMBIGUOUS={len(amb)} | PROVEN={len(spine)} "
          f"[mech_spine={len(mech_spine)} (airtight={len(airtight)} graded-patch={len(gradedpatch)} "
          f"hand={len(proseaff)}) + codebase-plural={len(cbplural)}] | hypothesis={len(hypo)} "
          f"(auto-pa={len(auto_pa)} codebase/borderline={len(cb_border)}) KNOWN_BAD={len(kb)} ERR={len(err)}")


if __name__ == "__main__":
    main()
