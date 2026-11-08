import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common import band_index, band_line, canonical_sha256, tokenize


def test_tokenizer_basic():
    assert tokenize("Hello, World!") == ["hello", "world"]


def test_tokenizer_underscore_is_separator():
    assert tokenize("a_b c__d") == ["a", "b", "c", "d"]


def test_tokenizer_unicode_letters_and_digits():
    assert tokenize("Café 123 naïve") == ["café", "123", "naïve"]


def test_band_boundaries():
    assert band_index(0) is None
    assert band_index(1) == 0
    assert band_index(10) == 0
    assert band_index(11) == 1
    assert band_index(50) == 1
    assert band_index(51) == 2
    assert band_index(5000) == 6
    assert band_index(5001) == 7
    assert band_index(10**9) == 7


def test_band_line_format():
    assert band_line(0, 2, 10) == "B0\t1\t10\t2\t10\t5.000000"
    assert band_line(7, 0, 0) == "B7\t5001\tinf\t0\t0\t0.000000"


def test_canonical_sha_is_order_free():
    a = canonical_sha256(["b\t1", "a\t2"])
    b = canonical_sha256(["a\t2", "b\t1"])
    assert a == b
