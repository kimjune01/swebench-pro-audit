#!/usr/bin/env python3
"""plurality_proof.py -- the TWO-EXPERT standard, applied case by case with receipts.

Imagine two of the world's best engineers given only the prose + the repo source. If both write a
reasonable, requirement-faithful implementation but the hidden test passes one and fails the other, the
bench is imperfect: it grades an unstated choice. That split has exactly two sources, EITHER of which
proves it:
  PROSE  -- the requirement text licenses >=2 readings, both faithful (receipt: the unselecting span).
  SOURCE -- the codebase already makes the SAME decision >=2 live, comparable, prose-silent ways
            (receipt: >=2 verbatim non-test snippets).

This SUPERSEDES the opus-convergence demotion. "A solver would probably converge" is a likelihood poll,
not an existence proof; under the two-expert standard it does not discharge a genuine split. codex is
asked to CONSTRUCT the proof (or refute it) against this standard, adversarial against itself.

Reads spec.md (prose), codebase_ambiguity.json (the discriminating choice + pre-verified source
precedents). Writes the verdict back into codebase_ambiguity.json and (re)writes the witness/hypothesis
markdown with the two-axis receipt. Resumable: skips cases already carrying a two_expert verdict unless
--force.

  tools/plurality_proof.py <slug> ...|--all [--workers 6] [--force]
"""
import sys, json, re, subprocess, pathlib, concurrent.futures as cf

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"
JUDGE = AUDIT / "data" / "judge"
TIMEOUT = 300

PROMPT = (AUDIT / "tools" / "plurality_proof.prompt.txt").read_text()


def codex(prompt):
    """Prompt via stdin (`-`); codex blocks on a tty-less stdin otherwise."""
    try:
        r = subprocess.run(
            ["timeout", str(TIMEOUT), "codex", "exec", "--skip-git-repo-check",
             "--dangerously-bypass-approvals-and-sandbox", "-c", "model=gpt-5.5", "-"],
            input=prompt, capture_output=True, text=True, timeout=TIMEOUT + 30)
        return r.stdout
    except Exception:
        return ""


def extract_json(text):
    """Grab the last well-formed {"prose_plurality"...} object (codex prints prose then the JSON)."""
    key = '{"prose_plurality"'
    i = text.rfind(key)
    if i < 0:
        return None
    depth, instr, esc = 0, False, False
    for j in range(i, len(text)):
        c = text[j]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[i:j + 1])
                    except Exception:
                        return None
    return None


def witness_md(slug, iid, repo_line, j):
    pp, sp = j.get("prose_plurality", {}), j.get("source_plurality", {})
    verdict = j.get("verdict", "")
    axis = {"ambiguous-prose": "prose", "ambiguous-source": "source",
            "ambiguous-both": "prose+source"}.get(verdict, "?")
    cls = {"ambiguous-prose": "prose-plural", "ambiguous-source": "codebase-plural",
           "ambiguous-both": "plural-both"}.get(verdict, "plural")
    out = [f"# Ambiguity witness -- {slug}  (two-expert split: {axis})", "",
           f"- instance_id: `{iid}`",
           f"- class: **{cls}** (PROVEN under the two-expert standard)",
           f"- {repo_line}", "",
           "## The two-expert split",
           "Two of the world's best engineers, given only the prose and the source, both write a "
           "requirement-faithful implementation; the hidden test passes one and fails the other.", "",
           f"**Why both are reasonable:** {j.get('why','')}", ""]
    if pp.get("exists"):
        out += ["## Prose plurality (the requirement text licenses both)",
                f"- **Reading A:** {pp.get('reading_A','')}",
                f"- **Reading B:** {pp.get('reading_B','')}",
                f"- **Both survive expert review:** {pp.get('both_survive_expert_review','')}",
                f"- **The hidden test pins:** {pp.get('test_pins','')}",
                "- **Unselecting prose span (verbatim):**", "  ```",
                "  " + (pp.get("unselecting_prose_quote", "") or "").replace("\n", "\n  "), "  ```", ""]
    if sp.get("exists"):
        out += ["## Source plurality (the codebase already does it both ways)",
                f"- **The same decision:** {sp.get('same_decision','')}"]
        for k, p in enumerate(sp.get("precedents", []), 1):
            out += [f"{k}. `{p.get('path','')}` -- {p.get('way','')}", "   ```",
                    "   " + (p.get("snippet", "") or "").replace("\n", "\n   "), "   ```"]
        out += [""]
    out += ["_Guard: prose readings checked against the task's own spec.md; source precedents are the "
            "pre-verified set (grep'd verbatim at base_commit, non-test/non-vendor). Two-expert standard "
            "supersedes the opus-convergence demotion: existence of the split, not likelihood of "
            "convergence._"]
    return "\n".join(out) + "\n"


