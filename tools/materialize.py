#!/usr/bin/env python3
"""materialize.py -- build all 728 public-set case bundles for the determinacy audit.

Joins the canonical solver-prose (companion repo tasks/pro_repl_fields.json, the 728 public tasks)
with the HF dataset ScaleAI/SWE-bench_Pro (gold patch, hidden test, fail_to_pass) and writes one
bundle per task under data/cases/<slug>/:

  spec.md          # PROBLEM + REQUIREMENTS + INTERFACE (the prose a solver receives)
  gold.diff        # the accepted reference patch
  hidden_test.diff # the grader's test patch
  fail_to_pass.txt # one graded test id per line (ast.literal_eval of the dataset field)
  instance_id.txt  # the full instance_id

slug = <org>_<base_commit[:8]> (verified unique + collision-free across the 728). The four hand-built
worked cases (tutao/element/qutebrowser/protonmail) keep their existing short dirs and are NOT
overwritten (witnesses, our_failed.diff stay intact). Resumable: --batch N --offset M; skips a dir that
already carries all five files.

  tools/materialize.py [--batch 50] [--offset 0]
"""
import sys, os, json, ast, pathlib

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"
# Canonical 728-task solver-prose. Vendored at data/pro_repl_fields.json so the audit repo is
# self-contained; falls back to the companion repo (env SWEBENCH_PRO_REPO or the default path) if the
# vendored copy is absent.
DATASET_REVISION = "7ab5114912baf22bb098818e604c02fe7ad2c11f"  # ScaleAI/SWE-bench_Pro, frozen 2026-02-23
_VENDORED = AUDIT / "data" / "pro_repl_fields.json"
if _VENDORED.exists():
    FIELDS = json.load(open(_VENDORED))
else:
    COMPANION = pathlib.Path(os.environ.get("SWEBENCH_PRO_REPO", "/Users/junekim/Documents/swebench-pro"))
    FIELDS = json.load(open(COMPANION / "tasks" / "pro_repl_fields.json"))

# instance_ids that already have a hand-built short dir (preserve as-is, do not regenerate)
EXISTING = {
    "instance_tutao__tutanota-51818218c6ae33de00cbea3a4d30daac8c34142e-vc4e41fd0029957297843cb9dec4a25c7c756f029": "tutao",
    "instance_element-hq__element-web-ad26925bb6628260cfe0fcf90ec0a8cba381f4a4-vnan": "element",
    "instance_qutebrowser__qutebrowser-e34dfc68647d087ca3175d9ad3f023c30d8c9746-v363c8a7e5ccdf6968fc7ab84a2053ac78036691d": "qutebrowser",
    "instance_protonmail__webclients-e65cc5f33719e02e1c378146fb981d27bc24bdf4": "protonmail",
}
REQ_FILES = ("spec.md", "gold.diff", "hidden_test.diff", "fail_to_pass.txt", "instance_id.txt")


def deq(s):
    """strip one balanced layer of surrounding double-quotes (a source serialization artifact)."""
    s = (s or "").strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1].strip()
    return s


def slug(iid, base):
    org = iid[len("instance_"):].split("__", 1)[0]
    return f"{org}_{base[:8]}"


def f2p_lines(raw):
    try:
        v = ast.literal_eval(raw)
        if isinstance(v, (list, tuple)):
            return "\n".join(str(x) for x in v) + "\n"
    except Exception:
        pass
    return (raw or "").strip() + "\n"


def write_bundle(d, iid, prose, row):
    d.mkdir(parents=True, exist_ok=True)
    short = d.name
    spec = (f"# {short}  ({iid})\n\n"
            f"## PROBLEM\n{deq(prose['problem_statement'])}\n\n"
            f"## REQUIREMENTS\n{deq(prose['requirements'])}\n\n"
            f"## INTERFACE\n{deq(prose['interface'])}\n")
    (d / "spec.md").write_text(spec)
    (d / "gold.diff").write_text(row["patch"] or "")
    (d / "hidden_test.diff").write_text(row["test_patch"] or "")
    (d / "fail_to_pass.txt").write_text(f2p_lines(row["fail_to_pass"]))
    (d / "instance_id.txt").write_text(iid + "\n")


def main():
    a = sys.argv
    batch = int(a[a.index("--batch") + 1]) if "--batch" in a else 100000
    offset = int(a[a.index("--offset") + 1]) if "--offset" in a else 0
    from datasets import load_dataset
    ds = load_dataset("ScaleAI/SWE-bench_Pro", split="test", revision=DATASET_REVISION)
    byid = {r["instance_id"]: r for r in ds}

    ids = list(FIELDS.keys())[offset:offset + batch]
    made = skipped = preserved = 0
    for iid in ids:
        if iid not in byid:
            print(f"  MISSING in HF: {iid}"); continue
        if iid in EXISTING:
            preserved += 1; continue  # hand-built dir, leave intact
        d = CASES / slug(iid, byid[iid]["base_commit"])
        if all((d / f).exists() for f in REQ_FILES):
            skipped += 1; continue
        write_bundle(d, iid, FIELDS[iid], byid[iid])
        made += 1
    print(f"made={made} skipped(complete)={skipped} preserved(hand-built)={preserved} "
          f"range=[{offset},{offset+len(ids)})")


if __name__ == "__main__":
    main()
