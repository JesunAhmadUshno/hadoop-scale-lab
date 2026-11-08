# Decisions

## D1. Corpus: English Wikisource articles dump, not Wikipedia abstracts

The brief recommended the Wikipedia abstracts dump subset. That file
no longer exists: https://dumps.wikimedia.org/enwiki/latest/ no longer
lists any abstract file, and the historical URL
enwiki-latest-abstract.xml.gz returns 404 (both verified 2026-11-08).
Under the brief's own fallback rule (another real public corpus, one
downloadable file, checksum recorded, nested subsets), the corpus is
the English Wikisource full-articles dump, run of 2026-11-01:

- File: enwikisource-20261101-pages-articles.xml.bz2, 3,438,896,364
  bytes, downloaded from
  https://dumps.wikimedia.org/enwikisource/20261101/
- Published MD5 (enwikisource-20261101-md5sums.txt):
  4f0f5f9704207360eaa9471fb088acd3
- SHA-256 recorded by us in PREREGISTRATION.md after download
  verification against the published MD5.

Wikisource is real document text (full books, papers, and public
documents), which fits the study's document-analytics framing at least
as well as abstracts: digitized long documents are the actual workload
of the digitization pipelines the README discusses. Deviation and
reason recorded here, before any run, per the charter.

## D2. Zero-token documents in Job 2

A page can survive stripping with non-empty text but zero tokens
(for example, only punctuation). The frozen bands start at 1 token,
so such a document falls in no band. Both arms use the shared
common.band_index, which returns None for a zero count, and both
exclude the document from Job 2 identically; Job 1 is unaffected.
This is an interpretation note on an edge case, not a protocol
change: the shared-code construction makes the arms agree by
construction, which the equivalence tests exercise (fixture doc 6).
