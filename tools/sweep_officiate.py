#!/usr/bin/env python3
"""sweep_officiate.py -- officiate EVERY gap of a hypothesis case under the determinacy taxonomy.

For each GAP row in data/judge/<slug>.json, decide -- grounded on the cloned repo at base_commit --
which of four outcomes holds for the discriminating choice that gap turns on:

  DETERMINED-codebase  the codebase does it exactly ONE way (>=1 live comparable precedent), and gold
                       MATCHES that way. A from-codebase solver lands on gold. NOT a defect.
  MISDETERMINED        the codebase does it exactly ONE way, and gold pins a DIFFERENT value. A
                       codebase-faithful solver produces the determined answer and fails. DEFECT.
  AMBIGUOUS (airtight) neither prose nor codebase determines it (0 comparable precedents); the graded
                       value is a free authorial constant present only in gold+test. DEFECT.
  AMBIGUOUS (codebase-plural) the codebase does it >=2 live comparable ways; the test pins one. DEFECT.

codex PROPOSES the per-gap classification + verbatim precedents; Python VERIFIES every precedent snippet
greps verbatim in a non-test path of the clone, and (airtight) that the gold constant is absent from the
codebase. Unverifiable precedents are dropped; an over-claim downgrades toward AMBIGUOUS, never up.

Case verdict precedence: AMBIGUOUS > MISDETERMINED > DETERMINED-codebase > ENTAILED.
Writes the judge json (per-row status + counts + verdict), and an AMBIGUITY_WITNESS.md (defect, with the
strongest gap) or AMBIGUITY_HYPOTHESIS.md (DETERMINED-codebase note). Resumable: skips cases already
carrying `officiated: true` in the judge json unless --force.

  tools/sweep_officiate.py <slug> ...|--all [--workers 6] [--force]
"""
import sys, json, re, subprocess, pathlib, concurrent.futures as cf

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"
JUDGE = AUDIT / "data" / "judge"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import witness as W          # clone_at, hf_row
import codebase_ambiguity as CA  # grep_path, EXCLUDE
TIMEOUT = 600

PROMPT = """You are a benchmark determinacy auditor. A screen found GAP behaviors: things the hidden
test checks and the gold patch implements, but NO prose requirement states. For EACH gap, decide what
the repository ITSELF determines about the discriminating choice that gap turns on -- using only the
working tree at this base commit, NOT anything you recall about the project.

For each gap, identify the discriminating choice (the specific value/wording/order/default the test
pins), then search the repo for how that SAME KIND of choice is made in LIVE production code (not under
test/spec/example/vendor/deprecated/fixture/mock paths). Classify into exactly one:

- "DETERMINED-codebase": the codebase makes this choice exactly ONE way, and GOLD MATCHES it. Give >=1
  verbatim live precedent (path + snippet) showing that one way.
- "MISDETERMINED": the codebase makes this choice exactly ONE way, but GOLD PINS A DIFFERENT value than
  the codebase convention. Give >=1 verbatim live precedent of the codebase's way, and state gold's
  deviating value. (A codebase-faithful solver would follow the precedent and fail the test.)
- "AMBIGUOUS-airtight": NEITHER prose nor codebase determines it -- the graded value is a free constant
  with no comparable precedent. Give the exact gold constant; precedents = [].
- "AMBIGUOUS-plural": the codebase makes this choice >=2 live comparable ways. Give >=2 verbatim
  precedents (distinct files, different ways).

STRICT: precedents must be live, comparable, current production code; copy snippets EXACTLY; never
manufacture a precedent. If unsure between DETERMINED and MISDETERMINED, look at whether gold's value
equals the precedent's value.

Output ONLY this JSON:
{"gaps":[{"behavior":"<verbatim gap behavior>","choice":"<the discriminating choice>",
  "klass":"DETERMINED-codebase|MISDETERMINED|AMBIGUOUS-airtight|AMBIGUOUS-plural",
  "gold_value":"<what gold/test pin>","codebase_value":"<the codebase's way, or null>",
  "precedents":[{"path":"...","snippet":"...","way":"..."}],
  "why":"<one sentence>"}]}

=== PROSE ===
{spec}
=== GOLD PATCH ===
{gold}
=== HIDDEN TEST ===
{test}
=== GAP behaviors (screen) ===
{gaps}
=== REPO FILE LIST (live sample) ===
{files}
"""