def hypothesis_md(slug, j):
    return (f"# Ambiguity HYPOTHESIS (two-expert: DETERMINED -- not claimed) -- {slug}\n\n"
            "- class: **determined** (NOT claimed)\n"
            f"- Under the two-expert standard, no genuine split: {j.get('why','')}\n"
            "- Either the prose/interface selects one answer, or the cited source precedents are not the "
            "same decision in comparable context (lookalikes). Not underdetermined.\n")


def check(slug):
    d = CASES / slug
    caf = d / "codebase_ambiguity.json"
    spec = d / "spec.md"
    if not caf.exists() or not spec.exists():
        return slug, None, "missing spec.md / codebase_ambiguity.json"
    ca = json.loads(caf.read_text())
    if ca.get("two_expert") and "--force" not in sys.argv:
        return slug, ca["two_expert"].get("two_expert_split"), "cached"
    prec = "\n".join(
        f"- {p.get('verified_path', p.get('path'))}: {p.get('way','')}\n    {(p.get('snippet') or '')[:240]}"
        for p in ca.get("verified", []))
    prompt = (PROMPT.replace("{SPEC}", spec.read_text()[:11000])
              .replace("{CHOICE}", str(ca.get("choice", "")))
              .replace("{PREC}", prec[:2500] or "(none proposed)"))
    raw = codex(prompt)
    JUDGE.mkdir(exist_ok=True)
    (JUDGE / f"{slug}.plur.txt").write_text(raw)
    j = extract_json(raw)
    if not j:
        return slug, None, "parse fail (raw kept)"
    ca["two_expert"] = j
    caf.write_text(json.dumps(ca, indent=1))
    iid = ca.get("iid", (d / "instance_id.txt").read_text().strip() if (d / "instance_id.txt").exists() else slug)
    # find an existing repo line to preserve, else synthesize
    repo_line = "repo (see instance_id)"
    for fn in ("AMBIGUITY_WITNESS.md", "AMBIGUITY_HYPOTHESIS.md"):
        p = d / fn
        if p.exists():
            m = re.search(r"^- repo .*$", p.read_text(), re.M)
            if m:
                repo_line = m.group(0)[2:]
                break
    wf, hf = d / "AMBIGUITY_WITNESS.md", d / "AMBIGUITY_HYPOTHESIS.md"
    split = bool(j.get("two_expert_split")) and j.get("verdict", "").startswith("ambiguous")
    if split:
        wf.write_text(witness_md(slug, iid, repo_line, j))
        if hf.exists():
            hf.unlink()
    else:
        hf.write_text(hypothesis_md(slug, j))
        if wf.exists():
            wf.unlink()
    return slug, split, j.get("verdict", "")


def main():
    a = sys.argv[1:]
    workers = int(a[a.index("--workers") + 1]) if "--workers" in a else 6
    if "--all" in a:
        slugs = []
        for d in sorted(CASES.iterdir()):
            if not d.is_dir():
                continue
            for fn in ("AMBIGUITY_WITNESS.md", "AMBIGUITY_HYPOTHESIS.md"):
                p = d / fn
                if p.exists() and re.search(r"codebase-plural", p.read_text()):
                    slugs.append(d.name)
                    break
    else:
        slugs = [x for x in a if not x.startswith("--") and (CASES / x).is_dir()]
    print(f"two-expert plurality proof over {len(slugs)} cases, workers={workers}")
    split = det = skip = 0
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for slug, verdict, note in ex.map(check, slugs):
            if verdict is None:
                skip += 1
                print(f"  {slug:26} SKIP   {note}")
                continue
            split += bool(verdict)
            det += (not verdict)
            print(f"  {slug:26} {'SPLIT ' if verdict else 'determ'} {note}")
    print(f"DONE: two_expert_split(WITNESS)={split}  determined(demoted)={det}  skip={skip}")


if __name__ == "__main__":
    main()
