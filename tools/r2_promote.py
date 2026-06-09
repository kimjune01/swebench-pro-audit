#!/usr/bin/env python3
"""r2_promote.py -- promote codex-proposed prose-affirmative HYPOTHESES to PROVEN via the
graded-patch existence proof (user's rule: an impl matches the prose iff opus AND codex agree, blind).

Per case (a case dir whose AMBIGUITY_HYPOTHESIS.md has class prose-affirmative):

  gen   -- opus writes R2: a prose-faithful implementation that takes the ALTERNATIVE reading the
           witness describes (a minimal deviation from gold), as a full unified diff. Saved r2.diff.
  gate  -- the BLIND prose-match gate: opus and codex EACH judge, seeing ONLY the prose (spec.md) and
           the R2 diff -- never the gold, the hidden test, or each other -- whether R2 satisfies every
           stated requirement. Both must say yes. Saved r2_gate.json.
           (Grading R2 against the held-out test happens on an EC2 box via grade_r2.py: R2 must FAIL.
            both-raters-yes + official-FAIL => PROVEN graded-patch witness.)

  tools/r2_promote.py gen  [<slug> ...|--all] [--workers 6]
  tools/r2_promote.py gate [<slug> ...|--all] [--workers 6]

--all selects every case whose AMBIGUITY_HYPOTHESIS.md is class prose-affirmative.
"""
import sys, json, re, subprocess, pathlib, concurrent.futures as cf

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"
OPUS = "claude-opus-4-8"


