#!/usr/bin/env python3
"""Job 2 reducer: per band present in the input, emit the canonical
band line (common.band_line). Bands absent from every reducer input
are filled with zero lines by the collector in scripts/run_study.py,
which is part of the frozen output assembly.
"""
import sys

import _bootstrap  # noqa: F401
from common import BAND_IDS, band_line


def main():
    cur = None
    cnt = 0
    tot = 0

    def flush():
        if cur is not None:
            sys.stdout.write(band_line(BAND_IDS.index(cur), cnt, tot) + "\n")

    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line:
            continue
        band, value = line.split("\t", 1)
        c, t = value.split(":")
        if band != cur:
            flush()
            cur, cnt, tot = band, 0, 0
        cnt += int(c)
        tot += int(t)
    flush()


if __name__ == "__main__":
    main()
