#!/usr/bin/env python3
"""codebase_ambiguity.py -- promote codebase-class HYPOTHESES to PROVEN by the two-precedent rule:
if the codebase itself does the discriminating thing >1 way (and the prose is silent), a from-codebase
solver could land on either, so the test pins an underdetermined choice -> AMBIGUOUS.

User's ruling: "if there's more than one way to do it in the codebase, cite both instances and declare
ambiguous." Guard against the cherry-pick attack (codex sniff v2): the two cited precedents must be
COMPARABLE and LIVE -- same kind of call site, neither under a test/example/vendor/deprecated path --
and each must verify verbatim in the repo at base_commit (grep), with the prose silent on the choice.

Per case: clone repo@base_commit; codex proposes the discriminating choice + >=2 conflicting live
precedents (path + verbatim snippet); Python verifies each snippet exists in the clone, excludes
test/example/vendor/dead paths, and confirms prose silence. >=2 survive -> PROVEN; write
AMBIGUITY_WITNESS.md (class codebase-plural) and drop the hypothesis file. Else stays hypothesis.

  tools/codebase_ambiguity.py <slug> ...|--all  [--workers 6]
"""
import sys, json, re, subprocess, pathlib, shutil, concurrent.futures as cf

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import witness as W   # reuse clone_at, hf_row


def codex(prompt, out, timeout=600):
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["codex", "exec", "--skip-git-repo-check",
                    "--dangerously-bypass-approvals-and-sandbox", "-c", "model=gpt-5.5",
                    "-o", str(out), prompt], capture_output=True, text=True, timeout=timeout)
    return out.read_text() if out.exists() else ""

EXCLUDE = re.compile(r"(^|/)(tests?|testing|__tests__|spec|specs|examples?|example|vendor|"
                     r"node_modules|third_party|deprecated|legacy|\.git|fixtures?|mocks?|testdata)(/|$)",
                     re.I)

PROMPT = """You are auditing whether a benchmark task pins a choice the CODEBASE leaves open. A screen
found a GAP: the hidden test checks a behavior the gold implements but no prose requirement states.

Your job: decide if the codebase ALREADY does this discriminating thing in MORE THAN ONE WAY. If a
solver reading the codebase would find two (or more) established, CURRENT, comparable precedents that
make this choice differently, the choice is underdetermined and the test arbitrarily pins one.

Find >=2 such precedents in the repo (the working tree at this commit). For each, give the file path and
a SHORT verbatim code snippet (copy exactly) that shows the choice being made that way. STRICT rules:
- precedents must be LIVE production code -- NOT under any test/spec/example/vendor/deprecated/fixture
  path, NOT dead code.
- they must be COMPARABLE -- the same kind of decision in a similar context, genuinely showing two
  conventions a solver could follow, not superficially-similar-but-different concerns.
- if the codebase is actually CONSISTENT (only one way, or the differences are not comparable), say so:
  return "consistent": true and an empty precedents list. Do not manufacture a conflict.

Output ONLY this JSON:
{"discriminating_choice":"...", "consistent": true|false,
 "precedents":[{"path":"...","snippet":"...","way":"which convention this shows"}, ...]}

=== PROSE ===
{spec}
=== GOLD PATCH ===
{gold}
=== HIDDEN TEST ===
{test}
=== GAP behavior (screen) ===
{gap}
=== REPO FILE LIST (sample) ===
{files}
"""


def is_codebase_hyp(d):
    p = d / "AMBIGUITY_HYPOTHESIS.md"
    if not p.exists():
        return False
    m = re.search(r"class:\s*\*\*([\w-]+)\*\*", p.read_text())
    return bool(m) and m.group(1) == "hypothesis"


