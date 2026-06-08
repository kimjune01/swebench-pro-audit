#!/usr/bin/env python3
"""build_ledgers.py -- regenerate the human-viewable markdown ledgers from per-case data.

GitHub renders markdown tables natively, so the repo is its own viewer (no frontend). Sources:
  - data/judge/<case>.json         (coverage-table results from judge_pool.py / reverify.py)
  - data/cases/gold_fails_grader.defects.jsonl  (the pre-run gold-fails-grader defects)
  - CLASSIFY below                 (which judged cases are KNOWN_AMBIGUOUS vs OUR_CAPABILITY_GAP)

Emits: SUMMARY.md, KNOWN_BAD.md, KNOWN_AMBIGUOUS.md, OUR_CAPABILITY_GAPS.md (repo root).
Re-run after any judge/reverify pass.
"""
import json, pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
JUDGE = REPO / "data" / "judge"

# cases we ran through recon+craft and lost (so an ENTAILED verdict = our capability gap)
OUR_LOSSES = {"qutebrowser", "protonmail", "tutao", "element"}


def classify_of(case, rec):
    """Mechanical: AMBIGUOUS verdict (>=1 GAP) -> KNOWN_AMBIGUOUS; ENTAILED + we-lost -> OUR_GAP."""
    if rec.get("verdict") == "AMBIGUOUS":
        return "AMBIGUOUS"
    if rec.get("verdict") == "ENTAILED" and case in OUR_LOSSES:
        return "OUR_GAP"
    return "—"


def load_judged():
    out = {}
    for f in sorted(JUDGE.glob("*.json")):
        try: out[f.stem] = json.loads(f.read_text())
        except Exception: pass
    return out


def gap_behaviors(rec, n=4):
    g = [r.get("test", "") for r in rec.get("rows", []) if r.get("status") == "GAP"]
    return "; ".join(x[:70] for x in g[:n]) + (" …" if len(g) > n else "")


def main():
    judged = load_judged()
    iid = lambda c: ((REPO / "data" / "cases" / c / "instance_id.txt").read_text().strip()
                     if (REPO / "data" / "cases" / c / "instance_id.txt").exists() else c)

    # SUMMARY.md
    s = ["# SWE-bench Pro audit — summary", "",
         "Public-set audit. Each row links to its coverage-table attribution. "
         "Verdict is mechanical: a blank cell (GAP) is a test behavior with no covering requirement.", "",
         "| case | verdict | coverage | gaps | list | attribution |", "|---|---|---|---|---|---|"]
    for c, r in sorted(judged.items()):
        den = r.get('in_gold_total', r.get('n_rows'))
        s.append(f"| {c} | {r.get('verdict')} | {r.get('n_covered')}/{den} | "
                 f"{r.get('n_gap',0)} | {classify_of(c,r)} | [table](data/attribution/{c}.md) |")
    (REPO / "SUMMARY.md").write_text("\n".join(s) + "\n")

    # KNOWN_BAD.md (from the gold-fails-grader defects)
    kb = ["# KNOWN_BAD — gold fails its own grader", "",
          "Mechanical defects (binary): the reference solution does not pass the official verifier at the "
          "pinned commit. Frozen pre-run, results-independent. Receipt: `data/cases/gold_fails_grader.defects.jsonl`.", "",
          "| instance_id | grader verdict |", "|---|---|"]
    df = REPO / "data" / "cases" / "gold_fails_grader.defects.jsonl"
    if df.exists():
        for line in df.read_text().splitlines():
            if not line.strip(): continue
            d = json.loads(line)
            kb.append(f"| `{d['instance_id']}` | {d.get('detail','')} |")
    (REPO / "KNOWN_BAD.md").write_text("\n".join(kb) + "\n")

    # KNOWN_AMBIGUOUS.md
    ka = ["# KNOWN_AMBIGUOUS — gold passes, prose underdetermines", "",
          "Gold passes its verifier, but the hidden test checks behavior no requirement determines "
          "(a specification lottery). The blank cells in each attribution are the evidence. "
          "Screen = codex coverage table; confirm with the decontaminated panel (see docs/ADMISSIBILITY-SPEC.md).", "",
          "| case | instance_id | coverage | gaps | status | witness | attribution |",
          "|---|---|---|---|---|---|---|"]
    for c, r in sorted(judged.items()):
        if classify_of(c, r) != "AMBIGUOUS": continue
        w = REPO / "data" / "cases" / c / "AMBIGUITY_WITNESS.md"
        status, witness = ("**PROVEN**", f"[witness](data/cases/{c}/AMBIGUITY_WITNESS.md)") if w.exists() else ("screen-flagged", "(pending)")
        ka.append(f"| {c} | `{iid(c)}` | {r['n_covered']}/{r.get('in_gold_total', r.get('n_rows'))} | {r.get('n_gap',0)} | "
                  f"{status} | {witness} | [table](data/attribution/{c}.md) |")
    (REPO / "KNOWN_AMBIGUOUS.md").write_text("\n".join(ka) + "\n")

    # OUR_CAPABILITY_GAPS.md
    og = ["# OUR_CAPABILITY_GAPS — we lost, but the prose determines the behavior", "",
          "recon+craft lost these oracle-free, yet the coverage table shows the substantive behavior is "
          "fully specified (any blank is incidental: test scaffolding or export style). NOT bench defects; "
          "reported as ours. Integrity: the blind judge put these back on us.", "",
          "| case | instance_id | coverage | gaps | attribution |", "|---|---|---|---|---|"]
    for c, r in sorted(judged.items()):
        if classify_of(c, r) != "OUR_GAP": continue
        og.append(f"| {c} | `{iid(c)}` | {r['n_covered']}/{r.get('in_gold_total', r.get('n_rows'))} | {r.get('n_gap',0)} | "
                  f"[table](data/attribution/{c}.md) |")
    (REPO / "OUR_CAPABILITY_GAPS.md").write_text("\n".join(og) + "\n")
    print("wrote SUMMARY.md, KNOWN_BAD.md, KNOWN_AMBIGUOUS.md, OUR_CAPABILITY_GAPS.md")


if __name__ == "__main__":
    main()
