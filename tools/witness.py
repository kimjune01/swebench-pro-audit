#!/usr/bin/env python3
"""witness.py -- draft + MECHANICALLY VERIFY an ambiguity witness for an AMBIGUOUS-flagged case.

For each case with >=1 GAP (from data/judge/<slug>.json), codex proposes the single strongest
ambiguity witness over the GAP behaviors and classifies it into the spec's grid:

  airtight          -- keyed to an arbitrary constant present ONLY in gold+test (absent prose + codebase)
  prose-affirmative -- the prose explicitly describes the ALTERNATIVE reading R2 (tutao pattern)
  codebase          -- a codebase convention is relevant but non-binding (HYPOTHESIS; raters-pending)
  borderline        -- a single plausible convention might bind (HYPOTHESIS; panel/graded-patch pending)

codex only PROPOSES. Python then verifies, mechanically:
  - every anchor (prose clause / gold snippet / test assertion) resolves verbatim in its file;
  - airtight: the discriminating constant is ABSENT from the prose (spec.md), and -- when --clone is
    passed -- ABSENT from the codebase at base_commit (a cached git clone + ripgrep). Absent from both,
    present only in gold+test => airtight, claimable. Present in the codebase => downgraded to codebase.
  - prose-affirmative: the quoted R2-supporting prose clause verifies verbatim in spec.md.

Only airtight + prose-affirmative that PASS verification are written as PROVEN witnesses
(AMBIGUITY_WITNESS.md). codebase/borderline (and any that fail the airtight grep) are written to
AMBIGUITY_HYPOTHESIS.md and flagged raters-pending -- never claimed.

  tools/witness.py <slug> [<slug> ...] [--clone] [--workers 8]
  tools/witness.py --all [--clone] [--workers 8]   # every AMBIGUOUS case lacking a witness
"""
import sys, json, re, subprocess, pathlib, shutil, concurrent.futures as cf

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"
JUDGE = AUDIT / "data" / "judge"
CACHE = AUDIT / ".cache" / "repos"
COMPANION = pathlib.Path("/Users/junekim/Documents/swebench-pro")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import judge_pool as jp  # reuse aggr/cited/find_line

_HF = None
REVERIFY = False  # set in main(): re-verify from cached codex drafts instead of re-calling codex


def hf_row(iid):
    global _HF
    if _HF is None:
        from datasets import load_dataset
        ds = load_dataset("ScaleAI/SWE-bench_Pro", split="test")
        _HF = {r["instance_id"]: r for r in ds}
    return _HF.get(iid)


PROMPT = """You are a benchmark determinacy auditor. A screening pass already found GAP behaviors in this
task: behaviors the HIDDEN TEST checks and the GOLD PATCH implements, but that NO prose requirement
states. Your job: pick the SINGLE strongest ambiguity witness among the GAP behaviors and classify it.

Definitions (be strict):
- "airtight": the behavior is pinned by an ARBITRARY CONSTANT (a specific number, string literal, count,
  delay, key name) that a solver could not derive from the prose -- it is a free authorial choice. Give
  the EXACT constant token as it appears in gold+test (e.g. 60000, "404", two).
- "prose-affirmative": the prose EXPLICITLY describes a DIFFERENT, equally-faithful contract R2 than the
  one the test pins (R1). Quote the verbatim prose clause that supports R2.
- "codebase": the rule might be set by a codebase convention, not the prose. (We treat this as a
  hypothesis, not proof.)
- "borderline": a single plausible reading might bind; a competent engineer might deviate.

For the chosen witness output ONLY this JSON:
{
 "test_behavior": "the GAP behavior, concrete",
 "klass": "airtight" | "prose-affirmative" | "codebase" | "borderline",
 "constant": "the arbitrary constant token (airtight only; else null)",
 "r2_prose_clause": "verbatim prose clause supporting the alternative (prose-affirmative only; else null)",
 "gold_anchor": "verbatim snippet from GOLD PATCH implementing R1 (the test-pinned reading)",
 "test_assertion": "verbatim snippet from HIDDEN TEST that discriminates R1 from R2",
 "R1": "the reading the test pins (one sentence)",
 "R2": "a prose-faithful alternative a from-prose engineer could ship (one sentence)",
 "why_R2_fails": "why R2 fails the test assertion (one sentence)"
}
Copy all quoted snippets EXACTLY. Do NOT use anything you recall about this repo.

=== PROBLEM + REQUIREMENTS + INTERFACE (prose) ===
{spec}

=== GOLD PATCH ===
{gold}

=== HIDDEN TEST ===
{test}

=== GAP BEHAVIORS (screen) ===
{gaps}
"""