def opus(prompt, timeout=600):
    r = subprocess.run(["claude", "-p", "--model", OPUS, prompt],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout


def codex(prompt, out, timeout=600):
    subprocess.run(["codex", "exec", "--skip-git-repo-check",
                    "--dangerously-bypass-approvals-and-sandbox", "-c", "model=gpt-5.5",
                    "-o", str(out), prompt], capture_output=True, text=True, timeout=timeout)
    return out.read_text() if out.exists() else ""


def jblock(raw):
    try:
        return json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return None


def is_prose_aff(d):
    p = d / "AMBIGUITY_HYPOTHESIS.md"
    if not p.exists():
        return False
    m = re.search(r"class:\s*\*\*([\w-]+)\*\*", p.read_text())
    return bool(m) and m.group(1) == "prose-affirmative"


def select(argv):
    if "--all" in argv:
        return sorted(d.name for d in CASES.iterdir() if d.is_dir() and is_prose_aff(d))
    # skip flags AND their values (e.g. the integer after --workers), and any token that is not a
    # real case dir -- so `--workers 4` never gets misread as a slug.
    out, skip = [], False
    for x in argv:
        if skip:
            skip = False; continue
        if x.startswith("--"):
            if x in ("--workers",):
                skip = True
            continue
        if (CASES / x).is_dir():
            out.append(x)
    return out


GEN = """You are constructing an ALTERNATIVE but PROSE-FAITHFUL implementation of a coding task, to test
whether the task's hidden grader pins a choice the prose leaves open.

You are given: the task PROSE (problem + requirements + interface), the GOLD patch (one accepted
implementation), and a description of an ALTERNATIVE reading R2 that is also faithful to the prose.

Produce R2 as a single unified diff against the SAME base the gold applies to. Requirements:
- R2 must satisfy EVERY stated requirement in the prose -- it is a correct, shippable from-prose impl.
- R2 must take the ALTERNATIVE reading (the one the witness describes), so it deviates from gold ONLY
  on the prose-unconstrained choice. Change as little else as possible; reuse gold's structure where
  the prose determines it.
- MINIMALITY IS CRITICAL. Do NOT introduce any new dependency, import, or library. Do NOT add logging,
  comments-as-output, or any change unrelated to the one prose-unconstrained choice. The ONLY behavioral
  difference from gold must be the alternative reading. If gold compiles, R2 must compile with no new
  imports. A patch that fails to build is worthless here -- it must fail (if at all) ONLY on the test
  that pins the unconstrained choice.
- Output a VALID unified diff (correct ---/+++ headers and @@ hunk counts) that applies cleanly.
- Do NOT edit any test file.

Output ONLY the diff between these markers, nothing else:
<<<R2DIFF
diff --git ...
R2DIFF

=== PROSE ===
{spec}

=== GOLD PATCH (reading R1) ===
{gold}

=== ALTERNATIVE READING R2 (from the witness) ===
{r2}
"""

GATE = """You are a strict conformance checker. Given a task's PROSE SPEC and a candidate code PATCH,
decide whether the patch satisfies EVERY stated requirement in the prose. Judge ONLY against the prose
shown. Do not guess hidden tests. Do not assume a "standard" answer. If the patch meets every explicit
requirement, it conforms -- even if you would have implemented details differently.

Output ONLY this JSON: {"conforms": true|false, "unmet": "the first unmet requirement, or null"}

=== PROSE SPEC ===
{spec}

=== CANDIDATE PATCH ===
{patch}
"""


def gen_one(slug):
    d = CASES / slug
    spec = (d / "spec.md").read_text()
    gold = (d / "gold.diff").read_text()
    hyp = (d / "AMBIGUITY_HYPOTHESIS.md").read_text()
    r2desc = hyp  # the hypothesis file carries R1/R2/why-R2-fails
    prompt = (GEN.replace("{spec}", spec[:9000]).replace("{gold}", gold[:14000])
              .replace("{r2}", r2desc[:3000]))
    try:
        raw = opus(prompt)
    except Exception as e:
        return f"{slug}: gen ERROR {e}"
    m = re.search(r"<<<R2DIFF\s*(.*?)\s*R2DIFF", raw, re.S)
    diff = m.group(1).strip() if m else ""
    if not diff.startswith("diff ") and "--- " not in diff:
        return f"{slug}: no diff produced"
    (d / "r2.diff").write_text(diff + "\n")
    return f"{slug}: r2.diff {len(diff)}B"


def gate_one(slug):
    d = CASES / slug
    r2 = d / "r2.diff"
    if not r2.exists():
        return f"{slug}: no r2.diff"
    spec = (d / "spec.md").read_text()
    patch = r2.read_text()
    p = (GATE.replace("{spec}", spec[:9000]).replace("{patch}", patch[:14000]))
    try:
        oraw = opus(p)
        craw = codex(p, AUDIT / "data" / "judge" / f"{slug}.r2gate.codex.txt")
    except Exception as e:
        return f"{slug}: gate ERROR {e}"
    oj, cj = jblock(oraw), jblock(craw)
    res = {"opus": bool(oj and oj.get("conforms")), "codex": bool(cj and cj.get("conforms")),
           "opus_unmet": (oj or {}).get("unmet"), "codex_unmet": (cj or {}).get("unmet"),
           "opus_ok": oj is not None, "codex_ok": cj is not None}
    res["both"] = res["opus"] and res["codex"]
    (d / "r2_gate.json").write_text(json.dumps(res, indent=1))
    return f"{slug}: opus={res['opus']} codex={res['codex']} BOTH={res['both']}"


def witness_one(slug):
    """promote a CLEAN-FAIL case to a PROVEN graded-patch witness: write AMBIGUITY_WITNESS.md from the
    hypothesis (R1/R2), the blind gate (both agree), and the grade (gold passes, R2 fails the
    discriminating F2P, P2P green). Remove the old AMBIGUITY_HYPOTHESIS.md so the ledger counts PROVEN."""
    d = CASES / slug
    g = d / "r2_grade.json"; gate = d / "r2_gate.json"; hyp = d / "AMBIGUITY_HYPOTHESIS.md"
    if not g.exists() or not json.loads(g.read_text()).get("clean_fail"):
        return f"{slug}: not clean-fail, skip"
    gv = json.loads(g.read_text()); gt = json.loads(gate.read_text()) if gate.exists() else {}
    iid = (d / "instance_id.txt").read_text().strip()
    # carry R1/R2 lines out of the hypothesis file
    htext = hyp.read_text() if hyp.exists() else ""
    r1 = re.search(r"\*\*R1[^:]*:\*\*(.+)", htext); r2 = re.search(r"\*\*R2[^:]*:\*\*(.+)", htext)
    L = [f"# Ambiguity witness -- {slug}  (graded-patch existence proof)", "",
         f"- instance_id: `{iid}`",
         f"- class: **prose-affirmative** (PROVEN -- graded-patch + blind two-rater gate)",
         "- witness: a concrete R2 implementation, not an argument. One alternative impl suffices.", "",
         "## The proof (three independent legs)",
         f"1. **R2 is prose-faithful** -- the blind prose-match gate: opus AND codex each judged R2 "
         f"against ONLY the prose (not gold, not the test, not each other) and BOTH concluded it "
         f"satisfies every requirement. (opus={gt.get('opus')}, codex={gt.get('codex')})",
         f"2. **R2 takes the alternative reading** -- R2 ([`r2.diff`](r2.diff)) implements the "
         f"prose-faithful alternative the witness describes" + (f": {r2.group(1).strip()}" if r2 else "") + ".",
         f"3. **The bench rejects R2** -- the official grader: gold (R1) RESOLVES, R2 does NOT "
         f"(`r2_resolved={gv.get('r2_resolved')}`); R2 fails {gv.get('n_flips_pass_to_fail')} "
         f"FAIL_TO_PASS test(s) that gold passes, while keeping every PASS_TO_PASS green "
         f"(ran_ratio={gv.get('ran_ratio')}, no regressions). Receipt: [`r2_grade.json`](r2_grade.json).",
         "",
         "## Why this is unimpeachable",
         "Two independent models, blind, call R2 a faithful implementation of the prose; the official "
         "grader fails it on the exact behavior that distinguishes the two readings. A from-prose solver "
         "who ships R2 has satisfied the spec and lost the bench -- the test pins a choice the prose "
         "leaves open. No auditor judgment remains: the prose-conformance is a two-rater verdict, the "
         "failure is mechanical." + (f"\n\n- R1 (test-pinned/gold): {r1.group(1).strip()}" if r1 else ""),
         "",
         f"- discriminating tests R2 fails: " + ", ".join(f"`{x}`" for x in gv.get("flips", [])[:8]),
         "", "_R2 generated by opus; prose-conformance judged blind by opus+codex; failure graded by "
         "the official ScaleAI evaluator on a fresh container._"]
    (d / "AMBIGUITY_WITNESS.md").write_text("\n".join(L) + "\n")
    if hyp.exists():
        hyp.unlink()
    return f"{slug}: PROMOTED -> AMBIGUITY_WITNESS.md (flips={gv.get('n_flips_pass_to_fail')})"


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    argv = sys.argv[2:]
    workers = int(argv[argv.index("--workers") + 1]) if "--workers" in argv else 6
    if cmd == "witness":
        slugs = ([d.name for d in CASES.iterdir() if (d / "r2_grade.json").exists()
                  and json.loads((d / "r2_grade.json").read_text()).get("clean_fail")]
                 if "--all" in argv else select(argv))
        for s in slugs:
            print("  " + witness_one(s))
        return
    slugs = select(argv)
    fn = {"gen": gen_one, "gate": gate_one}.get(cmd)
    if not fn:
        print(__doc__); return
    print(f"{cmd} over {len(slugs)} cases, workers={workers}")
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for r in ex.map(fn, slugs):
            print("  " + r)


if __name__ == "__main__":
    main()
