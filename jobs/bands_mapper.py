#!/usr/bin/env python3
"""Job 2 mapper: document line -> band_id TAB 1:token_count.

Documents with zero tokens fall in no band (shared rule in
common.band_index) and emit nothing.
"""
import sys

import _bootstrap  # noqa: F401
from common import BAND_IDS, band_index, parse_doc_line, tokenize


def main():
    out = sys.stdout
    for line in sys.stdin:
        if not line.strip():
            continue
        _docid, text = parse_doc_line(line)
        n = len(tokenize(text))
        b = band_index(n)
        if b is not None:
            out.write("%s\t1:%d\n" % (BAND_IDS[b], n))


if __name__ == "__main__":
    main()
