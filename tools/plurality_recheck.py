#!/usr/bin/env python3
"""plurality_recheck.py -- apply the sharpened plurality rule to the codebase-plural receipts.

What we learned: genuine plurality is ambiguity only if it is also UNSELECTED -- no dominant/ordinary
convention quietly collapses it (the codex-sniff "plurality != binding force"). The original
codebase_ambiguity pass enforced *genuine* (>=2 live, comparable, non-test precedents, prose silent) but
not *unselected*. This recheck adds the unselected test by cross-referencing the convergence rater:

  divergence.json opus, working from prose + ORDINARY convention, answers "would a competent engineer
  converge?" If opus says DETERMINED for a codebase-plural case, an ordinary convention plausibly selects
  among the repo's patterns -> the plurality may be apparent, not binding -> the codebase-plural claim is
  CONTESTED and demoted from PROVEN to a hypothesis tier. If opus also fails to converge, the unselected
  reading is CORROBORATED and the witness stands.

Caveat (recorded in the receipt): opus is prose-only and may itself under-flag by assuming a convention;
so a flag is a contest, not a refutation -- hence demotion to hypothesis, not deletion.

  tools/plurality_recheck.py
"""
import json, re, pathlib

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"


def main():
    corrob = flagged = 0
    for d in sorted(CASES.iterdir()):
        w = d / "AMBIGUITY_WITNESS.md"
        if not w.exists():
            continue
        txt = w.read_text()
        m = re.search(r"class:\s*\*\*([\w-]+)\*\*", txt)
        if not (m and m.group(1) == "codebase-plural"):
            continue
        dj = d / "divergence.json"
        opus_und = False
        if dj.exists():
            try:
                opus_und = json.loads(dj.read_text())["opus"]["underdetermined"]
            except Exception:
                pass
        ca = d / "codebase_ambiguity.json"
        if ca.exists():
            obj = json.loads(ca.read_text())
            obj["convergence_corroborated"] = bool(opus_und)
            ca.write_text(json.dumps(obj, indent=1))
        if opus_und:
            # CORROBORATED: keep the witness, note the cross-check
            corrob += 1
            if "## Unselected cross-check" not in txt:
                w.write_text(txt.rstrip() + "\n\n## Unselected cross-check\n"
                             "Corroborated: the convergence rater (opus, prose + ordinary convention) also "
                             "does not resolve this, so the plurality is unselected, not collapsed by an "
                             "ordinary convention. The witness stands.\n")
        else:
            # CONTESTED: demote PROVEN -> hypothesis (move WITNESS.md -> AMBIGUITY_HYPOTHESIS.md)
            flagged += 1
            note = (
                f"# Ambiguity HYPOTHESIS (codebase-plural, CONTESTED -- demoted) -- {d.name}\n\n"
                "- class: **codebase-plural-contested** (disciplined hypothesis, NOT claimed)\n"
                "- Demoted from PROVEN by the unselected cross-check: the convergence rater (opus, prose + "
                "ordinary convention) judges this DETERMINED, so an ordinary convention may select among "
                "the repo's coexisting patterns -- the plurality could be apparent, not binding. Genuine "
                "plurality was shown (>=2 live comparable precedents, prose silent); *unselected* is now in "
                "doubt, so it is a hypothesis pending a dominance/locality check or raters, not a claim.\n"
                "- (opus is prose-only and may itself under-flag by assuming convention, so this is a "
                "contest, not a refutation.)\n\n"
                "---\n\n" + txt)
            (d / "AMBIGUITY_HYPOTHESIS.md").write_text(note)
            w.unlink()
    print(f"codebase-plural recheck: corroborated(kept PROVEN)={corrob}  contested(demoted->hypothesis)={flagged}")


if __name__ == "__main__":
    main()
