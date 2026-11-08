#!/usr/bin/env python3
"""Job 1 combiner: merge posting chunks per term.

Input values are "docid:tf" or comma-joined chunks of them; output is
one comma-joined chunk per term. Merging is associative, so the
reducer sees the same posting multiset with or without combining.
"""
import sys


def _emit(term, chunks):
    if term is not None and chunks:
        sys.stdout.write("%s\t%s\n" % (term, ",".join(chunks)))


def main():
    cur_term = None
    chunks = []
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line:
            continue
        term, value = line.split("\t", 1)
        if term != cur_term:
            _emit(cur_term, chunks)
            cur_term = term
            chunks = []
        chunks.append(value)
    _emit(cur_term, chunks)


if __name__ == "__main__":
    main()