def clone_at(repo, commit):
    """cached git checkout of `repo` (owner/name) at `commit`; returns path or None."""
    dst = CACHE / repo.replace("/", "__")
    marker = dst / ".checked_out"
    if marker.exists() and marker.read_text().strip() == commit:
        return dst
    dst.mkdir(parents=True, exist_ok=True)
    try:
        if not (dst / ".git").exists():
            subprocess.run(["git", "init", "-q"], cwd=dst, check=True)
            subprocess.run(["git", "remote", "add", "origin", f"https://github.com/{repo}.git"],
                           cwd=dst, check=True)
        f = subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin", commit],
                           cwd=dst, capture_output=True, text=True)
        if f.returncode != 0:  # commit not fetchable shallow; full fetch
            subprocess.run(["git", "fetch", "-q", "origin"], cwd=dst, capture_output=True, text=True)
        co = subprocess.run(["git", "checkout", "-q", "-f", commit], cwd=dst,
                            capture_output=True, text=True)
        if co.returncode != 0:
            return None
        marker.write_text(commit)
        return dst
    except Exception:
        return None


def _signatures(const):
    """tokens to grep: ALWAYS the full constant verbatim, PLUS a convention-prefix signature for
    templated strings. The full constant is never dropped (a short constant like an HTTP code must
    still be grepped -- omitting it vacuously certifies 'airtight'). Conservative by design: an
    overmatch (e.g. bare `500` matching `1500`) only pushes a candidate toward 'found-in-codebase' ->
    downgraded to hypothesis, which is the safe direction for an audit."""
    sigs = [const]
    # convention/template prefix: stuff before the first variable/separator, if it is meaty (>=6 chars)
    m = re.match(r"[\[\]\s\"']*([A-Za-z0-9_:\-./]{6,}?)(?:[,$%{}\s]|$)", const)
    if m and m.group(1) != const and len(m.group(1)) >= 6:
        sigs.append(m.group(1))
    return [s for s in dict.fromkeys(sigs) if s]


def in_codebase(tree, const):
    """True if the constant (or its convention-prefix signature) occurs in the tree, excluding tests."""
    if not const:
        return False
    rg = shutil.which("rg")
    for sig in _signatures(const):
        if rg:
            r = subprocess.run([rg, "-l", "--fixed-strings", "-g", "!*test*", "-g", "!*spec*",
                                sig, str(tree)], capture_output=True, text=True)
        else:
            r = subprocess.run(["grep", "-rIl", "--exclude=*test*", sig, str(tree)],
                               capture_output=True, text=True)
        if r.stdout.strip():
            return True
    return False


def draft(case_dir):
    d = pathlib.Path(case_dir); short = d.name
    jf = JUDGE / f"{short}.json"
    if not jf.exists():
        return {"case": short, "skip": "no judge json"}
    rec = json.loads(jf.read_text())
    gaps = [r for r in rec.get("rows", []) if r.get("status") == "GAP"]
    if not gaps:
        return {"case": short, "skip": "no GAP"}
    spec = (d / "spec.md").read_text() if (d / "spec.md").exists() else ""
    gold = (d / "gold.diff").read_text() if (d / "gold.diff").exists() else ""
    test = (d / "hidden_test.diff").read_text()[:12000] if (d / "hidden_test.diff").exists() else ""
    gaptxt = "\n".join(f"- {g['test']}  [gold: {g.get('gold_anchor')}]" for g in gaps)
    prompt = (PROMPT.replace("{spec}", spec[:9000]).replace("{gold}", gold[:14000])
              .replace("{test}", test).replace("{gaps}", gaptxt[:3000]))
    out = JUDGE / f"{short}.witness.last.txt"
    if REVERIFY and out.exists():  # re-verify from the cached codex draft; no new codex call
        raw = out.read_text()
    else:
        cmd = ["codex", "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
               "-c", "model=gpt-5.5", "-o", str(out), prompt]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            raw = out.read_text() if out.exists() else ""
        except Exception as e:
            raw = f"__ERR__ {e}"
    try:
        cand = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return {"case": short, "skip": "codex parse fail"}
    return {"case": short, "dir": str(d), "cand": cand, "spec": spec, "gold": gold,
            "test": test, "rec": rec}


