#!/usr/bin/env python3
"""judge_pool.py -- coverage-table determinacy auditor (the "mindreading" detector), fanned out over codex.

Per case, codex builds a COVERAGE TABLE over the behaviors the HIDDEN TEST checks. For each behavior it
returns the VERBATIM prose clause that determines it (or null) AND a VERBATIM snippet from the GOLD PATCH
that implements it (or null). Python verifies both citations against the actual text, then:

  GAP (blank)  = tested AND in-gold (anchor verifies) AND NOT specified (no verifying prose)
                 -> "mindreading": the gold has it, the test checks it, the prose never said it.
  COVERED      = tested AND in-gold AND specified.
  OUT_OF_SCOPE = not in-gold (or the gold anchor doesn't verify) -> pre-existing scaffolding, dropped.

Verdict: AMBIGUOUS iff >=1 GAP, else ENTAILED. Both columns are pointers a skeptic can check: the prose
column quotes the requirement, the gold column quotes the gold patch. No probabilities.

  tools/judge_pool.py [<case_dir> ...] [--workers 12]
"""
import sys, json, re, subprocess, pathlib, concurrent.futures as cf

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "judge"; OUT.mkdir(parents=True, exist_ok=True)
ATTR = REPO / "data" / "attribution"; ATTR.mkdir(parents=True, exist_ok=True)
DEFAULT = ["qutebrowser", "protonmail", "tutao", "element"]

PROMPT = """You are a benchmark determinacy auditor detecting "mindreading": behaviors a solver could only
produce by guessing the author's unstated intent. You are given the task's PROBLEM + REQUIREMENTS +
INTERFACE (the prose a solver receives), the GOLD PATCH (accepted solution), the HIDDEN TEST, and the
FAIL_TO_PASS list.

For EACH distinct behavior the hidden test asserts (a specific value, timing, ordering, exception, shape,
or when-to-act decision), output:
- "test": the behavior, concrete.
- "covering_prose": the VERBATIM clause from PROBLEM/REQUIREMENTS/INTERFACE that determines it, copied
  EXACTLY; or null if no prose determines it.
- "gold_anchor": a short VERBATIM snippet from the GOLD PATCH (a changed line or identifier) that
  implements this behavior, copied EXACTLY; or null if the gold does not implement it (pre-existing
  behavior or test scaffolding).

Both citations are checked against the actual text; invention is rejected. A behavior is determined only
if derivable from the quoted prose ALONE. Do NOT use anything you recall about this repo. Enumerate
specific constants (delays, counts), exception types, and decision points.

Output your FINAL message as ONLY this JSON, nothing else:
{"rows": [{"test": "...", "covering_prose": "..."|null, "gold_anchor": "..."|null}, ...]}

=== PROBLEM + REQUIREMENTS + INTERFACE (prose) ===
{spec}

=== GOLD PATCH (accepted solution) ===
{gold}

=== FAIL_TO_PASS ===
{f2p}

=== HIDDEN TEST (grader) ===
{test}
"""


def aggr(s):
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).split())


def cited(quote, ntext, tok):
    a = aggr(quote)
    if not a:
        return False
    if a in ntext:
        return True
    qt = [w for w in a.split() if len(w) > 3]
    return bool(qt) and sum(w in tok for w in qt) / len(qt) >= 0.85


def classify(rows, spec, gold):
    nspec, ngold = aggr(spec), aggr(gold)
    st, gt = set(w for w in nspec.split() if len(w) > 3), set(w for w in ngold.split() if len(w) > 3)
    for r in rows:
        in_gold = bool(r.get("gold_anchor")) and cited(r["gold_anchor"], ngold, gt)
        in_prose = bool(r.get("covering_prose")) and cited(r["covering_prose"], nspec, st)
        r["in_gold"] = in_gold
        r["status"] = "OUT_OF_SCOPE" if not in_gold else ("COVERED" if in_prose else "GAP")
    return rows


