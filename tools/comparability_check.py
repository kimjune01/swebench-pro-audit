#!/usr/bin/env python3
"""comparability_check.py -- re-ground codebase-plural on the right standard: an EXISTENCE proof of
COMPARABLE plurality is not-an-opinion. Replaces the opus-convergence demotion (which let a universal
"would a solver converge" opinion override an existence proof -- a category error).

The only thing an existence-of-plurality proof needs is that the exhibited precedents are GENUINELY
comparable: the same semantic decision in comparable live context, not different decisions that merely
look alike (the codex-sniff cherry-pick worry). That is a verifiable existence question, not a convergence
poll. So per codebase-plural case we ask exactly that, with a timeout (codex can hang):

  comparable=true  -> existence proof of comparable plurality stands -> codebase-plural WITNESS (claimed).
  comparable=false -> the precedents are different decisions/contexts -> not real plurality -> dropped to
                      HYPOTHESIS (cherry-pick, not underdetermination).

Reads the verified precedents from codebase_ambiguity.json (path/snippet/way). Restores any case the
opus-demotion sent to AMBIGUITY_HYPOTHESIS.md if it passes comparability.

  tools/comparability_check.py <slug> ...|--all [--workers 6]
"""
import sys, json, re, subprocess, pathlib, concurrent.futures as cf

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"
TIMEOUT = 240


def codex(prompt, out):
    try:
        subprocess.run(["timeout", str(TIMEOUT), "codex", "exec", "--skip-git-repo-check",
                        "--dangerously-bypass-approvals-and-sandbox", "-c", "model=gpt-5.5",
                        "-o", str(out), prompt], capture_output=True, text=True, timeout=TIMEOUT + 30)
        return out.read_text() if out.exists() else ""
    except Exception:
        return ""


PROMPT = """You verify whether cited code precedents constitute GENUINE comparable plurality: the SAME
semantic decision made more than one way in comparable live contexts, versus different decisions that
merely look similar. This is an existence check, not a judgment about which is better.

The discriminating choice: {choice}

Cited precedents (each is real, live, non-test code at the same commit):
{precedents}

Are these the SAME semantic decision (e.g. the same kind of validation / the same status-selection /
the same default), made differently in comparable contexts -- so a developer choosing how to do THIS
decision faces a genuinely plural codebase? Or are they DIFFERENT decisions / different situations that
only resemble each other (e.g. "404 for a missing file" vs "403 for a traversal attempt" are different
situations, not plural conventions for one choice)?

Output ONLY: {"comparable": true|false, "why": "one sentence"}"""


def is_cbp(d):
    for fn in ("AMBIGUITY_WITNESS.md", "AMBIGUITY_HYPOTHESIS.md"):
        p = d / fn
        if p.exists():
            m = re.search(r"class:\s*\*\*([\w-]+)\*\*", p.read_text())
            if m and m.group(1) in ("codebase-plural", "codebase-plural-contested"):
                return fn
    return None


def check(slug):
    d = CASES / slug
    ca = d / "codebase_ambiguity.json"
    if not ca.exists():
        return slug, None, "no codebase_ambiguity.json"
    obj = json.loads(ca.read_text())
    prec = obj.get("verified", [])
    pretext = "\n".join(f"- {p.get('verified_path')}: {p.get('way','')}\n    {(p.get('snippet') or '')[:160]}"
                        for p in prec)
    raw = codex(PROMPT.replace("{choice}", str(obj.get("choice", "")))
                .replace("{precedents}", pretext[:4000]),
                AUDIT / "data" / "judge" / f"{slug}.cmp.txt")
    try:
        j = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return slug, None, "parse fail (kept as-is)"
    comp = bool(j.get("comparable"))
    obj["comparability_verified"] = comp
    obj["comparability_why"] = j.get("why")
    ca.write_text(json.dumps(obj, indent=1))
    # promote/demote based on comparability (the existence-proof standard)
    wf, hf = d / "AMBIGUITY_WITNESS.md", d / "AMBIGUITY_HYPOTHESIS.md"
    if comp:
        # ensure it is a codebase-plural WITNESS
        body = (hf.read_text() if hf.exists() else (wf.read_text() if wf.exists() else ""))
        # strip a prior demotion header if present
        body = re.sub(r"^# Ambiguity HYPOTHESIS.*?\n---\n\n", "", body, flags=re.S)
        body = re.sub(r"class:\s*\*\*codebase-plural-contested\*\*", "class: **codebase-plural**", body)
        if not body.strip().startswith("#"):
            body = f"# Ambiguity witness -- {slug}  (codebase-plurality)\n\n" + body
        wf.write_text(body.rstrip() + "\n\n## Comparability verified\n"
                      f"The cited precedents are the same semantic decision in comparable live context "
                      f"(existence proof of genuine plurality): {j.get('why')}\n")
        if hf.exists():
            hf.unlink()
        return slug, True, j.get("why", "")[:80]
    else:
        note = (f"# Ambiguity HYPOTHESIS (codebase-plural, NOT comparable -- dropped) -- {slug}\n\n"
                "- class: **codebase-plural-contested** (NOT claimed)\n"
                f"- The cited precedents are not genuine comparable plurality (different decisions/contexts): "
                f"{j.get('why')}. An existence proof of plurality requires the SAME decision; this is a "
                "cherry-pick, not underdetermination.\n")
        hf.write_text(note)
        if wf.exists():
            wf.unlink()
        return slug, False, j.get("why", "")[:80]


def main():
    a = sys.argv[1:]
    workers = int(a[a.index("--workers") + 1]) if "--workers" in a else 6
    if "--all" in a:
        slugs = sorted(d.name for d in CASES.iterdir() if d.is_dir() and is_cbp(d))
    else:
        slugs = [x for x in a if not x.startswith("--") and (CASES / x).is_dir()]
    print(f"comparability check over {len(slugs)} codebase-plural cases, workers={workers}")
    comp = noncomp = skip = 0
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for slug, verdict, why in ex.map(check, slugs):
            if verdict is None:
                skip += 1; print(f"  {slug:26} SKIP {why}"); continue
            comp += verdict; noncomp += (not verdict)
            print(f"  {slug:26} comparable={verdict}  {why}")
    print(f"DONE: comparable(codebase-plural PROVEN)={comp}  not-comparable(dropped)={noncomp}  skip={skip}")


if __name__ == "__main__":
    main()