def verify(res, do_clone):
    """mechanical verification; sets res['verdict'] in {airtight, prose-affirmative, hypothesis}."""
    if "cand" not in res:
        return res
    d = pathlib.Path(res["dir"]); c = res["cand"]
    spec, gold, test = res["spec"], res["gold"], res["test"]
    nspec = jp.aggr(spec)
    # citation checks
    ga = c.get("gold_anchor"); ta = c.get("test_assertion")
    res["gold_ok"] = bool(ga) and jp.cited(ga, jp.aggr(gold),
                                           set(w for w in jp.aggr(gold).split() if len(w) > 3))
    res["test_ok"] = bool(ta) and jp.cited(ta, jp.aggr(test),
                                           set(w for w in jp.aggr(test).split() if len(w) > 3))
    klass = c.get("klass")
    verdict = "hypothesis"
    if klass == "airtight":
        const = (c.get("constant") or "").strip()
        in_prose = bool(const) and const.lower() in spec.lower()
        res["const_in_prose"] = in_prose
        res["const_in_codebase"] = None
        base_ok = bool(const) and not in_prose and res["gold_ok"] and res["test_ok"]
        # airtight is ONLY claimable when codebase-absence is certified by a clone+grep.
        # absent prose+codebase, present only in gold+test -> airtight. Otherwise -> hypothesis.
        if base_ok and do_clone:
            row = hf_row((d / "instance_id.txt").read_text().strip())
            tree = clone_at(row["repo"], row["base_commit"]) if row else None
            if tree is not None:
                inc = in_codebase(tree, const)
                res["const_in_codebase"] = inc
                if inc is False:
                    verdict = "airtight"
                # inc True (convention exists) or clone failed (None) -> stays hypothesis
    elif klass == "prose-affirmative":
        clause = c.get("r2_prose_clause")
        cl_ok = bool(clause) and jp.cited(clause, nspec, set(w for w in nspec.split() if len(w) > 3))
        res["r2_clause_ok"] = cl_ok
        if cl_ok and res["gold_ok"] and res["test_ok"]:
            verdict = "prose-affirmative"
    res["verdict"] = verdict
    return res


