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
