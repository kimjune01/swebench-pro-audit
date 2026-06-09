#!/usr/bin/env python3
"""upstream_comments.py -- gather the human discussion on each case's upstream PR, deep-linked.

Pure mechanical fetch (no judgment): for every claimable case that resolved to a PR (upstream.json),
pull the PR's review-thread comments and conversation comments, each with its direct GitHub permalink
(html_url) and verbatim body. Writes data/cases/<slug>/upstream_comments.json.

This is the raw material for the strongest receipt the audit can offer: a human maintainer/reviewer
discussing the very choice the hidden test pins. The LLM does not decide ambiguity here; it only fetches.
Which comment *settles* it is pointed to by a reader (or a separate located-receipt step) and deep-linked;
the comment is human-authored and a skeptic clicks straight to it.

  tools/upstream_comments.py --claimable|--all|<slug>... [--force]
"""
import sys, json, subprocess, pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
CASES = REPO / "data" / "cases"


def gh_json(path, jq):
    try:
        r = subprocess.run(["gh", "api", path, "--paginate", "--jq", jq],
                           capture_output=True, text=True, timeout=60)
        return [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def fetch(repo, n):
    jq = ".[] | {url: .html_url, user: .user.login, body: .body}"
    review = gh_json(f"repos/{repo}/pulls/{n}/comments", jq)      # inline review-thread comments
    convo = gh_json(f"repos/{repo}/issues/{n}/comments", jq)       # PR conversation comments
    return review, convo


def select(argv):
    if "--all" in argv:
        return [d for d in sorted(CASES.iterdir()) if (d / "upstream.json").exists()]
    if "--claimable" in argv:
        return [d for d in sorted(CASES.iterdir())
                if (d / "AMBIGUITY_WITNESS.md").exists() and (d / "upstream.json").exists()]
    return [CASES / s for s in argv if not s.startswith("--") and (CASES / s).is_dir()]


def main():
    ds = select(sys.argv[1:])
    done = empty = nopr = 0
    for d in ds:
        out = d / "upstream_comments.json"
        if out.exists() and "--force" not in sys.argv:
            done += 1
            continue
        u = json.loads((d / "upstream.json").read_text())
        if not u.get("pr_number"):
            nopr += 1
            continue
        review, convo = fetch(u["repo"], u["pr_number"])
        rec = {"repo": u["repo"], "pr_number": u["pr_number"], "pr_url": u["pr_url"],
               "n_review": len(review), "n_convo": len(convo),
               "review_comments": review, "conversation_comments": convo}
        out.write_text(json.dumps(rec, indent=1))
        done += 1
        if not review and not convo:
            empty += 1
        print(f"  {d.name:28} PR#{u['pr_number']:<7} review={len(review):<3} convo={len(convo)}")
    print(f"DONE: gathered={done}  no-discussion={empty}  no-pr={nopr}  of {len(ds)}")


if __name__ == "__main__":
    main()
