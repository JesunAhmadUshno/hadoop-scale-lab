import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from build_corpus import strip_wikitext


def test_templates_removed():
    assert strip_wikitext("A {{Infobox|x=1}} B") == "A B"


def test_nested_templates_removed():
    assert strip_wikitext("A {{outer|{{inner|y}}}} B") == "A B"


def test_links_become_display_text():
    assert strip_wikitext("See [[Apple|the fruit]] and [[Banana]].") == \
        "See the fruit and Banana."


def test_file_links_removed():
    assert strip_wikitext("X [[File:pic.jpg|thumb|A caption]] Y") == "X Y"


def test_refs_removed():
    assert strip_wikitext("Fact.<ref name='a'>source</ref> Next") == "Fact. Next"


def test_headings_and_emphasis():
    assert strip_wikitext("== Life ==\nHe was '''bold'''.") == "Life He was bold."


def test_entities_unescaped():
    assert strip_wikitext("Fish &amp; Chips") == "Fish & Chips"