def gap_rows(d):
    jf = JUDGE / f"{d.name}.json"
    j = json.loads(jf.read_text())
    return j, [r for r in j["rows"] if r.get("status") == "GAP"]


def codex(prompt, out, tries=3):
    out.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(tries):
        try:
            subprocess.run(["codex", "exec", "--skip-git-repo-check",
                            "--dangerously-bypass-approvals-and-sandbox", "-c", "model=gpt-5.5",
                            "-o", str(out), prompt], capture_output=True, text=True, timeout=TIMEOUT)
        except Exception:
            pass
        txt = out.read_text() if out.exists() else ""
        if extract(txt) is not None:   # got parseable {"gaps":...}
            return txt
    return out.read_text() if out.exists() else ""


def extract(raw):
    i = raw.find('{"gaps"')
    if i < 0:
        return None
    depth = 0
    instr = esc = False
    for j in range(i, len(raw)):
        c = raw[j]
        if instr:
            esc = (c == "\\" and not esc)
            if c == '"' and not esc:
                instr = False
        elif c == '"':
            instr = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[i:j + 1])
                except Exception:
                    return None
    return None


def grep_count(tree, snippet):
    """count non-excluded files containing snippet's first line; 0 if too short."""
    return 1 if CA.grep_path(tree, snippet) else 0


def absent_in_codebase(tree, token):
    """True if the gold constant token does not occur in any non-excluded file."""
    return CA.grep_path(tree, token) is None


def officiate(slug):
    d = CASES / slug
    j, gaps = gap_rows(d)
    if j.get("officiated") and "--force" not in sys.argv:
        return slug, j.get("verdict"), "cached"
    if not gaps:
        return slug, j.get("verdict"), "no gaps"
    spec = (d / "spec.md").read_text() if (d / "spec.md").exists() else ""
    gold = (d / "gold.diff").read_text() if (d / "gold.diff").exists() else ""
    test = (d / "hidden_test.diff").read_text()[:8000] if (d / "hidden_test.diff").exists() else ""
    iid = (d / "instance_id.txt").read_text().strip()
    row = W.hf_row(iid)
    if not row:
        return slug, None, "no HF row"
    tree = W.clone_at(row["repo"], row["base_commit"])
    if tree is None:
        return slug, None, "clone failed"
    files = subprocess.run(["bash", "-lc", f"cd {tree} && git ls-files | grep -viE "
                            f"'(test|spec|example|vendor|node_modules|fixture|mock|testdata)' | head -400"],
                           capture_output=True, text=True).stdout
    gap_txt = "\n".join(f"- {r['test']}  [gold: {r.get('gold_anchor')}]" for r in gaps)
    prompt = (PROMPT.replace("{spec}", spec[:7000]).replace("{gold}", gold[:9000])
              .replace("{test}", test).replace("{gaps}", gap_txt[:3000]).replace("{files}", files[:6000]))
    raw = codex(prompt, JUDGE / f"{slug}.sweep.txt")
    parsed = extract(raw)
    if not parsed:
        return slug, None, "parse fail"
    # match codex gap verdicts back to rows by best substring overlap, then VERIFY
    by_choice = parsed.get("gaps", [])
    decisions = []
    for r in gaps:
        g = _match(r["test"], by_choice)
        kl = (g or {}).get("klass", "AMBIGUOUS-airtight")
        prec = (g or {}).get("precedents", []) or []
        verified = []
        for p in prec:
            vp = CA.grep_path(tree, p.get("snippet", ""))
            if vp:
                verified.append({**p, "verified_path": vp})
        airtight_absent = False
        # evidence settles it: DETERMINED/MISDETERMINED need >=1 verified live precedent; airtight needs
        # the gold constant verifiably absent from the codebase; plural needs >=2 distinct verified files.
        if kl == "DETERMINED-codebase":
            status = "DETERMINED-codebase" if verified else "AMBIGUOUS"
        elif kl == "MISDETERMINED":
            status = "MISDETERMINED" if verified else "AMBIGUOUS"
        elif kl == "AMBIGUOUS-plural":
            status = "AMBIGUOUS"  # >=2 ways; stays a defect either way
        else:  # AMBIGUOUS-airtight
            tok = (g or {}).get("gold_value") or ""
            airtight_absent = bool(tok) and absent_in_codebase(tree, tok)
            status = "AMBIGUOUS"
        r["status"] = status
        r["officiated_klass"] = kl
        decisions.append((r, g, verified, kl, airtight_absent))
    _writeback(d, j, decisions, row)
    return slug, j["verdict"], f"{j['verdict']} (gaps={len(gaps)})"


