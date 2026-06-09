#!/usr/bin/env python3
"""divergence.py -- the determinacy axis (DETERMINATE vs UNDERDETERMINED / "divergent"), orthogonal to
the per-behavior coverage screen. A task can be per-behavior ENTAILED yet fail the admission standard
(competent uncontaminated implementers, from the prose alone, converge on a test-passing solution)
because the prose admits multiple incompatible faithful designs and the held-out test pins one.

Three tiers (codex review; do not collapse):
  MECHANICALLY-FLAGGED  breadth (gold files/regions/LOC) -- TRIAGE ONLY, never a label.
  RATER-ASSESSED        two independent blind raters (opus + codex) EACH produce two concrete,
                        incompatible, prose-faithful designs and find no prose clause selecting one.
                        A disciplined hypothesis, not proof.
  PROVEN                k blind from-prose attempts scatter (low convergence + split) -- EC2, not here.

The raters see the PROSE ONLY (problem+requirements+interface) -- never the gold or the hidden test, so
"faithful" is judged against the spec, not reverse-engineered from the answer. We then separately note
the gold implements one reading (so the test rewards an unstated choice). NON-LABELS (insufficient on
their own): many files, new API/module, large LOC, feature-shaped, model failure, auditor surprise.

  tools/divergence.py <slug> ...            # rater-assessed pass on given cases
  tools/divergence.py --flagged [--workers 6]   # rater pass over the breadth-flagged tail
  tools/divergence.py --breadth             # (re)write the mechanical breadth flag only, no model
"""
import sys, json, re, subprocess, pathlib, concurrent.futures as cf

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"
OPUS = "claude-opus-4-8"
FLAG_FILES, FLAG_HUNKS = 8, 20   # breadth pre-filter (triage), per the 728 distribution (p~81)

RATER = """You are assessing whether a coding task's PROSE alone DETERMINES the implementation, or leaves
multiple incompatible faithful designs open. You see ONLY the problem + requirements + interface a solver
receives -- NOT any reference solution and NOT the tests. Judge "faithful" against the prose as written.

Answer ONLY this JSON:
{
 "determined": true | false,          // does the prose pin one implementation approach for the graded behavior?
 "design_A": "a concrete faithful implementation choice (or null if determined)",
 "design_B": "a DIFFERENT, incompatible, equally faithful implementation choice (or null)",
 "why_both_faithful": "one sentence: why the prose permits BOTH (or null)",
 "selecting_clause": "verbatim prose clause that would force A over B, or null if none exists"
}
Rules: do NOT call it underdetermined merely because the task is large, feature-shaped, touches many
files, or adds new API/modules -- those are not evidence. It is underdetermined ONLY if you can name two
concrete incompatible implementations that BOTH satisfy every stated requirement, with no clause
selecting one. If the prose does pin it (including large but uniform/mechanical changes), say determined:true.

=== PROBLEM + REQUIREMENTS + INTERFACE (prose only) ===
{spec}
"""


def opus(p, t=600):
    return subprocess.run(["claude", "-p", "--model", OPUS, p], capture_output=True, text=True, timeout=t).stdout


def codex(p, out, t=600):
    subprocess.run(["codex", "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
                    "-c", "model=gpt-5.5", "-o", str(out), p], capture_output=True, text=True, timeout=t)
    return out.read_text() if out.exists() else ""


def jb(raw):
    try:
        return json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return None


def breadth(slug):
    t = (CASES / slug / "gold.diff").read_text(errors="ignore")
    f = len([l for l in t.splitlines() if l.startswith("+++ b/")])
    h = len([l for l in t.splitlines() if l.startswith("@@")])
    loc = len([l for l in t.splitlines() if (l.startswith("+") or l.startswith("-"))
               and not l.startswith(("+++", "---"))])
    return {"files": f, "hunks": h, "loc": loc, "flagged": f >= FLAG_FILES or h >= FLAG_HUNKS}


def rater_assess(slug):
    d = CASES / slug
    spec = (d / "spec.md").read_text() if (d / "spec.md").exists() else ""
    p = RATER.replace("{spec}", spec[:9000])
    try:
        oj = jb(opus(p)); cj = jb(codex(p, AUDIT / "data" / "judge" / f"{slug}.div.codex.txt"))
    except Exception as e:
        return slug, {"error": str(e)[:200]}

    def und(j):  # this rater says underdetermined with concrete A/B and no selecting clause
        return bool(j and j.get("determined") is False and j.get("design_A") and j.get("design_B")
                    and not j.get("selecting_clause"))
    res = {"slug": slug, "breadth": breadth(slug),
           "opus": {"underdetermined": und(oj), "raw": oj},
           "codex": {"underdetermined": und(cj), "raw": cj},
           "rater_assessed_underdetermined": und(oj) and und(cj)}
    (d / "divergence.json").write_text(json.dumps(res, indent=1))
    return slug, res


def main():
    a = sys.argv[1:]
    workers = int(a[a.index("--workers") + 1]) if "--workers" in a else 6
    if "--breadth" in a:
        out = {s.name: breadth(s.name) for s in CASES.iterdir()
               if s.is_dir() and (s / "gold.diff").exists()}
        (AUDIT / "data" / "gold_sweep" / "breadth.json").write_text(json.dumps(out, indent=1))
        flagged = sum(1 for v in out.values() if v["flagged"])
        print(f"breadth: {len(out)} cases, {flagged} flagged (>= {FLAG_FILES} files or {FLAG_HUNKS} hunks)")
        return
    if "--flagged" in a:
        slugs = sorted(s.name for s in CASES.iterdir() if s.is_dir() and (s / "gold.diff").exists()
                       and breadth(s.name)["flagged"] and not (s / "divergence.json").exists())
    else:
        slugs = [x for x in a if not x.startswith("--") and (CASES / x).is_dir()]
    print(f"rater-assessed divergence over {len(slugs)} cases, workers={workers}")
    n_und = 0
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for slug, res in ex.map(rater_assess, slugs):
            if "error" in res:
                print(f"  {slug:26} ERROR {res['error']}"); continue
            u = res["rater_assessed_underdetermined"]; n_und += u
            print(f"  {slug:26} underdetermined={u}  (opus={res['opus']['underdetermined']} "
                  f"codex={res['codex']['underdetermined']}; files={res['breadth']['files']} hunks={res['breadth']['hunks']})")
    print(f"DONE: rater-assessed UNDERDETERMINED {n_und}/{len(slugs)}")


if __name__ == "__main__":
    main()
