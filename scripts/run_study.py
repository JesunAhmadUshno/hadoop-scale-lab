#!/usr/bin/env python3
"""Phase 2 driver: run the frozen study matrix on the machine of
record (the Dell R610) against the Docker Compose cluster.

This script is executed on the R610 host from the repository root.
It never runs timed cells anywhere else; PREREGISTRATION.md names
the R610 as the only machine of record.

Subcommands:
  preflight   host state snapshot (co-tenancy evidence) + cluster up
              and health waits
  prepare     build file layouts from the extracted subsets
  matrix      run the full frozen cell matrix (baselines, MapReduce
              cells, H2 layout cell, H3 replication cells)
  spark       run the optional H4 arm (only with --confirm-optional)
  down        compose down (volumes kept)
  teardown    compose down -v (cluster state removed; the study's
              end state, per the brief)

Every timed run appends one JSON object to results/raw_runs.jsonl.
Correctness is enforced here, in code: a MapReduce run whose
canonical output hash differs from the baseline's makes its cell
void, exactly as registered.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from common import BAND_IDS, band_line  # noqa: E402

SCALES = ["0.1GiB", "1GiB", "full"]
JOBS = {
    "ii": {
        "mapper": "ii_mapper.py",
        "combiner": "ii_combiner.py",
        "reducer": "ii_reducer.py",
    },
    "bands": {
        "mapper": "bands_mapper.py",
        "combiner": "bands_combiner.py",
        "reducer": "bands_reducer.py",
    },
}
STREAMING_JAR = "/opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar"
RESULTS = os.path.join(ROOT, "results")
OUTPUTS = os.path.join(RESULTS, "outputs")
RAW_RUNS = os.path.join(RESULTS, "raw_runs.jsonl")
COMBINED_BYTES = 128 * 1024 * 1024
SMALL_BYTES = 1 * 1024 * 1024


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def compose(*args, profile=None):
    cmd = ["docker", "compose"]
    if profile:
        cmd += ["--profile", profile]
    cmd += list(args)
    return sh(cmd, cwd=ROOT)


def cexec(*args):
    """Run a command inside the client container."""
    return compose("exec", "-T", "client", *args)


def log_row(row):
    os.makedirs(RESULTS, exist_ok=True)
    row = dict(row)
    row["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(RAW_RUNS, "a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(row, sort_keys=True), flush=True)


# ------------------------------------------------------------------
# Cluster lifecycle

def wait_cluster(timeout=600):
    """Wait for safemode OFF and 3 live datanodes."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = cexec("hdfs", "dfsadmin", "-report")
        out = r.stdout or ""
        live = out.count("Name: ")
        safe = cexec("hdfs", "dfsadmin", "-safemode", "get").stdout or ""
        if live >= 3 and "OFF" in safe:
            return True
        time.sleep(10)
    return False


def preflight(args):
    os.makedirs(RESULTS, exist_ok=True)
    snap = {}
    for name, cmd in {
        "docker_ps": ["docker", "ps", "--format", "{{.Names}} {{.Status}}"],
        "load": ["cat", "/proc/loadavg"],
        "free": ["free", "-h"],
        "nproc": ["nproc"],
    }.items():
        r = sh(cmd)
        snap[name] = (r.stdout or r.stderr).strip()
    with open(os.path.join(RESULTS, "host_state.json"), "w") as f:
        json.dump(snap, f, indent=2, sort_keys=True)
    r = compose("up", "-d", "--build")
    if r.returncode != 0:
        print(r.stdout, r.stderr, file=sys.stderr)
        return 1
    if not wait_cluster():
        print("cluster did not become healthy", file=sys.stderr)
        return 1
    py = compose("exec", "-T", "nodemanager", "python3", "--version")
    print("nodemanager python:", (py.stdout or py.stderr).strip())
    if py.returncode != 0:
        print("python3 missing on nodemanager", file=sys.stderr)
        return 1
    print("cluster healthy")
    return 0


# ------------------------------------------------------------------
# Layouts and ingest

