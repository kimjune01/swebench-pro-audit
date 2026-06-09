#!/usr/bin/env python3
"""officiate_cases.py -- apply the determinacy taxonomy to specific cases' judge JSON.

Row status for a prose-silent graded behavior (the rule):
  DETERMINED-codebase  -- the codebase does it exactly ONE way and gold MATCHES it. Not a defect.
  MISDETERMINED        -- the codebase does it exactly ONE way and gold pins a DIFFERENT value.
                          A codebase-faithful solver produces the determined answer and fails. Defect.
  AMBIGUOUS            -- the codebase does it >=2 ways (or prose licenses >=2). Specification lottery. Defect.
  COVERED / OUT_OF_SCOPE -- unchanged.

Case verdict precedence: AMBIGUOUS > MISDETERMINED > DETERMINED-codebase > ENTAILED.
Counts: n_gap = AMBIGUOUS rows; n_misdetermined; n_determined_codebase; n_covered unchanged.

Usage: tools/officiate_cases.py   (edits the 3 officiated cases in place)
"""
import json, pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
JUDGE = REPO / "data" / "judge"

# slug -> {substring of test behavior : new status}. Default for unmatched GAP rows is given per-case.
PLAN = {
    "element-hq_04bc8fb7": {  # all 5 attribute GAPs determined by reuse of the pre-existing SeekBar
        "_default_gap": "DETERMINED-codebase",
        "rows": {},
    },
    "ansible_07e7b69c": {
        "_default_gap": None,  # force explicit
        "rows": {
            "run_commands` is called exactly 10 times": "DETERMINED-codebase",   # retries=10 convention (24 modules)
            "only non-config commands are supported when using check mode": "MISDETERMINED",  # gold deviates from 17-module "show" convention
        },
    },
    "element-hq_f97cef80": {  # init=0 deviates from base's init=1 convention; all 5 sequence GAPs
        "_default_gap": "MISDETERMINED",
        "rows": {},
    },
}

VERDICT_ORDER = ["AMBIGUOUS", "MISDETERMINED", "DETERMINED-codebase", "ENTAILED"]


def reclassify(slug, plan):
    f = JUDGE / f"{slug}.json"
    d = json.loads(f.read_text())
    for r in d["rows"]:
        if r.get("status") != "GAP":
            continue
        new = None
        for sub, st in plan["rows"].items():
            if sub in r["test"]:
                new = st
                break
        if new is None:
            new = plan["_default_gap"]
        if new is None:
            raise SystemExit(f"{slug}: unmatched GAP row, no default: {r['test'][:70]}")
        r["status"] = new
    # recount
    from collections import Counter
    c = Counter(r["status"] for r in d["rows"])
    d["n_covered"] = c.get("COVERED", 0)
    d["n_gap"] = c.get("AMBIGUOUS", 0)            # n_gap now = genuinely-ambiguous count
    d["n_misdetermined"] = c.get("MISDETERMINED", 0)
    d["n_determined_codebase"] = c.get("DETERMINED-codebase", 0)
    d["n_out_of_scope"] = c.get("OUT_OF_SCOPE", 0)
    # verdict precedence
    if c.get("AMBIGUOUS"):
        v = "AMBIGUOUS"
    elif c.get("MISDETERMINED"):
        v = "MISDETERMINED"
    elif c.get("DETERMINED-codebase"):
        v = "DETERMINED-codebase"
    else:
        v = "ENTAILED"
    d["verdict"] = v
    f.write_text(json.dumps(d, indent=1))
    return slug, v, dict(c)


if __name__ == "__main__":
    for slug, plan in PLAN.items():
        print(reclassify(slug, plan))