def render(res):
    d = pathlib.Path(res["dir"]); short = d.name
    c = res["cand"]; v = res["verdict"]
    iid = (d / "instance_id.txt").read_text().strip()
    gl = jp.find_line(res["gold"], c.get("gold_anchor"))
    tl = jp.find_line(res["test"], c.get("test_assertion"))
    sl = jp.find_line(res["spec"], c.get("r2_prose_clause")) if c.get("r2_prose_clause") else None

    def a(label, f, ln):
        return f"[`{f}`{('#L'+str(ln)) if ln else ''}]({f}{('#L'+str(ln)) if ln else ''})" if label else ""

    # Only airtight (codebase-grep-certified) is auto-PROVEN. Auto prose-affirmative is NOT claimed:
    # its only mechanical check is that the cited clause exists verbatim -- not that the clause LICENSES
    # R2. That entailment is codex's judgment (the "auditor-constructed R2" hole, codex sniff v2), so it
    # is a disciplined hypothesis pending raters, exactly like the codebase class. (tutao stays PROVEN
    # via its hand-authored witness, which --all never overwrites.)
    proven = v == "airtight"
    title = "Ambiguity witness" if proven else "Ambiguity HYPOTHESIS (raters-pending, NOT claimed)"
    L = [f"# {title} -- {short}", "",
         f"- instance_id: `{iid}`",
         f"- class: **{v}** ({'PROVEN -- mechanical spine' if proven else 'disciplined hypothesis'})",
         f"- witness: argument; one behavior suffices (existence proof).", "",
         "## The graded behavior",
         f"{c.get('test_behavior','')}",
         f"- test assertion: {a(c.get('test_assertion'),'hidden_test.diff',tl)} `{c.get('test_assertion')}`",
         "", "## Two readings; the test pins one",
         f"- **R1 (test-pinned / gold):** {c.get('R1','')}  gold: {a(c.get('gold_anchor'),'gold.diff',gl)} `{c.get('gold_anchor')}`",
         f"- **R2 (prose-faithful alternative):** {c.get('R2','')}", ""]
    if v == "airtight":
        L += ["## Why airtight",
              f"The discriminating constant `{c.get('constant')}` appears nowhere a solver reads: "
              f"absent from the prose (spec.md){' and from the codebase at base_commit (ripgrep)' if res.get('const_in_codebase') is False else ''}, "
              f"present only in gold+test. A solver has no source for it but mindreading the author.", ""]
    elif v == "prose-affirmative":
        L += ["## Status: HYPOTHESIS (prose-affirmative, raters-pending)",
              f"codex reads the prose clause {a(c.get('r2_prose_clause'),'spec.md',sl)} "
              f"\"{c.get('r2_prose_clause')}\" as licensing R2 over the test-pinned R1. The clause is "
              "verified to exist verbatim, but whether it *entails* R2 is codex's judgment, not a "
              "mechanical fact (the auditor-constructed-R2 hole). **Not counted in the claimable spine** "
              "until >=2 independent raters concur. The hand-verified `tutao` is the only PROVEN "
              "prose-affirmative case.", ""]
    else:
        L += ["## Status: HYPOTHESIS",
              f"Class `{c.get('klass')}` is not snapshot-decidable as underdetermination (plurality != "
              f"binding force; see ADMISSIBILITY-SPEC.md). Flagged for >=2 independent codebase-aware "
              f"raters + kappa. **Not counted in the claimable spine.**", ""]
    L += [f"## Why R2 fails the test", c.get("why_R2_fails", ""), "",
          "_codex proposed; anchors mechanically verified against the committed gold/test/prose._"]
    name = "AMBIGUITY_WITNESS.md" if proven else "AMBIGUITY_HYPOTHESIS.md"
    (d / name).write_text("\n".join(L) + "\n")
    return name


def main():
    global REVERIFY
    a = sys.argv
    do_clone = "--clone" in a
    REVERIFY = "--reverify" in a
    workers = int(a[a.index("--workers") + 1]) if "--workers" in a else 8
    if "--all" in a:
        slugs = []
        for jf in sorted(JUDGE.glob("*.json")):
            try:
                r = json.loads(jf.read_text())
            except Exception:
                continue
            if r.get("verdict") == "AMBIGUOUS":
                d = CASES / jf.stem
                if d.exists() and not (d / "AMBIGUITY_WITNESS.md").exists() \
                        and not (d / "AMBIGUITY_HYPOTHESIS.md").exists():
                    slugs.append(jf.stem)
    else:
        slugs = [x for x in a[1:] if not x.startswith("--")]
    dirs = [str(CASES / s) for s in slugs]
    print(f"witness over {len(dirs)} cases (clone={do_clone}, draft-workers={workers})")
    # Phase 1: draft all via codex in parallel (independent, fast).
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        drafts = list(ex.map(draft, dirs))
    # Phase 2: verify+render SERIALLY -- clone_at re-checks-out a per-repo dir, so concurrent
    # checkouts of the same repo at different commits would race. Serial verify avoids that.
    air = pa = hyp = skip = 0
    for res in drafts:
        if "cand" not in res:
            skip += 1; print(f"  {res['case']:36s} SKIP {res.get('skip')}"); continue
        verify(res, do_clone)
        name = render(res)
        v = res["verdict"]
        air += v == "airtight"; pa += v == "prose-affirmative"; hyp += v == "hypothesis"
        print(f"  {res['case']:36s} {v:17s} -> {name}")
    print(f"DONE: airtight={air} prose-affirmative={pa} hypothesis={hyp} skip={skip}")


if __name__ == "__main__":
    main()
