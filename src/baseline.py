"""Tuned single-node baseline for both jobs (see PREREGISTRATION.md).

One process on the host. Tokenization uses src/common.py, the same
code path as the Streaming mapper. Aggregation runs in DuckDB:
group-by for both jobs. Job 1's posting lists are assembled in
Python from DuckDB's term-ordered rows; Job 2's means are formatted
in Python from DuckDB's integer counts and totals, so the bytes
match the MapReduce arm exactly.

Token rows reach DuckDB through a temporary CSV (DuckDB reads it
with read_csv); the temporary file lives in --workdir and is removed
at the end.

Usage:
  python src/baseline.py --job ii    --input docs.tsv --output out.txt
  python src/baseline.py --job bands --input docs.tsv --output out.txt
"""

import argparse
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import duckdb  # noqa: E402

from common import BANDS, band_index, band_line, parse_doc_line, tokenize  # noqa: E402


def _iter_docs(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield parse_doc_line(line)


def run_ii(input_path, output_path, workdir, threads, memory_limit):
    from collections import Counter

    tmp_csv = os.path.join(workdir, "tokens.csv")
    n_docs = 0
    with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for docid, text in _iter_docs(input_path):
            n_docs += 1
            for term, tf in Counter(tokenize(text)).items():
                w.writerow([term, docid, tf])
    con = duckdb.connect()
    con.execute("PRAGMA threads=%d" % threads)
    con.execute("PRAGMA memory_limit='%s'" % memory_limit)
    con.execute(
        "CREATE TABLE tokens AS SELECT * FROM read_csv(?, "
        "columns={'term':'VARCHAR','docid':'BIGINT','tf':'BIGINT'}, "
        "header=false)" % (),
        [tmp_csv],
    )
    stats = {
        term: (df, total)
        for term, df, total in con.execute(
            "SELECT term, count(*), sum(tf) FROM tokens GROUP BY term"
        ).fetchall()
    }
    cur = con.execute("SELECT term, docid, tf FROM tokens ORDER BY term, docid")
    with open(output_path, "w", encoding="utf-8") as out:
        state = {"term": None, "postings": []}

        def flush():
            if state["term"] is None:
                return
            df, total = stats[state["term"]]
            body = ",".join("%d:%d" % (d, t) for d, t in state["postings"])
            out.write("%s\t%d\t%d\t%s\n" % (state["term"], df, total, body))

        while True:
            rows = cur.fetchmany(100000)
            if not rows:
                break
            for term, docid, tf in rows:
                if term != state["term"]:
                    flush()
                    state["term"] = term
                    state["postings"] = []
                state["postings"].append((docid, tf))
        flush()
    con.close()
    os.remove(tmp_csv)
    return n_docs


def run_bands(input_path, output_path, workdir, threads, memory_limit):
    tmp_csv = os.path.join(workdir, "docbands.csv")
    n_docs = 0
    with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for docid, text in _iter_docs(input_path):
            n_docs += 1
            n = len(tokenize(text))
            b = band_index(n)
            if b is not None:
                w.writerow([b, n])
    con = duckdb.connect()
    con.execute("PRAGMA threads=%d" % threads)
    con.execute("PRAGMA memory_limit='%s'" % memory_limit)
    con.execute(
        "CREATE TABLE docbands AS SELECT * FROM read_csv(?, "
        "columns={'band':'INTEGER','n':'BIGINT'}, header=false)",
        [tmp_csv],
    )
    agg = {
        band: (cnt, total)
        for band, cnt, total in con.execute(
            "SELECT band, count(*), sum(n) FROM docbands GROUP BY band"
        ).fetchall()
    }
    con.close()
    os.remove(tmp_csv)
    with open(output_path, "w", encoding="utf-8") as out:
        for i in range(len(BANDS)):
            cnt, total = agg.get(i, (0, 0))
            out.write(band_line(i, cnt, total) + "\n")
    return n_docs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", choices=["ii", "bands"], required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--threads", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--memory-limit", default="32GB")
    args = ap.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="baseline-") as workdir:
        if args.job == "ii":
            n = run_ii(args.input, args.output, workdir,
                       args.threads, args.memory_limit)
        else:
            n = run_bands(args.input, args.output, workdir,
                          args.threads, args.memory_limit)
    print("baseline %s: %d documents" % (args.job, n), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