def subset_path(scale):
    return os.path.join(ROOT, "data", "docs_%s.tsv" % scale)


def layout_dir(scale, layout):
    return os.path.join(ROOT, "data", "layouts", "%s_%s" % (scale, layout))


def prepare(args):
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from split_layout import split
    summary = {}
    for scale in SCALES:
        src = subset_path(scale)
        if not os.path.exists(src):
            print("missing subset", src, file=sys.stderr)
            return 1
        out = layout_dir(scale, "combined")
        summary["%s_combined" % scale] = split(src, out, COMBINED_BYTES)
        if scale == "1GiB":
            out_small = layout_dir(scale, "small")
            summary["1GiB_small"] = split(src, out_small, SMALL_BYTES)
    with open(os.path.join(RESULTS, "layouts.json"), "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    print(json.dumps(summary, indent=2))
    return 0


def hdfs_dir(scale, layout, suffix=""):
    return "/data/%s_%s%s" % (scale, layout, suffix)


def ingest(scale, layout, rf, suffix=""):
    """Put a layout directory into HDFS at the given replication.
    Returns wall seconds of the put."""
    local = "/work/data/layouts/%s_%s" % (scale, layout)
    dest = hdfs_dir(scale, layout, suffix)
    cexec("hdfs", "dfs", "-rm", "-r", "-f", dest)
    cexec("hdfs", "dfs", "-mkdir", "-p", "/data")
    t0 = time.monotonic()
    r = cexec(
        "hdfs", "dfs", "-D", "dfs.replication=%d" % rf,
        "-put", local, dest,
    )
    wall = time.monotonic() - t0
    if r.returncode != 0:
        raise RuntimeError("ingest failed: %s" % (r.stderr or r.stdout))
    return wall


def input_stats(scale, layout, suffix=""):
    dest = hdfs_dir(scale, layout, suffix)
    local = layout_dir(scale, layout)
    files = len([x for x in os.listdir(local) if x.endswith(".tsv")])
    blocks = None
    r = cexec("hdfs", "fsck", dest)
    m = re.search(r"Total blocks \(validated\):\s+(\d+)", r.stdout or "")
    if m:
        blocks = int(m.group(1))
    return {"input_files": files, "hdfs_blocks": blocks}


# ------------------------------------------------------------------
# Job execution

_COUNTER_RES = {
    "reduce_shuffle_bytes": r"Reduce shuffle bytes=(\d+)",
    "hdfs_bytes_read": r"HDFS: Number of bytes read=(\d+)",
    "hdfs_bytes_written": r"HDFS: Number of bytes written=(\d+)",
    "file_bytes_written": r"FILE: Number of bytes written=(\d+)",
}


def parse_counters(text):
    out = {}
    for key, pat in _COUNTER_RES.items():
        m = re.search(pat, text or "")
        out[key] = int(m.group(1)) if m else None
    return out


def run_mr(job, hdfs_in, hdfs_out):
    """One MapReduce run. Returns (wall_s, counters, stderr)."""
    spec = JOBS[job]
    files = [
        "/work/jobs/%s" % spec["mapper"],
        "/work/jobs/%s" % spec["combiner"],
        "/work/jobs/%s" % spec["reducer"],
        "/work/jobs/_bootstrap.py",
        "/work/src/common.py",
    ]
    cexec("hdfs", "dfs", "-rm", "-r", "-f", hdfs_out)
    cmd = [
        "hadoop", "jar", STREAMING_JAR,
        "-D", "mapreduce.job.reduces=4",
        "-D", "dfs.replication=1",
        "-files", ",".join(files),
        # YARN localizes -files as symlinks into per-file filecache
        # directories, so the interpreter's sys.path[0] is the
        # script's filecache dir, not the task working directory
        # where _bootstrap.py and common.py land. Putting the task
        # working directory on PYTHONPATH restores the imports
        # (DECISIONS.md D8).
        "-cmdenv", "PYTHONPATH=.",
        # The image's Python 3.6 under the C locale decodes stdin
        # as ASCII with surrogateescape, which silently splits
        # every non-ASCII token; the baseline reads UTF-8. Force
        # UTF-8 on the task streams (DECISIONS.md D9).
        "-cmdenv", "PYTHONIOENCODING=utf-8",
        "-mapper", "python3 %s" % spec["mapper"],
        "-combiner", "python3 %s" % spec["combiner"],
        "-reducer", "python3 %s" % spec["reducer"],
        "-input", hdfs_in,
        "-output", hdfs_out,
    ]
    t0 = time.monotonic()
    r = cexec(*cmd)
    wall = time.monotonic() - t0
    if r.returncode != 0:
        raise RuntimeError("MR job failed: %s" % (r.stderr or "")[-2000:])
    # The Hadoop 3.3.6 client prints the counter table to stdout,
    # not stderr; parse both streams (DECISIONS.md D9).
    return wall, parse_counters((r.stdout or "") + (r.stderr or "")), r.stderr


def canonical_file_sha(path):
    """SHA-256 of a file's lines sorted bytewise, streamed through a
    temporary file so multi-GB outputs never sit in memory."""
    import hashlib
    import tempfile

    fd, tmp = tempfile.mkstemp(prefix="canonical-")
    try:
        with os.fdopen(fd, "wb") as out:
            r = subprocess.run(
                ["sort"], stdin=open(path, "rb"), stdout=out,
                env={**os.environ, "LC_ALL": "C"},
            )
        if r.returncode != 0:
            raise RuntimeError("sort failed")
        h = hashlib.sha256()
        n = 0
        with open(tmp, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
                n += chunk.count(b"\n")
        return h.hexdigest(), n
    finally:
        os.unlink(tmp)


def collect_mr(hdfs_out, job, tag):
    """Pull an MR output back and hash it with the SAME function the
    baseline uses (canonical_file_sha), so the void rule compares
    like with like byte for byte. Bands outputs get their
    missing-band zero lines appended first, per the frozen assembly
    rule in PREREGISTRATION.md."""
    os.makedirs(OUTPUTS, exist_ok=True)
    raw_path = os.path.join(OUTPUTS, "%s.raw" % tag)
    with open(raw_path, "wb") as f:
        r = compose(
            "exec", "-T", "client", "hdfs", "dfs", "-cat", hdfs_out + "/part-*"
        )
        f.write(r.stdout.encode("utf-8") if isinstance(r.stdout, str) else r.stdout)
    if job == "bands":
        present = set()
        with open(raw_path, "r", encoding="utf-8") as f:
            for ln in f:
                if ln.strip():
                    present.add(ln.split("\t", 1)[0])
        with open(raw_path, "a", encoding="utf-8") as f:
            for i, bid in enumerate(BAND_IDS):
                if bid not in present:
                    f.write(band_line(i, 0, 0) + "\n")
    n = 0
    with open(raw_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            n += chunk.count(b"\n")
    sha, _sorted_n = canonical_file_sha(raw_path)
    return sha, n


def run_baseline(job, scale, tag):
    os.makedirs(OUTPUTS, exist_ok=True)
    out_path = os.path.join(OUTPUTS, "%s.txt" % tag)
    cmd = [
        sys.executable, os.path.join(ROOT, "src", "baseline.py"),
        "--job", job, "--input", subset_path(scale),
        "--output", out_path,
    ]
    t0 = time.monotonic()
    r = sh(cmd)
    wall = time.monotonic() - t0
    if r.returncode != 0:
        raise RuntimeError("baseline failed: %s" % (r.stderr or "")[-2000:])
    sha, _n = canonical_file_sha(out_path)
    return wall, sha


# ------------------------------------------------------------------
# The frozen matrix

def timed_cell_mr(job, scale, layout, rf=1, suffix="", ref_sha=None):
    """Warm-up + 3 timed MR runs for one cell, with the void rule."""
    stats = input_stats(scale, layout, suffix)
    hin = hdfs_dir(scale, layout, suffix)
    rows = []
    ok = True
    for idx in range(0, 4):
        warmup = idx == 0
        hout = "/out/%s_%s_%s%s_r%d" % (job, scale, layout, suffix, idx)
        wall, counters, _err = run_mr(job, hin, hout)
        sha, _n = collect_mr(hout, job, "mr_%s_%s_%s%s_r%d" % (job, scale, layout, suffix, idx))
        void = ref_sha is not None and sha != ref_sha
        ok = ok and not void
        row = {
            "kind": "run", "arm": "mapreduce", "job": job, "scale": scale,
            "layout": layout, "rf": rf, "suffix": suffix, "run_index": idx,
            "warmup": warmup, "wall_s": None if warmup else round(wall, 3),
            "counters": counters, "output_sha256": sha, "void": void,
            **stats,
        }
        rows.append(row)
        log_row(row)
    return rows, ok


def timed_cell_baseline(job, scale):
    rows = []
    shas = set()
    for idx in range(0, 4):
        warmup = idx == 0
        wall, sha = run_baseline(job, scale, "baseline_%s_%s_r%d" % (job, scale, idx))
        shas.add(sha)
        row = {
            "kind": "run", "arm": "baseline", "job": job, "scale": scale,
            "layout": "local", "rf": None, "run_index": idx,
            "warmup": warmup, "wall_s": None if warmup else round(wall, 3),
            "counters": None, "output_sha256": sha, "void": False,
        }
        rows.append(row)
        log_row(row)
    if len(shas) != 1:
        raise RuntimeError(
            "baseline is not deterministic for %s %s: %s" % (job, scale, shas)
        )
    return rows, shas.pop()


def matrix(args):
    # Ingest the combined layouts once at rf=1 for the main matrix.
    for scale in SCALES:
        ingest(scale, "combined", 1)
    ingest("1GiB", "small", 1)

    ref_shas = {}
    for job in JOBS:
        for scale in SCALES:
            _brows, ref_sha = timed_cell_baseline(job, scale)
            ref_shas[(job, scale)] = ref_sha
            rows, ok = timed_cell_mr(job, scale, "combined", rf=1, ref_sha=ref_sha)
            if not ok:
                log_row({"kind": "void_cell", "job": job, "scale": scale,
                         "layout": "combined",
                         "note": "checksum mismatch; cell void per protocol, "
                                 "re-run once"})
                rows, ok = timed_cell_mr(job, scale, "combined", rf=1,
                                         ref_sha=ref_sha)
                if not ok:
                    log_row({"kind": "void_cell", "job": job, "scale": scale,
                             "layout": "combined",
                             "note": "still mismatched after re-run; cell "
                                     "stays void"})

    # H2: small-file layout at 1 GiB, Job 1 (the comparator is the MR
    # combined cell; the small cell's outputs must still match the
    # baseline checksum from the main matrix).
    rows, ok = timed_cell_mr("ii", "1GiB", "small", rf=1,
                             ref_sha=ref_shas[("ii", "1GiB")])
    if not ok:
        log_row({"kind": "void_cell", "job": "ii", "scale": "1GiB",
                 "layout": "small", "note": "checksum mismatch; void"})

    # H3: replication at the top scale point (full corpus, DECISIONS.md D6), Job 1. Self-contained double ingest.
    for rf in (1, 3):
        suffix = "_h3"
        w_warm = ingest("full", "combined", rf, suffix=suffix)
        log_row({"kind": "ingest", "scale": "full", "layout": "combined",
                 "rf": rf, "warmup": True, "wall_s": round(w_warm, 3)})
        w = ingest("full", "combined", rf, suffix=suffix)
        log_row({"kind": "ingest", "scale": "full", "layout": "combined",
                 "rf": rf, "warmup": False, "wall_s": round(w, 3)})
        rows, ok = timed_cell_mr("ii", "full", "combined", rf=rf,
                                 suffix=suffix,
                                 ref_sha=ref_shas[("ii", "full")])
        if not ok:
            log_row({"kind": "void_cell", "job": "ii", "scale": "full",
                     "layout": "combined", "rf": rf,
                     "note": "checksum mismatch; void"})
    print("matrix complete")
    return 0


def spark(args):
    if not args.confirm_optional:
        print("H4 is optional; pass --confirm-optional to run it")
        return 1
    compose("up", "-d", "spark-client", profile="spark")
    hin = "hdfs:///data/full_combined"
    hout = "hdfs:///out/ii_spark_full"
    cexec("hdfs", "dfs", "-rm", "-r", "-f", "/out/ii_spark_full")
    cmd = [
        "/opt/spark/bin/spark-submit", "--master", "yarn",
        "--deploy-mode", "client",
        # The driver runs the spark image's Python 3.8 while YARN
        # executors land in the Hadoop image, whose python3 is
        # 3.6.8; PySpark refuses the mismatch
        # (PYTHON_VERSION_MISMATCH). A standalone CPython 3.8.19
        # (python-build-standalone, DECISIONS.md D13) is shipped
        # to the executors through the distributed cache and used
        # as the worker interpreter. The job code, data, master,
        # and the H4 comparison are unchanged.
        "--conf",
        "spark.yarn.dist.archives=/work/spark/pbs38.tar.gz#python",
        "--conf", "spark.pyspark.python=python/python/bin/python3.8",
        # spark.pyspark.python is also the driver's fallback
        # interpreter; pin the driver to the spark image's own
        # Python 3.8 so only the workers use the archive path.
        "--conf",
        "spark.pyspark.driver.python=/usr/bin/python3",
        "--conf",
        "spark.executorEnv.PYSPARK_PYTHON=python/python/bin/python3.8",
        # The job imports the shared tokenizer (src/common.py) on
        # the driver; its closures reference the module by name,
        # so the workers need the module shipped with the job.
        "--py-files", "/work/src/common.py",
        "/work/spark/inverted_index_spark.py",
        "--input", hin, "--output", hout,
    ]
    t0 = time.monotonic()
    r = compose("exec", "-T", "spark-client", *cmd, profile="spark")
    wall = time.monotonic() - t0
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return 1
    # Three timed runs are required by the protocol; this subcommand
    # performs one invocation per call by design, so call it 3 times
    # after one warm-up call with --warmup.
    sha, _n = collect_mr("/out/ii_spark_full", "ii", "spark_ii_full")
    # The checksum rule applies to the optional arm too: compare
    # against the baseline reference hash already in the run log.
    ref_sha = None
    if os.path.exists(RAW_RUNS):
        with open(RAW_RUNS) as f:
            for line in f:
                row = json.loads(line)
                if (row.get("arm") == "baseline" and row.get("job") == "ii"
                        and row.get("scale") == "full"):
                    ref_sha = row.get("output_sha256")
                    break
    void = ref_sha is not None and sha != ref_sha
    log_row({
        "kind": "run", "arm": "spark", "job": "ii", "scale": "full",
        "layout": "combined", "rf": 1, "run_index": args.run_index,
        "warmup": args.warmup,
        "wall_s": None if args.warmup else round(wall, 3),
        "counters": None, "output_sha256": sha, "void": void,
    })
    return 0


def down(args):
    r = compose("down")
    print(r.stdout, r.stderr)
    return r.returncode


def teardown(args):
    r = compose("down", "-v")
    print(r.stdout, r.stderr)
    print("cluster containers and volumes removed")
    return r.returncode


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preflight")
    sub.add_parser("prepare")
    sub.add_parser("matrix")
    sp = sub.add_parser("spark")
    sp.add_argument("--confirm-optional", action="store_true")
    sp.add_argument("--warmup", action="store_true")
    sp.add_argument("--run-index", type=int, default=1)
    sub.add_parser("down")
    sub.add_parser("teardown")
    args = ap.parse_args(argv)
    fn = {
        "preflight": preflight,
        "prepare": prepare,
        "matrix": matrix,
        "spark": spark,
        "down": down,
        "teardown": teardown,
    }[args.cmd]
    return fn(args)


if __name__ == "__main__":
    sys.exit(main())
