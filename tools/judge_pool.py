#!/usr/bin/env python3
"""judge_pool.py -- coverage-table determinacy auditor, fanned out over codex locally.

Per case, codex builds a COVERAGE TABLE: every behavior the hidden test checks (left), mapped to the
VERBATIM requirement/prose clause that determines it (right), or null. We then VERIFY each cited clause
is a real substring of the prose (codex cannot fake coverage). The uncovered rows ARE the attribution.
No probabilities: a case is AMBIGUOUS iff >=1 test behavior has no covering prose (a GAP).

  tools/judge_pool.py [<case_dir> ...] [--workers 12]
Writes data/attribution/<case>.md (the table) + data/judge/<case>.json. Default: the recon+craft losses.
"""
import sys, json, re, subprocess, pathlib, concurrent.futures as cf

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "judge"; OUT.mkdir(parents=True, exist_ok=True)
ATTR = REPO / "data" / "attribution"; ATTR.mkdir(parents=True, exist_ok=True)
DEFAULT = ["qutebrowser", "protonmail", "tutao", "element"]

PROMPT = """You are a benchmark determinacy auditor. Build a COVERAGE TABLE mapping what the HIDDEN TEST
checks to the prose that determines it.

You are given a task's PROBLEM + REQUIREMENTS + INTERFACE (the prose a solver receives), the HIDDEN TEST
that grades solutions, and the FAIL_TO_PASS list. For EACH distinct behavior the hidden test asserts
(one row per behavior -- a specific value, timing, ordering, exception, shape, or when-to-act decision),
output the VERBATIM clause from the prose that determines it, copied EXACTLY so it can be found in the
text, or null if no prose determines it.

Rules:
- covering_prose MUST be an exact quote from the provided PROBLEM/REQUIREMENTS/INTERFACE. It will be
  checked against the text; paraphrase or invention will be rejected.
- A behavior is covered only if a competent engineer could derive it from the quoted prose ALONE.
- Do NOT use anything you recall about this repository. Judge from the prose only.
- Enumerate the behaviors the test actually checks, including specific constants (delays, counts),
  exception types, and decision points.

Output your FINAL message as ONLY this JSON, nothing else:
{"rows": [{"test": "<the behavior the test asserts, concrete>", "covering_prose": "<verbatim prose clause>" | null}, ...]}

=== PROBLEM + REQUIREMENTS + INTERFACE (prose) ===
{spec}

=== FAIL_TO_PASS ===
{f2p}

=== HIDDEN TEST (grader) ===
{test}
"""


def norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def judge(case_dir):
    d = pathlib.Path(case_dir); short = d.name
    spec = (d / "spec.md").read_text() if (d / "spec.md").exists() else ""
    test = (d / "hidden_test.diff").read_text()[:12000] if (d / "hidden_test.diff").exists() else ""
    f2p = (d / "fail_to_pass.txt").read_text()[:2000] if (d / "fail_to_pass.txt").exists() else ""
    prompt = (PROMPT.replace("{spec}", spec[:9000]).replace("{f2p}", f2p).replace("{test}", test))
    last = OUT / f"{short}.last.txt"
    cmd = ["codex", "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
           "-c", "model=gpt-5.5", "-o", str(last), prompt]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        raw = last.read_text() if last.exists() else ""
    except Exception as e:
        raw = f"__ERROR__ {e}"
    rows, ok = [], False
    if "{" in raw and "}" in raw:
        try:
            obj = json.loads(raw[raw.index("{"): raw.rindex("}") + 1]); rows = obj.get("rows", []); ok = True
        except Exception:
            ok = False
    nspec = norm(spec)
    # verify each citation is a real substring of the prose
    for r in rows:
        cp = r.get("covering_prose")
        if not cp:
            r["status"] = "GAP"
        elif norm(cp) in nspec:
            r["status"] = "COVERED"
        else:
            r["status"] = "UNVERIFIED"   # cited prose not found verbatim -> not trusted as coverage
    # binary: a cell is filled only if the citation verifies; null or unverified -> blank (uncovered)
    n_cov = sum(r["status"] == "COVERED" for r in rows)
    n_blank = len(rows) - n_cov
    verdict = "ERROR" if not ok else ("ENTAILED" if n_blank == 0 else "AMBIGUOUS")
    rec = {"case": short, "ok": ok, "verdict": verdict, "n_rows": len(rows),
           "n_covered": n_cov, "n_blank": n_blank, "rows": rows}
    (OUT / f"{short}.json").write_text(json.dumps(rec, indent=1))
    write_table(d, rec)
    return rec


def write_table(d, rec):
    short = rec["case"]
    iid = (d / "instance_id.txt").read_text().strip() if (d / "instance_id.txt").exists() else short
    lines = [f"# Coverage attribution: {short}", "",
             f"- instance_id: `{iid}`",
             f"- verdict: **{rec['verdict']}**  ({rec['n_covered']}/{rec['n_rows']} covered; "
             f"{rec['n_blank']} blank = the gap)",
             f"- judge: codex/gpt-5.5; a cell is filled only if the quote verifies verbatim in the prose", "",
             "| test behavior | covering requirement |",
             "|---|---|"]
    for r in rec["rows"]:
        t = (r.get("test") or "").replace("|", "\\|")[:160]
        cp = (r.get("covering_prose") or "").replace("|", "\\|")[:300] if r["status"] == "COVERED" else ""
        lines.append(f"| {t} | {cp} |")
    recpts = [f"- `data/cases/{short}/{n}`" for n in ("spec.md", "gold.diff", "hidden_test.diff", "our_failed.diff") if (d / n).exists()]
    lines += ["", "## Receipts", *recpts, f"- judge JSON: `data/judge/{short}.json`"]
    (ATTR / f"{short}.md").write_text("\n".join(lines) + "\n")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 12
    cases = args or [str(REPO / "data" / "cases" / c) for c in DEFAULT]
    print(f"coverage-judging {len(cases)} cases, {workers} workers")
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for r in ex.map(judge, cases):
            print(f"  {r['case']:24s} {r['verdict']:10s} covered={r['n_covered']}/{r['n_rows']} blank={r['n_blank']}")


if __name__ == "__main__":
    main()
