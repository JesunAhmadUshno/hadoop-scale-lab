#!/bin/sh
# Correctness smoke test on THIS machine (never the machine of
# record): runs the pipe-vs-baseline equivalence suite. No timing
# number produced here is ever reported.
set -eu
cd "$(dirname "$0")/.."
python3 -m pytest tests/test_equivalence.py tests/test_common.py \
    tests/test_strip.py tests/test_build_corpus.py -q
echo "smoke OK: streaming jobs and baseline agree byte-for-byte"
