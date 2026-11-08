"""Shared definitions for every arm of the study.

The tokenizer, the length bands, and the document-line format are
defined once here and used by the Hadoop Streaming jobs and by the
single-node baseline, so both arms see byte-identical tokens. This is
what makes the checksum-equality rule in PREREGISTRATION.md possible.
"""

import re

# Tokens are maximal runs of Unicode letters and digits. Underscore is
# a separator, per the character class [^\W_].
TOKEN_RE = re.compile(r"[^\W_]+")

# Length bands frozen in PREREGISTRATION.md: (low, high) token counts,
# high None means unbounded. Band ids are B0..B7 in this order.
BANDS = [
    (1, 10),
    (11, 50),
    (51, 100),
    (101, 250),
    (251, 500),
    (501, 1000),
    (1001, 5000),
    (5001, None),
]
BAND_IDS = ["B%d" % i for i in range(len(BANDS))]


def tokenize(text):
    """Return the token list for a document text (frozen rule)."""
    return TOKEN_RE.findall(text.lower())


def band_index(token_count):
    """Band index for a token count, or None if the count is 0.

    Documents with zero tokens fall in no band. Both arms use this
    function, so they agree on the exclusion.
    """
    if token_count <= 0:
        return None
    for i, (low, high) in enumerate(BANDS):
        if low <= token_count and (high is None or token_count <= high):
            return i
    return None  # unreachable for counts >= 1


def band_line(band_i, doc_count, total_tokens):
    """Canonical Job 2 output line for one band (frozen format)."""
    low, high = BANDS[band_i]
    high_s = "inf" if high is None else str(high)
    mean = (total_tokens / doc_count) if doc_count else 0.0
    return "%s\t%d\t%s\t%d\t%d\t%.6f" % (
        BAND_IDS[band_i],
        low,
        high_s,
        doc_count,
        total_tokens,
        mean,
    )


def parse_doc_line(line):
    """Parse one document file line into (docid:int, text:str)."""
    docid_s, text = line.rstrip("\n").split("\t", 1)
    return int(docid_s), text


def canonical_sha256(lines):
    """SHA-256 of output lines sorted bytewise, per the frozen
    correctness rule (LC_ALL=C sort order)."""
    import hashlib

    h = hashlib.sha256()
    for line in sorted(lines, key=lambda s: s.encode("utf-8")):
        h.update(line.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()
