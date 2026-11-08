#!/usr/bin/env python3
"""Job 1 mapper: document line -> term TAB docid:tf per distinct term."""
import sys

import _bootstrap  # noqa: F401
from common import parse_doc_line, tokenize


def main():
    from collections import Counter

    out = sys.stdout
    for line in sys.stdin:
        if not line.strip():
            continue
        docid, text = parse_doc_line(line)
        for term, tf in Counter(tokenize(text)).items():
            out.write("%s\t%d:%d\n" % (term, docid, tf))


if __name__ == "__main__":
    main()
