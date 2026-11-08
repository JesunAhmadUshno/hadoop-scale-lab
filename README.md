# Hadoop Scale Lab

Where does Hadoop MapReduce on HDFS actually stand against a tuned
single-node baseline for document analytics, and what do shuffle,
replication, and the small-file effect cost? A pre-registered scale
study, measured on one named machine, verdicts published either way.

## Status: pre-registered and built; awaiting timed runs

The study is locked in PREREGISTRATION.md (the first content commit
in this repository) and the full harness is built and
correctness-tested. No timed cell has been run yet: the machine of
record, the Dell R610, does not yet accept this programme's SSH key,
so Phase 2 (the measured runs) has not started. RESULTS.md carries
the honest awaiting-runs state. No number in this repository comes
from any other machine; development machines were used for
correctness smoke tests only.

## Problem

"Just use a laptop script" and "you need a cluster" are both common
advice for batch document processing, usually given without numbers.
Hadoop MapReduce carries real fixed costs (JVM and container
startup, shuffle, HDFS replication, NameNode metadata per file) and
real scale benefits. For a small team digitizing documents, the
honest questions are quantitative: at what input size does the
distributed system catch up to a well-tuned single node, if it ever
does inside a realistic range, and what do replication and many
small files cost on the way?

## Research question and hypotheses

RQ: for document analytics at small-team scale, where does Hadoop
MapReduce on HDFS stand against a tuned single-node baseline: at
what scale does it catch up or win, and what do shuffle,
replication, and the small-file effect cost?

- H1, scale crossover: the MapReduce-to-baseline wall-time ratio
  for the inverted-index job at 5 GiB is at most 1.0, or at most
  half its 0.1 GiB value.
- H2, small-file effect: at 1 GiB, storing the corpus as roughly
  1 MiB files instead of roughly 128 MiB files costs at least
  15 percent of job wall time.
- H3, replication cost: at 5 GiB, replication factor 3 versus 1
  costs at least 15 percent on ingest write time and at least
  5 percent on job wall time.
- H4 (optional arm): Spark on YARN beats MapReduce wall time by at
  least 30 percent at 5 GiB.

Every hypothesis has a frozen numeric pass line and a
CONFIRMED / REFUTED / INCONCLUSIVE rule in PREREGISTRATION.md.

## Design in one paragraph

Corpus: the English Wikisource full-articles dump of 2026-11-01,
one file, MD5 verified against the publisher's checksum file
(DECISIONS.md D1 explains why it is not the Wikipedia abstracts
dump: Wikimedia no longer publishes one). Nested subsets of
0.1, 1, and 5 GiB of extracted text. Two jobs, both in Python:
an inverted index with term statistics (Hadoop Streaming on the
cluster arm, Spark in the optional arm) and a document-length-band
aggregation. The baseline is a single process on the same host:
the same tokenizer code path, aggregation in DuckDB. The cluster
is Hadoop 3.3.6 in Docker Compose (one NameNode, three DataNodes,
one ResourceManager, one NodeManager), capped at 8 CPUs and
24 GiB in aggregate so the host's other duties are never squeezed.
Correctness gates timing: every run's output must hash identically
to the baseline's, byte for byte after canonical sorting, before
its time counts. Three timed runs per cell, medians reported,
counters (shuffle bytes, HDFS bytes read and written) recorded per
run.

## Why this matters beyond the lab

Batch document processing is the backbone of bank and
public-sector document digitization: archives, case files, forms,
and historical records all move through exactly this kind of
pipeline. Knowing the real scale limits of the boring, owned
option (one decent server, free software) against rented or
clustered scale helps small teams choose cheap, boring
infrastructure with evidence instead of fashion, and tells them
the point at which the cluster genuinely starts paying for
itself.

## Layout

- PREREGISTRATION.md: the locked study design.
- DECISIONS.md: deviations and interpretation notes, dated.
- src/common.py: the shared tokenizer, bands, and canonical hash.
- src/build_corpus.py: dump to document file and nested subsets.
- src/baseline.py: the DuckDB single-node baseline.
- jobs/: the Hadoop Streaming mappers, combiners, reducers.
- spark/: the optional H4 arm.
- docker-compose.yml and docker/: the capped Hadoop cluster.
- scripts/fetch_corpus.sh: download and checksum verification.
- scripts/run_study.py: the Phase 2 driver (runs on the R610).
- scripts/make_results.py: RESULTS.md generated from raw runs.
- tests/: tokenizer, stripper, corpus builder, and the
  pipe-vs-baseline byte-equivalence suite.
- RESULTS.md: verdicts and the raw run table (awaiting runs).
- AUDIT.md: the author's graded audit.

## Reproducing

Phase 1 (anywhere, correctness only):
scripts/fetch_corpus.sh, then python src/build_corpus.py, then
scripts/smoke_local.sh. Phase 2 (the R610 only): python
scripts/run_study.py preflight, prepare, matrix; then python
scripts/make_results.py; then run_study.py teardown removes the
cluster containers and volumes.
