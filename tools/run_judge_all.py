#!/usr/bin/env python3
"""run_judge_all.py -- drive judge_pool over the full 728 public set, resumably, in commit batches.

Builds the case list in Python (no shell globbing -- the Bash tool is zsh and won't word-split), skips
cases that already have a data/judge/<slug>.json (resume), and runs judge_pool.judge() with a thread
pool. Excludes the 4 hand-curated worked cases (their judge JSON is authoritative) and the 3
golddefect dirs (KNOWN_BAD; gold is broken so coverage is moot). Commits every --commit-batch cases.

  tools/run_judge_all.py [--workers 12] [--commit-batch 50] [--limit N] [--no-commit]
"""
import sys, subprocess, pathlib, concurrent.futures as cf
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import judge_pool

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"
JUDGE = AUDIT / "data" / "judge"
SKIP = {"tutao", "element", "qutebrowser", "protonmail",
        "ansible_golddefect", "nodebb_golddefect", "vuls_golddefect"}


def commit(n_done, total):
    subprocess.run(["git", "add", "data/judge", "data/attribution"], cwd=AUDIT)
    subprocess.run(["git", "commit", "-q", "-m",
                    f"judge_pool coverage pass: {n_done}/{total} cases labeled (incremental)"],
                   cwd=AUDIT)


def main():
    a = sys.argv
    workers = int(a[a.index("--workers") + 1]) if "--workers" in a else 12
    cbatch = int(a[a.index("--commit-batch") + 1]) if "--commit-batch" in a else 50
    limit = int(a[a.index("--limit") + 1]) if "--limit" in a else None
    do_commit = "--no-commit" not in a

    all_dirs = sorted(d for d in CASES.iterdir()
                      if d.is_dir() and d.name not in SKIP and (d / "spec.md").exists())
    todo = [d for d in all_dirs if not (JUDGE / f"{d.name}.json").exists()]
    if limit:
        todo = todo[:limit]
    print(f"coverage targets: {len(all_dirs)} | already judged: {len(all_dirs)-len(todo)} | "
          f"to run now: {len(todo)} | workers={workers}")

    done = 0
    since_commit = 0
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(judge_pool.judge, str(d)): d.name for d in todo}
        for fut in cf.as_completed(futs):
            name = futs[fut]
            try:
                r = fut.result()
                print(f"  {r['case']:36s} {r['verdict']:9s} cov={r['n_covered']}/{r['in_gold_total']} "
                      f"GAP={r['n_gap']} oos={r['n_out_of_scope']} ok={r['ok']}")
            except Exception as e:
                print(f"  {name:36s} EXC {e}")
            done += 1; since_commit += 1
            if do_commit and since_commit >= cbatch:
                commit(done, len(todo)); since_commit = 0
                print(f"  --- committed at {done}/{len(todo)} ---")
    if do_commit and since_commit:
        commit(done, len(todo))
        print(f"  --- final commit at {done}/{len(todo)} ---")
    print(f"DONE: ran {done} cases")


if __name__ == "__main__":
    main()
