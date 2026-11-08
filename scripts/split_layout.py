#!/usr/bin/env python3
"""Split a document subset file into layout chunk files.

Frozen rule (PREREGISTRATION.md): files are filled at document
boundaries; a file ends when adding the next document would exceed
--max-bytes; every file holds at least one document. Used for the
combined layout (128 MiB) and the small-file layout (1 MiB).

Prints a JSON summary: file count and total bytes.
"""
import argparse
import json
import os
import sys


def split(input_path, outdir, max_bytes, prefix="part"):
    os.makedirs(outdir, exist_ok=True)
    count = 0
    total = 0
    cur = None
    cur_size = 0

    def open_next():
        nonlocal count, cur, cur_size
        path = os.path.join(outdir, "%s-%05d.tsv" % (prefix, count))
        count += 1
        cur = open(path, "wb")
        cur_size = 0

    open_next()
    with open(input_path, "rb") as f:
        for line in f:
            if cur_size > 0 and cur_size + len(line) > max_bytes:
                cur.close()
                open_next()
            cur.write(line)
            cur_size += len(line)
            total += len(line)
    cur.close()
    return {"files": count, "bytes": total, "max_bytes": max_bytes}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--max-bytes", type=int, required=True)
    ap.add_argument("--prefix", default="part")
    args = ap.parse_args(argv)
    print(json.dumps(split(args.input, args.outdir, args.max_bytes, args.prefix)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
