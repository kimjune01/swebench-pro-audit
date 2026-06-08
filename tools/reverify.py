#!/usr/bin/env python3
"""reverify.py -- re-score saved coverage tables with a robust citation matcher (no codex calls).

The first pass used a whitespace-only normalized substring check, which produced FALSE blanks when
codex quoted with backticks/arrows/line-wraps. This re-verifies each saved covering_prose against the
prose with aggressive normalization + a token-coverage fallback, then recomputes the verdict.

Trustworthy gap signal = GAP (codex returned null: no prose at all). A citation that still cannot be
matched after robust normalization is marked CHECK (needs a human glance), NOT auto-counted as a gap.
Verdict: AMBIGUOUS iff >=1 GAP.

  tools/reverify.py [<case> ...]
"""
import sys, json, re, pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
JUDGE = REPO / "data" / "judge"; ATTR = REPO / "data" / "attribution"
DEFAULT = ["qutebrowser", "protonmail", "tutao", "element"]


def aggr(s):
    return re.sub(r"[^a-z0-9 ]+", " ", re.sub(r"\s+", " ", (s or "").lower())).replace("  ", " ").strip()


def toks(s):
    return [w for w in aggr(s).split() if len(w) > 3]


def covered(quote, nspec, spec_tok):
    a = " ".join(aggr(quote).split())
    if not a:
        return False
    if a in nspec:
        return True
    # token-coverage fallback: most content words of the quote appear in the prose
    qt = [w for w in a.split() if len(w) > 3]
    if not qt:
        return False
    hit = sum(1 for w in qt if w in spec_tok)
    return hit / len(qt) >= 0.85


def reverify(case):
    jf = JUDGE / f"{case}.json"
    if not jf.exists():
        print(f"{case}: no judge json"); return
    rec = json.loads(jf.read_text())
    spec = (REPO / "data" / "cases" / case / "spec.md").read_text()
    nspec = " ".join(aggr(spec).split()); spec_tok = set(toks(spec))
    for r in rec["rows"]:
        cp = r.get("covering_prose")
        if not cp:
            r["status"] = "GAP"
        elif covered(cp, nspec, spec_tok):
            r["status"] = "COVERED"
        else:
            r["status"] = "CHECK"
    gap = sum(r["status"] == "GAP" for r in rec["rows"])
    chk = sum(r["status"] == "CHECK" for r in rec["rows"])
    cov = sum(r["status"] == "COVERED" for r in rec["rows"])
    rec["n_covered"], rec["n_gap"], rec["n_check"] = cov, gap, chk
    rec["n_blank"] = gap  # only true gaps are blanks now
    rec["verdict"] = "AMBIGUOUS" if gap else ("CHECK" if chk else "ENTAILED")
    jf.write_text(json.dumps(rec, indent=1))
    write_table(case, rec)
    print(f"  {case:24s} {rec['verdict']:10s} covered={cov}/{len(rec['rows'])} GAP={gap} check={chk}")


def write_table(case, rec):
    d = REPO / "data" / "cases" / case
    iid = (d / "instance_id.txt").read_text().strip() if (d / "instance_id.txt").exists() else case
    L = [f"# Coverage attribution: {case}", "",
         f"- instance_id: `{iid}`",
         f"- verdict: **{rec['verdict']}**  ({rec['n_covered']}/{len(rec['rows'])} covered; "
         f"{rec['n_gap']} GAP = uncovered; {rec.get('n_check',0)} CHECK = citation needs human glance)",
         "- judge: codex/gpt-5.5; cell filled only if its quote matches the prose (robust). GAP = codex found no prose.", "",
         "| test behavior | covering requirement |", "|---|---|"]
    for r in rec["rows"]:
        t = (r.get("test") or "").replace("|", "\\|")[:160]
        cell = (r.get("covering_prose") or "").replace("|", "\\|")[:300] if r["status"] == "COVERED" else (
            "" if r["status"] == "GAP" else "_(cited, unverified — check)_")
        L.append(f"| {t} | {cell} |")
    recpts = [f"- `data/cases/{case}/{n}`" for n in ("spec.md", "gold.diff", "hidden_test.diff", "our_failed.diff") if (d / n).exists()]
    L += ["", "## Receipts", *recpts, f"- judge JSON: `data/judge/{case}.json`"]
    (ATTR / f"{case}.md").write_text("\n".join(L) + "\n")


def main():
    cases = [a for a in sys.argv[1:] if not a.startswith("--")] or DEFAULT
    print(f"reverifying {len(cases)} cases (no codex)")
    for c in cases: reverify(c)


if __name__ == "__main__":
    main()
