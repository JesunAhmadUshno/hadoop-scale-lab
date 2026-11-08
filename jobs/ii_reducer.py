#!/usr/bin/env python3
"""Job 1 reducer: per term, emit the canonical inverted-index line:
term TAB df TAB total_tf TAB docid:tf,docid:tf,... (docid ascending).
"""
import sys


def _emit(term, postings):
    if term is None:
        return
    postings.sort(key=lambda p: p[0])
    df = len(postings)
    total = sum(tf for _d, tf in postings)
    body = ",".join("%d:%d" % (d, tf) for d, tf in postings)
    sys.stdout.write("%s\t%d\t%d\t%s\n" % (term, df, total, body))


def main():
    cur_term = None
    postings = []
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line:
            continue
        term, value = line.split("\t", 1)
        if term != cur_term:
            _emit(cur_term, postings)
            cur_term = term
            postings = []
        for pair in value.split(","):
            d, tf = pair.split(":")
            postings.append((int(d), int(tf)))
    _emit(cur_term, postings)


if __name__ == "__main__":
    main()
