#!/usr/bin/env python3
"""Generate RESULTS.md from results/raw_runs.jsonl.

Every number in RESULTS.md is computed here from the raw run rows;
verdicts follow the frozen rules in PREREGISTRATION.md exactly.
With no run rows, this writes the honest awaiting-runs RESULTS.md.
"""

import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "results", "raw_runs.jsonl")
OUT = os.path.join(ROOT, "RESULTS.md")
SCALES = ["0.1GiB", "1GiB", "5GiB"]


def load_rows():
    if not os.path.exists(RAW):
        return []
    rows = []
    with open(RAW) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def median_wall(rows, **match):
    vals = [
        r["wall_s"]
        for r in rows
        if r.get("kind") == "run"
        and not r.get("warmup")
        and not r.get("void")
        and r.get("wall_s") is not None
        and all(r.get(k) == v for k, v in match.items())
    ]
    return statistics.median(vals) if vals else None


def verdict_h1(rows):
    r_small = ratio(rows, "ii", "0.1GiB")
    r_big = ratio(rows, "ii", "5GiB")
    if r_small is None or r_big is None:
        return "INCONCLUSIVE", "a needed cell is missing or void"
    if r_big <= 1.0 or r_big <= 0.5 * r_small:
        return "CONFIRMED", "R(5 GiB)=%.3f, R(0.1 GiB)=%.3f" % (r_big, r_small)
    if r_big >= r_small:
        return "REFUTED", "R(5 GiB)=%.3f >= R(0.1 GiB)=%.3f" % (r_big, r_small)
    return "INCONCLUSIVE", "gap narrowed by less than half: %.3f vs %.3f" % (
        r_big, r_small)


def ratio(rows, job, scale, layout="combined", arm_mr=True):
    mr = median_wall(rows, arm="mapreduce", job=job, scale=scale,
                     layout=layout, suffix="")
    base = median_wall(rows, arm="baseline", job=job, scale=scale)
    if mr is None or base is None:
        return None
    return mr / base


def verdict_h2(rows):
    comb = median_wall(rows, arm="mapreduce", job="ii", scale="1GiB",
                       layout="combined", suffix="")
    small = median_wall(rows, arm="mapreduce", job="ii", scale="1GiB",
                        layout="small", suffix="")
    if comb is None or small is None:
        return "INCONCLUSIVE", "a needed cell is missing or void"
    cost = (small - comb) / comb * 100.0
    if cost >= 15.0:
        return "CONFIRMED", "small-file cost %.1f%%" % cost
    if cost <= 5.0:
        return "REFUTED", "small-file cost %.1f%%" % cost
    return "INCONCLUSIVE", "small-file cost %.1f%%" % cost


def ingest_wall(rows, rf):
    vals = [
        r["wall_s"]
        for r in rows
        if r.get("kind") == "ingest" and r.get("rf") == rf
        and not r.get("warmup")
    ]
    return vals[0] if vals else None


def verdict_h3(rows):
    w1, w3 = ingest_wall(rows, 1), ingest_wall(rows, 3)
    t1 = median_wall(rows, arm="mapreduce", job="ii", scale="5GiB",
                     layout="combined", rf=1, suffix="_h3")
    t3 = median_wall(rows, arm="mapreduce", job="ii", scale="5GiB",
                     layout="combined", rf=3, suffix="_h3")
    if None in (w1, w3, t1, t3):
        return "INCONCLUSIVE", "a needed cell is missing or void"
    wp = (w3 - w1) / w1 * 100.0
    tp = (t3 - t1) / t1 * 100.0
    detail = "write penalty %.1f%%, job penalty %.1f%%" % (wp, tp)
    if wp >= 15.0 and tp >= 5.0:
        return "CONFIRMED", detail
    if wp < 5.0 and tp < 5.0:
        return "REFUTED", detail
    return "INCONCLUSIVE", detail


