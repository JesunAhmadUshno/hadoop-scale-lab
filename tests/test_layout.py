"""Portfolio standard checks: the lock holds and the required files exist."""
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SHA-256 of PREREGISTRATION.md as committed in d06513e (tag proposal-v1), before any code or run.
LOCKED_SHA256 = "78ff97fcdc382f33f78d1dcfa7c3fc746e146a19bc9ba018dc7f124e584944b9"


def test_preregistration_is_unchanged_since_the_lock():
    with open(os.path.join(ROOT, "PREREGISTRATION.md"), "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == LOCKED_SHA256, \
            "PREREGISTRATION.md changed after its lock; record an amendment in DECISIONS.md instead"


def test_required_files_exist():
    need = ["README.md", "PREREGISTRATION.md", "AUDIT.md", "RESULTS.md", "DECISIONS.md", "CHANGELOG.md",
            "CITATION.cff", "SECURITY.md", "LICENSE", "results/corpus_manifest.json"]
    missing = [p for p in need if not os.path.exists(os.path.join(ROOT, p))]
    assert not missing, "missing: " + ", ".join(missing)


def test_no_public_grade():
    for name in ("README.md", "AUDIT.md", "RESULTS.md"):
        text = open(os.path.join(ROOT, name)).read()
        assert "of 10,000" not in text and "Grade:" not in text, name + " carries a grade; grades are internal"
