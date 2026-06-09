#!/usr/bin/env python3
"""grade_r2_fleet.py -- grade the both-agree R2 candidates on the existing audit fleet.

For each candidate slug: scp driver/grade_r2.py + the case's r2.diff to a box, then run
grade_r2.py <iid> <r2.diff> on the box (gold + R2 graded, per-test clean-fail check). Collects the
R2_VERDICT json per case -> data/cases/<slug>/r2_grade.json. Round-robins across boxes; one grade per
box at a time (a ThreadPoolExecutor with one worker per box) to limit docker contention with the
running gold sweep (which is deprioritized -- ambiguity is the goal).

  tools/grade_r2_fleet.py <slug> [<slug> ...]
"""
import sys, json, subprocess, pathlib, concurrent.futures as cf

AUDIT = pathlib.Path(__file__).resolve().parent.parent
CASES = AUDIT / "data" / "cases"
COMPANION = pathlib.Path("/Users/junekim/Documents/swebench-pro")
GRADE_R2 = COMPANION / "driver" / "grade_r2.py"
SSH = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15"]


def boxes():
    out = []
    for i in range(1, 9):
        env = pathlib.Path(f"/tmp/audit{i}.env")
        if not env.exists():
            continue
        kv = dict(l.strip().split("=", 1) for l in env.read_text().splitlines() if "=" in l)
        out.append({"name": f"audit{i}", "ip": kv.get("PUBIP"), "pem": f"/tmp/{kv.get('KEY')}.pem"})
    return [b for b in out if b["ip"] and pathlib.Path(b["pem"]).exists()]


def run(box, slug):
    d = CASES / slug
    iid = (d / "instance_id.txt").read_text().strip()
    r2 = d / "r2.diff"
    if not r2.exists():
        return slug, {"error": "no r2.diff"}
    ip, pem = box["ip"], box["pem"]
    scp = ["scp", "-o", "StrictHostKeyChecking=no", "-i", pem]
    try:
        subprocess.run(scp + [str(GRADE_R2), f"ec2-user@{ip}:/home/ec2-user/swebench-pro/driver/grade_r2.py"],
                       capture_output=True, timeout=60, check=True)
        subprocess.run(scp + [str(r2), f"ec2-user@{ip}:/tmp/{slug}.r2.diff"],
                       capture_output=True, timeout=60, check=True)
        cmd = (f"cd ~/swebench-pro && . driver/.proenv && BENCH=pro $PY driver/grade_r2.py "
               f"{iid} /tmp/{slug}.r2.diff")
        r = subprocess.run(SSH + ["-i", pem, f"ec2-user@{ip}", cmd],
                           capture_output=True, text=True, timeout=3600)
        line = next((l for l in r.stdout.splitlines() if l.startswith("R2_VERDICT ")), None)
        if not line:
            return slug, {"error": "no verdict", "tail": (r.stdout + r.stderr)[-500:]}
        v = json.loads(line[len("R2_VERDICT "):])
        (d / "r2_grade.json").write_text(json.dumps(v, indent=1))
        return slug, v
    except Exception as e:
        return slug, {"error": str(e)[:300]}


def main():
    slugs = sys.argv[1:]
    bx = boxes()
    print(f"grading {len(slugs)} R2 candidates across {len(bx)} boxes")
    # assign round-robin; run one worker per box so each box does its cases sequentially
    assign = {b["name"]: [] for b in bx}
    for i, s in enumerate(slugs):
        assign[bx[i % len(bx)]["name"]].append(s)

    def box_worker(b):
        res = []
        for s in assign[b["name"]]:
            slug, v = run(b, s)
            cf_flag = v.get("clean_fail")
            print(f"  [{b['name']}] {slug}: clean_fail={cf_flag} "
                  f"r2_resolved={v.get('r2_resolved')} flips={v.get('n_flips_pass_to_fail')} "
                  f"{('ERR ' + v['error']) if 'error' in v else ''}")
            res.append((slug, v))
        return res

    with cf.ThreadPoolExecutor(max_workers=len(bx)) as ex:
        list(ex.map(box_worker, bx))
    clean = sum(1 for s in slugs if (CASES / s / "r2_grade.json").exists()
                and json.loads((CASES / s / "r2_grade.json").read_text()).get("clean_fail"))
    print(f"DONE: {clean}/{len(slugs)} CLEAN-FAIL (PROVEN graded-patch witnesses)")


if __name__ == "__main__":
    main()