def judge(case_dir):
    d = pathlib.Path(case_dir); short = d.name
    spec = (d / "spec.md").read_text() if (d / "spec.md").exists() else ""
    gold = (d / "gold.diff").read_text() if (d / "gold.diff").exists() else ""
    test = (d / "hidden_test.diff").read_text()[:12000] if (d / "hidden_test.diff").exists() else ""
    f2p = (d / "fail_to_pass.txt").read_text()[:2000] if (d / "fail_to_pass.txt").exists() else ""
    prompt = (PROMPT.replace("{spec}", spec[:9000]).replace("{gold}", gold[:14000])
              .replace("{f2p}", f2p).replace("{test}", test))
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
            rows = json.loads(raw[raw.index("{"): raw.rindex("}") + 1]).get("rows", []); ok = True
        except Exception:
            ok = False
    classify(rows, spec, gold)
    gap = sum(r["status"] == "GAP" for r in rows); cov = sum(r["status"] == "COVERED" for r in rows)
    oos = sum(r["status"] == "OUT_OF_SCOPE" for r in rows)
    rec = {"case": short, "ok": ok, "verdict": "ERROR" if not ok else ("AMBIGUOUS" if gap else "ENTAILED"),
           "in_gold_total": cov + gap, "n_covered": cov, "n_gap": gap, "n_out_of_scope": oos, "rows": rows}
    (OUT / f"{short}.json").write_text(json.dumps(rec, indent=1))
    write_table(d, rec)
    return rec


def write_table(d, rec):
    short = rec["case"]
    iid = (d / "instance_id.txt").read_text().strip() if (d / "instance_id.txt").exists() else short
    L = [f"# Coverage attribution: {short}", "",
         f"- instance_id: `{iid}`",
         f"- verdict: **{rec['verdict']}**  ({rec['n_covered']}/{rec['in_gold_total']} in-gold behaviors "
         f"covered; **{rec['n_gap']} GAP** = mindreading; {rec['n_out_of_scope']} out-of-scope)",
         "- gold patch: [`gold.diff`](../cases/" + short + "/gold.diff)  ·  hidden test: "
         "[`hidden_test.diff`](../cases/" + short + "/hidden_test.diff)  ·  spec: "
         "[`spec.md`](../cases/" + short + "/spec.md)",
         "- A **GAP** is a behavior the gold implements (right column) and the test checks, but no "
         "requirement states (blank middle): a solver could only get it by mindreading the author.", "",
         "| test behavior | covering requirement (prose) | implemented in gold (anchor) |", "|---|---|---|"]
    order = {"GAP": 0, "COVERED": 1, "OUT_OF_SCOPE": 2}
    for r in sorted(rec["rows"], key=lambda r: order.get(r["status"], 3)):
        t = (r.get("test") or "").replace("|", "\\|")[:140]
        prose = (r.get("covering_prose") or "").replace("|", "\\|")[:240] if r["status"] == "COVERED" else ""
        if r["status"] == "OUT_OF_SCOPE":
            anchor = "_(not in gold)_"
        else:
            anchor = "`" + (r.get("gold_anchor") or "").replace("|", "\\|")[:120] + "`"
        L.append(f"| {t} | {prose} | {anchor} |")
    recpts = [f"- `data/cases/{short}/{n}`" for n in ("spec.md", "gold.diff", "hidden_test.diff", "our_failed.diff") if (d / n).exists()]
    L += ["", "## Receipts", *recpts, f"- judge JSON: `data/judge/{short}.json`"]
    (ATTR / f"{short}.md").write_text("\n".join(L) + "\n")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 12
    cases = args or [str(REPO / "data" / "cases" / c) for c in DEFAULT]
    print(f"coverage-judging {len(cases)} cases, {workers} workers (GAP = tested + in-gold + unspecified = mindreading)")
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for r in ex.map(judge, cases):
            print(f"  {r['case']:24s} {r['verdict']:10s} covered={r['n_covered']}/{r['in_gold_total']} "
                  f"GAP={r['n_gap']} oos={r['n_out_of_scope']}")


if __name__ == "__main__":
    main()
