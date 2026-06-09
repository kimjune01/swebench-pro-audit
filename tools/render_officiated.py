#!/usr/bin/env python3
"""render_officiated.py -- author AMBIGUITY_WITNESS.md / AMBIGUITY_HYPOTHESIS.md from officiation.json.

Evidence settles the class (no rater, no adversary):
  DETERMINED-codebase verdict -> AMBIGUITY_HYPOTHESIS.md, class **determined-codebase** (NOT claimed):
                                 prose silent, >=1 grep-verified live precedent, gold matches it.
  defect (MISDETERMINED / AMBIGUOUS) -> AMBIGUITY_WITNESS.md, class by the strongest provable gap:
    misdetermined   -- a MISDETERMINED gap with >=1 verified live precedent + gold deviates (mech spine)
    airtight        -- an AMBIGUOUS gap whose gold constant is verified ABSENT from the codebase (mech spine)
    codebase-plural -- an AMBIGUOUS gap with >=2 distinct verified live precedents (two-expert)
    else            -- no mechanical proof -> AMBIGUITY_HYPOTHESIS.md, class **hypothesis** (not claimed)

Usage: tools/render_officiated.py [--all | <slug> ...]
"""
import sys, json, pathlib

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"


def repo_line(off):
    return f"repo `{off['repo']}` @ `{off['base'][:10]}`"


def precedent_block(precs, n=3):
    out = []
    for i, p in enumerate(precs[:n], 1):
        out += [f"{i}. `{p['path']}` -- {p.get('way','')}", "   ```",
                "   " + (p.get("snippet", "") or "").strip().replace("\n", "\n   ")[:400], "   ```"]
    return out


def pick_witness(gaps):
    """strongest provable defect gap -> (class, gap). evidence order: misdetermined, airtight, plural."""
    misd = [g for g in gaps if g["status"] == "MISDETERMINED" and g["precedents"]]
    if misd:
        return "misdetermined", misd[0]
    air = [g for g in gaps if g["status"] == "AMBIGUOUS" and g.get("airtight_absent") and g.get("gold_value")]
    if air:
        return "airtight", air[0]
    plural = [g for g in gaps if g["status"] == "AMBIGUOUS"
              and len({p["path"] for p in g["precedents"]}) >= 2]
    if plural:
        return "codebase-plural", plural[0]
    return None, None


def render(slug):
    d = CASES / slug
    off_f = d / "officiation.json"
    if not off_f.exists():
        return slug, "no officiation.json"
    off = json.loads(off_f.read_text())
    verdict = off["verdict"]
    iid = (d / "instance_id.txt").read_text().strip()
    wf, hf = d / "AMBIGUITY_WITNESS.md", d / "AMBIGUITY_HYPOTHESIS.md"

    if verdict == "DETERMINED-codebase":
        dgs = [g for g in off["gaps"] if g["status"] == "DETERMINED-codebase"]
        L = [f"# Ambiguity HYPOTHESIS (two-expert: DETERMINED-codebase -- not claimed) -- {slug}", "",
             f"- instance_id: `{iid}`",
             "- class: **determined-codebase** (NOT claimed -- prose silent, one codebase way, gold matches)",
             f"- {repo_line(off)}", "",
             "## Why this is determined, not ambiguous",
             "The prose is silent on these behaviors, but the codebase implements each exactly one live way "
             "and gold matches it; a from-codebase solver lands on gold. Not underdetermined.", ""]
        for g in dgs:
            L += [f"- **{g['behavior']}** -- gold `{g.get('gold_value')}` matches codebase "
                  f"`{g.get('codebase_value')}`. {g.get('why','')}"]
            L += precedent_block(g["precedents"], 1)
        L += ["", "_Guard: each precedent grep'd verbatim at base_commit in a non-test/non-vendor path; "
              "gold's value equals the codebase's one way. Evidence settles it -- no rater._"]
        hf.write_text("\n".join(L) + "\n")
        if wf.exists():
            wf.unlink()
        return slug, "DETERMINED-codebase note"

    # defect: author a witness if mechanically provable
    klass, g = pick_witness(off["gaps"])
    if not klass:
        L = [f"# Ambiguity HYPOTHESIS (raters-pending, NOT claimed) -- {slug}", "",
             f"- instance_id: `{iid}`", "- class: **hypothesis** (disciplined hypothesis)",
             f"- {repo_line(off)}", "",
             "## Defect, but not mechanically proven",
             f"Verdict **{verdict}**: a faithful solver fails, but no single gap yields a grep-clean "
             "witness (airtight-absent / >=1 misdetermined precedent / >=2 plural precedents). "
             "Raters-pending; not claimed.", ""]
        for gg in off["gaps"]:
            if gg["status"] in ("AMBIGUOUS", "MISDETERMINED"):
                L += [f"- ({gg['status']}) {gg['behavior']} -- {gg.get('why','')}"]
        hf.write_text("\n".join(L) + "\n")
        if wf.exists():
            wf.unlink()
        return slug, f"{verdict} hypothesis (unproven)"

    axis = {"misdetermined": "the codebase determines one value; gold/test pin a different one",
            "airtight": "an arbitrary constant absent from prose and codebase",
            "codebase-plural": "the codebase makes this choice >=2 live ways; the test pins one"}[klass]
    L = [f"# Ambiguity witness -- {slug}  ({klass})", "",
         f"- instance_id: `{iid}`",
         f"- class: **{klass}** (PROVEN -- {axis})",
         f"- {repo_line(off)}", "",
         "## The graded behavior",
         f"{g['behavior']}",
         f"- gold value (test-pinned): `{g.get('gold_value')}`"]
    if g.get("codebase_value"):
        L.append(f"- codebase value (the one live way): `{g.get('codebase_value')}`")
    L += ["", f"**Why a faithful solver fails:** {g.get('why','')}", ""]
    if klass == "airtight":
        L += ["## Airtight: the graded constant is absent from prose and codebase",
              f"The value `{g.get('gold_value')}` is a free authorial choice -- it appears only in "
              "gold+test, verified absent from the repository at base_commit (grep). Nothing a from-prose "
              "or from-codebase solver receives selects it."]
    else:
        L += ["## Source evidence (grep-verified live precedents)"]
        L += precedent_block(g["precedents"])
    L += ["", "_Guard: precedents grep'd verbatim at base_commit in non-test/non-vendor paths; airtight "
          "constants verified absent. Evidence settles it -- mechanical, no rater._"]
    wf.write_text("\n".join(L) + "\n")
    if hf.exists():
        hf.unlink()
    return slug, f"{verdict} witness ({klass})"


def main():
    a = sys.argv[1:]
    if "--all" in a:
        slugs = [d.name for d in sorted(CASES.iterdir()) if (d / "officiation.json").exists()]
    else:
        slugs = [x for x in a if not x.startswith("--")]
    for s in slugs:
        print("  ", *render(s))


if __name__ == "__main__":
    main()