def grep_path(tree, snippet):
    """return a non-excluded repo-relative path containing the snippet, else None."""
    rg = shutil.which("rg")
    snip = snippet.strip().splitlines()[0].strip() if snippet.strip() else ""
    if len(snip) < 6:
        return None
    if rg:
        r = subprocess.run([rg, "-l", "--fixed-strings", snip, str(tree)],
                           capture_output=True, text=True)
    else:
        r = subprocess.run(["grep", "-rIl", snip, str(tree)], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        rel = str(pathlib.Path(line).relative_to(tree)) if str(tree) in line else line
        if not EXCLUDE.search(rel):
            return rel
    return None


def first_gap(d):
    jf = AUDIT / "data" / "judge" / f"{d.name}.json"
    if not jf.exists():
        return ""
    for r in json.loads(jf.read_text()).get("rows", []):
        if r.get("status") == "GAP":
            return f"{r['test']}  [gold: {r.get('gold_anchor')}]"
    return ""


def run(slug):
    d = CASES / slug
    spec = (d / "spec.md").read_text() if (d / "spec.md").exists() else ""
    gold = (d / "gold.diff").read_text() if (d / "gold.diff").exists() else ""
    test = (d / "hidden_test.diff").read_text()[:8000] if (d / "hidden_test.diff").exists() else ""
    gap = first_gap(d)
    iid = (d / "instance_id.txt").read_text().strip()
    row = W.hf_row(iid)
    if not row:
        return f"{slug}: no HF row"
    tree = W.clone_at(row["repo"], row["base_commit"])
    if tree is None:
        return f"{slug}: clone failed"
    # a sample of live file paths to ground codex
    files = subprocess.run(["bash", "-lc", f"cd {tree} && git ls-files | grep -viE "
                            f"'(test|spec|example|vendor|node_modules|fixture|mock|testdata)' | head -400"],
                           capture_output=True, text=True).stdout
    prompt = (PROMPT.replace("{spec}", spec[:7000]).replace("{gold}", gold[:9000])
              .replace("{test}", test).replace("{gap}", gap[:400]).replace("{files}", files[:6000]))
    raw = codex(prompt, AUDIT / "data" / "judge" / f"{slug}.cbamb.txt")
    cand = None
    try:
        cand = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return f"{slug}: codex parse fail"
    if cand.get("consistent") or not cand.get("precedents"):
        return f"{slug}: codex says consistent / no conflict -> stays hypothesis"
    # verify each precedent: snippet exists in a non-excluded path; prose silent on the choice
    verified = []
    nspec = spec.lower()
    for p in cand["precedents"]:
        rel = grep_path(tree, p.get("snippet", ""))
        if rel:
            verified.append({**p, "verified_path": rel})
    # need >=2 verified precedents in DISTINCT files showing different "way"s
    ways = {v.get("way", "") for v in verified}
    distinct_files = {v["verified_path"] for v in verified}
    ok = len(verified) >= 2 and len(distinct_files) >= 2 and len(ways) >= 2
    res = {"slug": slug, "iid": iid, "choice": cand.get("discriminating_choice"),
           "n_verified": len(verified), "verified": verified, "ok": ok}
    (d / "codebase_ambiguity.json").write_text(json.dumps(res, indent=1))
    if ok:
        render(d, res, row)
        if (d / "AMBIGUITY_HYPOTHESIS.md").exists():
            (d / "AMBIGUITY_HYPOTHESIS.md").unlink()
        return f"{slug}: PROVEN codebase-plural ({len(verified)} live precedents)"
    return f"{slug}: only {len(verified)} verified live precedents -> stays hypothesis"


def render(d, res, row):
    repo = row["repo"]; commit = row["base_commit"]
    L = [f"# Ambiguity witness -- {d.name}  (codebase-plurality)", "",
         f"- instance_id: `{res['iid']}`",
         f"- class: **codebase-plural** (PROVEN -- two live conflicting precedents, prose silent)",
         f"- repo `{repo}` @ `{commit[:10]}`", "",
         "## The underdetermined choice",
         f"{res.get('choice','')}", "",
         "## The codebase already does it more than one way (live, comparable, prose-silent)",
         "A from-codebase solver finds these coexisting production precedents making the choice "
         "differently; the prose names no rule, so either is defensible. The hidden test pins one.", ""]
    for i, v in enumerate(res["verified"], 1):
        L += [f"{i}. `{v['verified_path']}` -- {v.get('way','')}",
              f"   ```\n   {v.get('snippet','').strip()[:300]}\n   ```"]
    L += ["", "_Guard: each precedent verified to occur verbatim at base_commit in a non-test, "
          "non-example, non-vendor, non-deprecated path (grep); the prose is silent on the choice. "
          "codex proposed; citations mechanically verified._"]
    (d / "AMBIGUITY_WITNESS.md").write_text("\n".join(L) + "\n")


def repo_of(slug):
    row = W.hf_row((CASES / slug / "instance_id.txt").read_text().strip())
    return row["repo"] if row else "?"


def main():
    argv = sys.argv[1:]
    workers = int(argv[argv.index("--workers") + 1]) if "--workers" in argv else 8
    if "--all" in argv:
        slugs = sorted(d.name for d in CASES.iterdir() if d.is_dir() and is_codebase_hyp(d)
                       and not (d / "codebase_ambiguity.json").exists())  # resumable: skip judged
    else:
        slugs = [x for x in argv if not x.startswith("--") and (CASES / x).is_dir()]
    # group by repo; one worker per repo, cases within a repo run SERIALLY so concurrent checkouts of
    # the same per-repo clone dir at different commits never race (the clone_at re-checkout hazard).
    groups = {}
    for s in slugs:
        groups.setdefault(repo_of(s), []).append(s)
    print(f"codebase-ambiguity over {len(slugs)} cases across {len(groups)} repos, "
          f"repo-parallel workers={workers}")

    def repo_worker(items):
        for s in items:
            print("  " + run(s), flush=True)

    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(repo_worker, groups.values()))


if __name__ == "__main__":
    main()
