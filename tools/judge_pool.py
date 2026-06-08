#!/usr/bin/env python3
"""judge_pool.py -- fan out the determinacy second-reader (codex/gpt-5.5) over task bundles, locally.

Each worker reads ONE case bundle (spec.md + gold.diff + hidden_test.diff) and asks codex whether the
PROSE ALONE determines the behavior the hidden test checks. Read-only, no container, no grading -- so it
parallelizes freely. This is the cheap KNOWN_AMBIGUOUS screen; the full from-prose panel (decontaminated,
multi-family, with grading) confirms. Codex is contaminated (caveat written into the prompt + recorded).

  tools/judge_pool.py <case_dir> [<case_dir> ...] [--workers 12]

Writes data/judge/<case>.json per task; prints a tally.
"""
import sys, json, subprocess, pathlib, concurrent.futures as cf

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "judge"; OUT.mkdir(parents=True, exist_ok=True)
ATTR = REPO / "data" / "attribution"; ATTR.mkdir(parents=True, exist_ok=True)
# default batch: the cases our recon+craft failed (the loss set)
DEFAULT = ["qutebrowser", "protonmail", "tutao", "element"]


def write_attribution(d, rec):
    """One attribution file per AMBIGUOUS case, in data/attribution/. Skip entailed (not ambiguous)."""
    if rec.get("verdict") == "entailed" or not rec.get("ok"):
        return None
    short = rec["case"]; iid = (d / "instance_id.txt").read_text().strip() if (d / "instance_id.txt").exists() else short
    recpts = [f"- {n}: `data/cases/{short}/{n}`" for n in ("spec.md", "gold.diff", "hidden_test.diff", "our_failed.diff") if (d / n).exists()]
    md = (f"# Ambiguity attribution: {short}\n\n"
          f"- instance_id: `{iid}`\n- verdict: **{rec.get('verdict')}**  (prose_determines_graded_behavior="
          f"{rec.get('prose_determines_graded_behavior')}, confidence={rec.get('confidence')})\n"
          f"- judge: codex/gpt-5.5 (contaminated; instructed to reason from prose only, recognized="
          f"{rec.get('recognized')})\n\n"
          f"## The unstated behavior the hidden test pins\n{rec.get('splitting_assertion') or '(none cited)'}\n\n"
          f"## A defensible reading the prose allows but the test rejects\n{rec.get('alternative_reading') or '(none cited)'}\n\n"
          f"## Justification\n{rec.get('justification') or rec.get('one_line') or ''}\n\n"
          f"## Receipts\n" + "\n".join(recpts) + f"\n- judge JSON: `data/judge/{short}.json`\n")
    (ATTR / f"{short}.md").write_text(md)
    return str(ATTR / f"{short}.md")

PROMPT = """You are a benchmark DETERMINACY auditor. You are given a coding task's PROBLEM statement
(the prose a solver receives), its GOLD patch (the maintainer's accepted solution), and the HIDDEN TEST
that grades solutions. Decide ONE thing: does the PROBLEM PROSE ALONE determine the behavior the HIDDEN
TEST checks -- such that a competent engineer reading only the prose (and the codebase) would produce a
solution the test accepts?

Reason ONLY from prose -> behavior. Do NOT use anything you may recall about this repository; if you
recognize it, set "recognized": true and judge as if you did not. The failure you are hunting for: the
hidden test pins a specific behavior (an exception type, an ordering, a when-to-call decision, one of
several defensible readings) that the prose never states -- a "specification lottery."

Output your FINAL message as ONLY a JSON object, no prose around it:
{"verdict": "entailed|underdetermined|contradicted",
 "prose_determines_graded_behavior": true/false,
 "splitting_assertion": "the test assertion that checks an unstated behavior, or empty",
 "alternative_reading": "a defensible solution the prose allows but the test would reject, or empty",
 "justification": "2-4 sentences: cite the exact prose gap and the exact test behavior it fails to pin",
 "recognized": true/false,
 "confidence": 0.0,
 "one_line": "one sentence"}

=== PROBLEM (prose) ===
{spec}

=== GOLD PATCH (accepted solution) ===
{gold}

=== HIDDEN TEST (grader) ===
{test}
"""


def judge(case_dir):
    d = pathlib.Path(case_dir)
    short = d.name
    spec = (d / "spec.md").read_text()[:8000] if (d / "spec.md").exists() else ""
    gold = (d / "gold.diff").read_text()[:12000] if (d / "gold.diff").exists() else ""
    test = (d / "hidden_test.diff").read_text()[:10000] if (d / "hidden_test.diff").exists() else ""
    prompt = PROMPT.replace("{spec}", spec).replace("{gold}", gold).replace("{test}", test)
    last = OUT / f"{short}.last.txt"
    cmd = ["codex", "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
           "-c", "model=gpt-5.5", "-o", str(last), prompt]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        raw = last.read_text() if last.exists() else ""
    except Exception as e:
        raw = f"__ERROR__ {e}"
    # extract the JSON object from the last message
    obj = None
    if "{" in raw and "}" in raw:
        frag = raw[raw.index("{"): raw.rindex("}") + 1]
        try: obj = json.loads(frag)
        except Exception: obj = None
    rec = {"case": short, "ok": obj is not None, **(obj or {"raw_tail": raw[-300:]})}
    (OUT / f"{short}.json").write_text(json.dumps(rec, indent=1))
    rec["attribution"] = write_attribution(d, rec)
    return rec


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    workers = 12
    if "--workers" in sys.argv: workers = int(sys.argv[sys.argv.index("--workers") + 1])
    cases = args or [str(REPO / "data" / "cases" / c) for c in DEFAULT]
    print(f"judging {len(cases)} cases, {workers} workers")
    results = []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for r in ex.map(judge, cases):
            results.append(r)
            v = r.get("verdict", "ERR")
            print(f"  {r['case']:24s} {v:15s} det={r.get('prose_determines_graded_behavior')} conf={r.get('confidence')}")
    tally = {}
    for r in results: tally[r.get("verdict", "ERR")] = tally.get(r.get("verdict", "ERR"), 0) + 1
    print("TALLY:", tally)


if __name__ == "__main__":
    main()
