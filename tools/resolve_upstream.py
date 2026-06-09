#!/usr/bin/env python3
"""resolve_upstream.py -- backlink each case to its real upstream GitHub PR.

The instance_id is instance_<org>__<name>-<fix_commit>-v<env_commit>; <fix_commit> is the merge/fix
commit, which the GitHub API maps to the PR that introduced the graded change. This is the deepest rung
of the audit's progressive-disclosure ladder: claim -> witness -> spec/gold/test -> the real PR where the
maintainer made the choice the hidden test pins. It also lets a reader check, on the record, whether the
upstream issue underspecified that choice -- external ground truth, not a model proxy.

Writes data/cases/<slug>/upstream.json = {repo, fix_commit, pr_number, pr_url, pr_title}. Resumable.

  tools/resolve_upstream.py <slug>...|--claimable|--all [--force]
"""
import sys, re, json, subprocess, pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
CASES = REPO / "data" / "cases"
IID = re.compile(r"instance_([^_]+)__(.+?)-([0-9a-f]{40})(?:-v.*)?$")


def parse_iid(iid):
    m = IID.match(iid)
    if not m:
        return None, None
    org, name, fix = m.group(1), m.group(2), m.group(3)
    return f"{org}/{name}", fix


def gh_pr(repo, commit):
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{repo}/commits/{commit}/pulls",
             "--jq", ".[0] | {number, url: .html_url, title}"],
            capture_output=True, text=True, timeout=30)
        s = out.stdout.strip()
        return json.loads(s) if s and s != "null" else None
    except Exception:
        return None


def iid_of(d):
    p = d / "instance_id.txt"
    if p.exists() and p.read_text().strip():
        return p.read_text().strip()
    ca = d / "codebase_ambiguity.json"
    if ca.exists():
        v = json.loads(ca.read_text()).get("iid")
        if v:
            return v
    for fn in ("AMBIGUITY_WITNESS.md", "AMBIGUITY_HYPOTHESIS.md"):
        f = d / fn
        if f.exists():
            m = re.search(r"instance_id:\s*`([^`]+)`", f.read_text())
            if m:
                return m.group(1)
    return ""


def resolve(d):
    out = d / "upstream.json"
    if out.exists() and "--force" not in sys.argv:
        return d.name, "cached", json.loads(out.read_text()).get("pr_number")
    iid = iid_of(d)
    repo, fix = parse_iid(iid)
    if not repo:
        return d.name, "no-iid", None
    pr = gh_pr(repo, fix)
    rec = {"repo": repo, "fix_commit": fix,
           "pr_number": pr.get("number") if pr else None,
           "pr_url": pr.get("url") if pr else None,
           "pr_title": pr.get("title") if pr else None}
    out.write_text(json.dumps(rec, indent=1))
    return d.name, ("ok" if pr else "no-pr"), rec.get("pr_number")


def select(argv):
    if "--all" in argv:
        return [d for d in sorted(CASES.iterdir()) if d.is_dir()]
    if "--claimable" in argv:
        return [d for d in sorted(CASES.iterdir()) if (d / "AMBIGUITY_WITNESS.md").exists()]
    return [CASES / s for s in argv if not s.startswith("--") and (CASES / s).is_dir()]


def main():
    ds = select(sys.argv[1:])
    ok = nopr = skip = 0
    for d in ds:
        name, status, pr = resolve(d)
        if status in ("ok", "cached"):
            ok += 1
        elif status == "no-pr":
            nopr += 1
        else:
            skip += 1
        print(f"  {name:28} {status:8} {pr if pr else ''}")
    print(f"DONE: resolved={ok}  no-pr={nopr}  skipped={skip}  of {len(ds)}")


if __name__ == "__main__":
    main()