def verdict_h4(rows):
    spark = median_wall(rows, arm="spark", job="ii", scale="5GiB")
    mr = median_wall(rows, arm="mapreduce", job="ii", scale="5GiB",
                     layout="combined", rf=1, suffix="")
    if spark is None:
        return "NOT TESTED", "optional arm not run"
    if mr is None:
        return "INCONCLUSIVE", "MapReduce comparator cell missing"
    if spark <= 0.70 * mr:
        return "CONFIRMED", "spark %.1fs vs MR %.1fs" % (spark, mr)
    if spark >= mr:
        return "REFUTED", "spark %.1fs vs MR %.1fs" % (spark, mr)
    return "INCONCLUSIVE", "spark %.1fs vs MR %.1fs" % (spark, mr)


def fmt(x, nd=3):
    return "n/a" if x is None else ("%.*f" % (nd, x))


def main():
    rows = load_rows()
    lines = ["# Results", ""]
    if not rows:
        lines += [
            "Status: AWAITING TIMED RUNS.",
            "",
            "The study is pre-registered (PREREGISTRATION.md) and the",
            "harness is built and correctness-tested, but no timed cell",
            "has been run: the machine of record (Dell R610) is not yet",
            "reachable by SSH, so Phase 2 has not started. No number in",
            "this repository comes from any other machine.",
            "",
            "Per-hypothesis state:",
            "",
            "- H1 (scale crossover): NOT TESTED, awaiting runs.",
            "- H2 (small-file effect): NOT TESTED, awaiting runs.",
            "- H3 (replication cost): NOT TESTED, awaiting runs.",
            "- H4 (Spark arm, optional): NOT TESTED, awaiting runs.",
            "",
        ]
        with open(OUT, "w") as f:
            f.write("\n".join(lines))
        print("wrote awaiting-runs RESULTS.md")
        return 0

    verdicts = {
        "H1": verdict_h1(rows),
        "H2": verdict_h2(rows),
        "H3": verdict_h3(rows),
        "H4": verdict_h4(rows),
    }
    lines += ["## Verdicts (frozen rules, PREREGISTRATION.md)", ""]
    for h in ("H1", "H2", "H3", "H4"):
        v, detail = verdicts[h]
        lines.append("- %s: **%s**. %s" % (h, v, detail))
    lines += ["", "## Median wall times (seconds, 3 timed runs per cell)", "",
              "| Job | Scale | Baseline | MapReduce | Ratio |",
              "| --- | --- | --- | --- | --- |"]
    for job in ("ii", "bands"):
        for scale in SCALES:
            b = median_wall(rows, arm="baseline", job=job, scale=scale)
            m = median_wall(rows, arm="mapreduce", job=job, scale=scale,
                            layout="combined", suffix="")
            r = ratio(rows, job, scale)
            lines.append("| %s | %s | %s | %s | %s |" % (
                job, scale, fmt(b), fmt(m), fmt(r)))
    lines += ["", "## Raw run table", "",
              "| Arm | Job | Scale | Layout | RF | Run | Warm-up | Wall s | "
              "Shuffle bytes | HDFS read | HDFS written | SHA-256 (short) | Void |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        if r.get("kind") != "run":
            continue
        c = r.get("counters") or {}
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r.get("arm"), r.get("job"), r.get("scale"), r.get("layout"),
            r.get("rf"), r.get("run_index"), r.get("warmup"),
            fmt(r.get("wall_s")), c.get("reduce_shuffle_bytes"),
            c.get("hdfs_bytes_read"), c.get("hdfs_bytes_written"),
            (r.get("output_sha256") or "")[:12], r.get("void")))
    for r in rows:
        if r.get("kind") == "ingest":
            lines.append("")
            lines.append("Ingest: scale %s rf %s warm-up %s wall %s s" % (
                r.get("scale"), r.get("rf"), r.get("warmup"),
                fmt(r.get("wall_s"))))
        if r.get("kind") == "void_cell":
            lines.append("")
            lines.append("VOID CELL: job %s scale %s layout %s: %s" % (
                r.get("job"), r.get("scale"), r.get("layout"), r.get("note")))
    lines.append("")
    with open(OUT, "w") as f:
        f.write("\n".join(lines))
    print("wrote RESULTS.md with verdicts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
