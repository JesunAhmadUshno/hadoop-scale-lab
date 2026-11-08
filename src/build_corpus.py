"""Build the document file and nested scale subsets from the
Wikisource dump.

Extraction rules are frozen in PREREGISTRATION.md. The stripper here
is deliberately mechanical: it does not try to render wikitext, it
applies fixed removals in a fixed order so the output is a pure
function of the dump bytes.

Usage:
  python src/build_corpus.py --input data/raw/<dump>.xml.bz2 \
      --outdir data/ [--max-docs N] [--targets 107374182,1073741824,5368709120]
"""

import argparse
import bz2
import hashlib
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

# Frozen scale targets in bytes (0.1, 1, 5 GiB of extracted text).
DEFAULT_TARGETS = [107374182, 1073741824, 5368709120]
TARGET_NAMES = ["0.1GiB", "1GiB", "5GiB"]

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
_REF_RE = re.compile(r"<ref[^>]*>.*?</ref\s*>|<ref[^>]*/>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_HEADING_RE = re.compile(r"^(={1,6})\s*(.*?)\s*\1\s*$", re.M)
_LIST_MARK_RE = re.compile(r"^([*#;:]+)\s*", re.M)
_MAGIC_RE = re.compile(r"__[A-Z][A-Z0-9]*__")
_EXT_LINK_TEXT_RE = re.compile(r"\[(?:https?://|ftp://)\S+\s+([^\]]*)\]")
_EXT_LINK_BARE_RE = re.compile(r"\[(?:https?://|ftp://)\S+\]")
_BARE_URL_RE = re.compile(r"(?:https?://|ftp://)\S+")
_WS_RE = re.compile(r"\s+")


def _remove_nested(text, open_tok, close_tok):
    """Remove spans delimited by open_tok/close_tok with nesting."""
    out = []
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        if text.startswith(open_tok, i):
            depth += 1
            i += len(open_tok)
        elif depth > 0 and text.startswith(close_tok, i):
            depth -= 1
            i += len(close_tok)
        else:
            if depth == 0:
                out.append(text[i])
            i += 1
    return "".join(out)


def _rewrite_links(text):
    """[[File:...]]/[[Image:...]]/[[Category:...]] are removed whole;
    other wiki links become their display text. Scans [[ ... ]] spans
    with nesting depth 1 handling."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("[[", i):
            end = text.find("]]", i + 2)
            if end == -1:
                out.append(text[i:])
                break
            inner = text[i + 2 : end]
            head = inner.split("|", 1)[0].strip().lower()
            if head.startswith(("file:", "image:", "category:", "media:")):
                pass  # drop the whole link
            elif "|" in inner:
                out.append(inner.split("|", 1)[1])
            else:
                out.append(inner)
            i = end + 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def strip_wikitext(wikitext):
    """Deterministic wikitext to plain text (frozen rule order)."""
    t = wikitext
    t = _HTML_COMMENT_RE.sub(" ", t)
    t = _REF_RE.sub(" ", t)
    t = _remove_nested(t, "{{", "}}")          # templates
    t = _remove_nested(t, "{|", "|}")          # tables
    t = _rewrite_links(t)
    t = _EXT_LINK_TEXT_RE.sub(r"\1", t)
    t = _EXT_LINK_BARE_RE.sub(" ", t)
    t = _BARE_URL_RE.sub(" ", t)
    t = _TAG_RE.sub(" ", t)
    t = t.replace("'''", "").replace("''", "")
    t = _HEADING_RE.sub(r"\2", t)
    t = _LIST_MARK_RE.sub("", t)
    t = _MAGIC_RE.sub(" ", t)
    t = html.unescape(t)
    t = _WS_RE.sub(" ", t)
    return t.strip()


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def iter_pages(source):
    """Yield (title, ns, is_redirect, wikitext) per page, streaming."""
    context = ET.iterparse(source, events=("end",))
    for _event, elem in context:
        if _local(elem.tag) != "page":
            continue
        title = ""
        ns = ""
        is_redirect = False
        wikitext = None
        for child in elem:
            name = _local(child.tag)
            if name == "title":
                title = child.text or ""
            elif name == "ns":
                ns = child.text or ""
            elif name == "redirect":
                is_redirect = True
            elif name == "revision":
                for sub in child:
                    if _local(sub.tag) == "text":
                        wikitext = sub.text or ""
        yield title, ns, is_redirect, wikitext
        elem.clear()


def build(input_path, outdir, max_docs=None, targets=None):
    targets = list(targets) if targets else list(DEFAULT_TARGETS)
    os.makedirs(outdir, exist_ok=True)
    docs_path = os.path.join(outdir, "docs.tsv")
    sha_docs = hashlib.sha256()
    subset_at = {}  # target -> (doc_count_at_crossing)
    total_bytes = 0
    doc_count = 0
    skipped_ns = 0
    skipped_redirect = 0
    skipped_empty = 0

    with bz2.open(input_path, "rb") as source, open(docs_path, "wb") as out:
        for title, ns, is_redirect, wikitext in iter_pages(source):
            if ns != "0":
                skipped_ns += 1
                continue
            if is_redirect:
                skipped_redirect += 1
                continue
            if wikitext is None:
                skipped_empty += 1
                continue
            text = strip_wikitext(title + " " + wikitext)
            if not text:
                skipped_empty += 1
                continue
            doc_count += 1
            line = ("%d\t%s\n" % (doc_count, text)).encode("utf-8")
            out.write(line)
            sha_docs.update(line)
            total_bytes += len(line)
            for tgt in targets:
                if tgt not in subset_at and total_bytes >= tgt:
                    subset_at[tgt] = doc_count
            if max_docs and doc_count >= max_docs:
                break

    # Materialize nested subsets as line prefixes of docs.tsv: the
    # subset for a target is the first subset_at[target] lines.
    subsets = {}
    names = {t: TARGET_NAMES[i] for i, t in enumerate(DEFAULT_TARGETS)}
    if subset_at:
        handles = {}
        hashers = {}
        try:
            for tgt, cnt in sorted(subset_at.items()):
                name = names.get(tgt, str(tgt))
                path = os.path.join(outdir, "docs_%s.tsv" % name)
                handles[tgt] = open(path, "wb")
                hashers[tgt] = hashlib.sha256()
                subsets[name] = {"target_bytes": tgt, "docs": cnt,
                                 "file": os.path.basename(path)}
            max_lines = max(subset_at.values())
            with open(docs_path, "rb") as f:
                for lineno, line in enumerate(f, start=1):
                    for tgt, cnt in subset_at.items():
                        if lineno <= cnt:
                            handles[tgt].write(line)
                            hashers[tgt].update(line)
                    if lineno >= max_lines:
                        break
            for tgt in handles:
                entry = subsets[names.get(tgt, str(tgt))]
                entry["sha256"] = hashers[tgt].hexdigest()
                entry["bytes"] = os.path.getsize(
                    os.path.join(outdir, entry["file"]))
        finally:
            for h in handles.values():
                h.close()

    manifest = {
        "source_file": os.path.basename(input_path),
        "documents": doc_count,
        "docs_file": "docs.tsv",
        "docs_bytes": total_bytes,
        "docs_sha256": sha_docs.hexdigest(),
        "skipped": {
            "non_namespace_0": skipped_ns,
            "redirects": skipped_redirect,
            "empty_after_strip": skipped_empty,
        },
        "subsets": subsets,
        "targets_not_reached": [
            names.get(t, str(t)) for t in targets if t not in subset_at
        ],
    }
    with open(os.path.join(outdir, "extraction_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--max-docs", type=int, default=None)
    ap.add_argument(
        "--targets",
        default=None,
        help="comma-separated byte targets (default: the frozen GiB ladder)",
    )
    args = ap.parse_args(argv)
    targets = (
        [int(x) for x in args.targets.split(",")] if args.targets else None
    )
    manifest = build(args.input, args.outdir, args.max_docs, targets)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