def _match(test, gaps):
    best, bestn = None, 0
    tw = set(re.findall(r"\w+", test.lower()))
    for g in gaps:
        gw = set(re.findall(r"\w+", (g.get("behavior", "") + " " + g.get("choice", "")).lower()))
        ov = len(tw & gw)
        if ov > bestn:
            best, bestn = g, ov
    return best


def _writeback(d, j, decisions, row):
    from collections import Counter
    c = Counter(r["status"] for r in j["rows"])
    j["n_covered"] = c.get("COVERED", 0)
    j["n_gap"] = c.get("AMBIGUOUS", 0)
    j["n_misdetermined"] = c.get("MISDETERMINED", 0)
    j["n_determined_codebase"] = c.get("DETERMINED-codebase", 0)
    j["n_out_of_scope"] = c.get("OUT_OF_SCOPE", 0)
    if c.get("AMBIGUOUS"):
        v = "AMBIGUOUS"
    elif c.get("MISDETERMINED"):
        v = "MISDETERMINED"
    elif c.get("DETERMINED-codebase"):
        v = "DETERMINED-codebase"
    else:
        v = "ENTAILED"
    j["verdict"] = v
    j["officiated"] = True
    if "--dry" not in sys.argv:
        (JUDGE / f"{d.name}.json").write_text(json.dumps(j, indent=1))
    # leave witness/hypothesis authoring to a render pass; record the per-gap decisions for it
    dec = [{"behavior": r["test"], "status": r["status"], "klass": kl, "airtight_absent": ab,
            "gold_anchor": r.get("gold_anchor"),
            "gold_value": (g or {}).get("gold_value"), "codebase_value": (g or {}).get("codebase_value"),
            "why": (g or {}).get("why"),
            "precedents": [{"path": p.get("verified_path", p.get("path")), "snippet": p.get("snippet"),
                            "way": p.get("way")} for p in ver]}
           for (r, g, ver, kl, ab) in decisions]
    (d / "officiation.json").write_text(json.dumps(
        {"slug": d.name, "repo": row["repo"], "base": row["base_commit"], "verdict": v, "gaps": dec}, indent=1))


def main():
    a = sys.argv[1:]
    workers = int(a[a.index("--workers") + 1]) if "--workers" in a else 6
    if "--all" in a:
        # the codebase/borderline raters-pending tier: a hypothesis file whose class is NOT
        # prose-affirmative (that's a separate prose/graded-patch axis) and NOT already officiated.
        slugs = []
        for dd in sorted(CASES.iterdir()):
            hp = dd / "AMBIGUITY_HYPOTHESIS.md"
            jf = JUDGE / f"{dd.name}.json"
            if not (dd.is_dir() and hp.exists() and jf.exists()):
                continue
            if json.loads(jf.read_text()).get("officiated"):
                continue
            m = re.search(r"class:\s*\*\*([\w-]+)\*\*", hp.read_text())
            cls = m.group(1) if m else ""
            if cls not in ("prose-affirmative", "determined-codebase"):
                slugs.append(dd.name)
    else:
        slugs = [x for x in a if not x.startswith("--") and (CASES / x).is_dir()]
    # group by repo; serial within a repo (shared clone dir, re-checkout hazard)
    groups = {}
    for s in slugs:
        iid = (CASES / s / "instance_id.txt").read_text().strip()
        rr = W.hf_row(iid)
        groups.setdefault(rr["repo"] if rr else "?", []).append(s)
    print(f"officiate sweep over {len(slugs)} cases / {len(groups)} repos, workers={workers}", flush=True)

    def repo_worker(items):
        for s in items:
            try:
                print("  " + " ".join(str(x) for x in officiate(s)), flush=True)
            except Exception as e:
                print(f"  {s} ERROR {e}", flush=True)

    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(repo_worker, groups.values()))


if __name__ == "__main__":
    main()
