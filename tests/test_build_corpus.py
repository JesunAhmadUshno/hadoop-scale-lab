import bz2
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from build_corpus import build

XML = """<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">
<page><title>Alpha</title><ns>0</ns><id>1</id>
<revision><text xml:space="preserve">'''Alpha''' is a [[Letter|letter]] used {{fact}} widely.</text></revision></page>
<page><title>Beta</title><ns>0</ns><id>2</id><redirect title="Alpha"/>
<revision><text xml:space="preserve">#REDIRECT [[Alpha]]</text></revision></page>
<page><title>Project:About</title><ns>4</ns><id>3</id>
<revision><text xml:space="preserve">Not a document.</text></revision></page>
<page><title>Gamma</title><ns>0</ns><id>4</id>
<revision><text xml:space="preserve">Gamma rays &amp; other text here.</text></revision></page>
</mediawiki>
"""


def test_build_filters_and_nesting(tmp_path):
    src = tmp_path / "dump.xml.bz2"
    with bz2.open(src, "wt", encoding="utf-8") as f:
        f.write(XML)
    outdir = tmp_path / "out"
    manifest = build(str(src), str(outdir), targets=[10, 60])
    assert manifest["documents"] == 2
    assert manifest["skipped"]["redirects"] == 1
    assert manifest["skipped"]["non_namespace_0"] == 1
    docs = (outdir / "docs.tsv").read_text(encoding="utf-8")
    lines = docs.splitlines()
    assert lines[0].startswith("1\tAlpha Alpha is a letter used widely.")
    assert lines[1].startswith("2\tGamma Gamma rays & other text here.")
    # nested: the smaller subset's docs are a prefix of the larger's
    small = manifest["subsets"]["10"]
    big = manifest["subsets"]["60"]
    assert small["docs"] <= big["docs"] <= 2
    small_bytes = (outdir / small["file"]).read_bytes()
    big_bytes = (outdir / big["file"]).read_bytes()
    assert big_bytes.startswith(small_bytes)
