"""End-to-end correctness: the Streaming jobs run through a local
pipe (mapper | sort | combiner | sort | reducer) must produce the
same canonical output as the DuckDB baseline, on the same documents.
This is the correctness half of the frozen checksum rule, exercised
without a cluster.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from common import BAND_IDS, band_line, canonical_sha256  # noqa: E402

DOCS = [
    (1, "the quick brown fox jumps over the lazy dog"),
    (2, "the dog barks and the fox runs"),
    (3, "Café society café CAFÉ"),
    (4, "a"),
    (5, " ".join("word%d" % (i % 37) for i in range(300))),
    (6, "!!! --- ..."),
]


def _write_docs(tmp_path):
    p = tmp_path / "docs.tsv"
    with open(p, "w", encoding="utf-8") as f:
        for docid, text in DOCS:
            f.write("%d\t%s\n" % (docid, text))
    return str(p)


def _pipe(docs_path, scripts):
    data = open(docs_path, "rb").read()
    env = {**os.environ, "LC_ALL": "C"}
    for script in scripts:
        if script == "SORT":
            cmd = ["sort"]
        else:
            cmd = [sys.executable, os.path.join(ROOT, "jobs", script)]
        r = subprocess.run(cmd, input=data, capture_output=True, env=env)
        assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
        data = r.stdout
    return [ln for ln in data.decode("utf-8").splitlines() if ln]


def _baseline(tmp_path, docs_path, job):
    out = str(tmp_path / ("baseline_%s.txt" % job))
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "src", "baseline.py"),
         "--job", job, "--input", docs_path, "--output", out],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    with open(out, encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f if ln.strip()]


def test_inverted_index_equivalence(tmp_path):
    docs = _write_docs(tmp_path)
    mr = _pipe(docs, ["ii_mapper.py", "SORT", "ii_combiner.py", "SORT",
                      "ii_reducer.py"])
    base = _baseline(tmp_path, docs, "ii")
    assert canonical_sha256(mr) == canonical_sha256(base)
    # spot check: 'the' appears in docs 1 and 2, tf 2 and 2
    the_line = [ln for ln in base if ln.startswith("the\t")][0]
    assert the_line == "the\t2\t4\t1:2,2:2"


def test_bands_equivalence(tmp_path):
    docs = _write_docs(tmp_path)
    mr = _pipe(docs, ["bands_mapper.py", "SORT", "bands_combiner.py",
                      "SORT", "bands_reducer.py"])
    present = {ln.split("\t", 1)[0] for ln in mr}
    for i, bid in enumerate(BAND_IDS):
        if bid not in present:
            mr.append(band_line(i, 0, 0))
    base = _baseline(tmp_path, docs, "bands")
    assert canonical_sha256(mr) == canonical_sha256(base)
    assert len(base) == 8
