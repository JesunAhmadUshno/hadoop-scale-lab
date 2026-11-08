#!/usr/bin/env python3
"""Job 2 combiner: sum count:total pairs per band."""
import sys


def _sums():
    cur = None
    cnt = 0
    tot = 0
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line:
            continue
        band, value = line.split("\t", 1)
        c, t = value.split(":")
        if band != cur:
            if cur is not None:
                yield cur, cnt, tot
            cur, cnt, tot = band, 0, 0
        cnt += int(c)
        tot += int(t)
    if cur is not None:
        yield cur, cnt, tot


def main():
    for band, cnt, tot in _sums():
        sys.stdout.write("%s\t%d:%d\n" % (band, cnt, tot))


if __name__ == "__main__":
    main()
