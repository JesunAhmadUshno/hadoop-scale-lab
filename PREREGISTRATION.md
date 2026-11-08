# Pre-registration: Hadoop MapReduce vs a tuned single-node baseline

Locked before any timed run exists. The commit that adds this file
precedes every result in this repository; git history proves the
order. Any change to this file after locking is an amendment and must
be recorded in DECISIONS.md with its reason, before the runs it
affects.

## Research question

For document analytics at small-team scale, where does Hadoop
MapReduce on HDFS actually stand against a tuned single-node baseline:
at what input scale does it catch up or win, and what do shuffle,
replication, and the small-file effect cost?

## Machine of record

All timed runs happen on one named machine: the Dell PowerEdge R610
(Ubuntu 24.04.5, 94 GiB RAM) that hosts the cluster and the baseline.
No timing number from any other machine is ever reported in this
study. Development smoke tests on other machines check correctness
only. The R610 is a shared host (it also runs a Penpot design server,
Cockpit, and an n8n instance); co-tenancy during the runs is recorded
in AUDIT.md, not hidden.

## Corpus

One real public corpus, one downloadable file (see DECISIONS.md D1
for why it is Wikisource and not the Wikipedia abstracts dump, which
Wikimedia no longer publishes):

- enwikisource-20261101-pages-articles.xml.bz2, 3,438,896,364 bytes,
  from https://dumps.wikimedia.org/enwikisource/20261101/
- Published MD5: 4f0f5f9704207360eaa9471fb088acd3
  (enwikisource-20261101-md5sums.txt, same directory)
- SHA-256: recorded in results/corpus_manifest.json at download
  verification, before any timed run.

### Document extraction (frozen)

Documents are pages in namespace 0 that are not redirects, in dump
order. Each page's wikitext passes through the deterministic
stripper in src/build_corpus.py (templates, file and image links,
references, tables, and markup removed by fixed rules; HTML entities
unescaped). Document text is title + one space + stripped body, with
every run of whitespace collapsed to a single space. A page whose
stripped text is empty is dropped. Document ids are sequential
integers in dump order, starting at 1. The extracted document file
has one line per document: docid, a tab, then the text.

### Scale ladder (frozen)

Scale points are cumulative sizes of the extracted document file:
0.1 GiB (107,374,182 bytes), 1 GiB (1,073,741,824 bytes), and 5 GiB
(5,368,709,120 bytes). Subsets are nested prefixes: the subset for a
scale point is the shortest prefix of the document stream whose file
size reaches that point, so the 0.1 GiB subset is contained in the
1 GiB subset, which is contained in the 5 GiB subset. The subset
builder (src/build_corpus.py) writes a manifest with the document
count, exact byte size, and SHA-256 of each subset. If the full
corpus yields less than 5 GiB of extracted text, the top scale point
becomes the full corpus and the ladder is re-anchored by a
DECISIONS.md amendment before any run; no run may precede that
amendment.

### File layouts (frozen)

- Combined layout: the subset split into files of at most 128 MiB,
  filled at document boundaries (a file ends when adding the next
  document would exceed 128 MiB; every file holds at least one
  document).
- Small-file layout (H2 only, at the 1 GiB point): the same bytes
  split into files of at most 1 MiB under the same rule.

## Jobs (frozen)

Both jobs run in Python via Hadoop Streaming on the cluster arm, and
in the baseline arm on the same host. Both arms consume the identical
document files and the identical tokenizer (src/common.py: lowercase
with Python str.lower, tokens are maximal runs of Unicode letters
and digits, regex [^\W_]+).

### Job 1: inverted index with term statistics

For every term, one output line:
term, tab, document frequency, tab, total term frequency, tab,
postings, where postings is a comma-separated list of docid:tf pairs
sorted by docid in ascending numeric order. The MapReduce version
uses a combiner that merges posting chunks per term; the reducer
produces the final sorted postings.

### Job 2: document-length-band aggregation

Bands by token count per document, frozen: B0 1-10, B1 11-50,
B2 51-100, B3 101-250, B4 251-500, B5 501-1000, B6 1001-5000,
B7 5001 and above. For every band, one output line: band id, tab,
band low, tab, band high (the word inf for B7), tab, document count,
tab, total tokens, tab, mean tokens per document formatted with
exactly six decimal places, computed from the integer count and
total in Python by both arms. Bands with zero documents appear with
count 0, total 0, mean 0.000000.

### Baseline (frozen)

The tuned single-node implementation runs on the R610, outside the
cluster, in one process. It tokenizes with the same src/common.py
code path as the Streaming mapper, loads token rows into DuckDB,
and aggregates in DuckDB (group by term for Job 1; group by band for
Job 2, with band assigned by the same frozen boundaries). Postings
assembly and mean formatting happen in Python from DuckDB's integer
outputs, so both arms format bytes identically. DuckDB is configured
with threads equal to the host's online cores and a memory limit of
32 GiB. The timed region for the baseline is the whole baseline
process: read documents from local disk, tokenize, aggregate, write
the output file.

### Cluster (frozen)

Hadoop 3.3.6 (image apache/hadoop:3.3.6, amd64 digest recorded in
docker-compose.yml) as a Docker Compose pseudo-distributed cluster,
project name hadoop-scale-lab: one NameNode, three DataNodes, one
ResourceManager, one NodeManager, one client container. Aggregate
caps across all cluster containers: at most 8 CPUs and 24 GiB.
HDFS block size 128 MiB. MapReduce job configuration is frozen in
the run scripts (4 reducers for both jobs; map memory 1024 MiB,
reduce memory 2048 MiB). Output replication for jobs is 1 in every
cell; the replication under test in H3 applies to the ingested
input directories.

## Hypotheses (frozen, with pass lines)

Verdict vocabulary: CONFIRMED, REFUTED, INCONCLUSIVE, and NOT TESTED
for the optional arm only. R(job, scale) is the wall-time ratio
MapReduce divided by baseline, each the median of the timed runs in
that cell.

### H1: scale crossover

Scored on Job 1. CONFIRMED if R(Job 1, 5 GiB) is at most 1.0
(MapReduce catches up or wins at the top of the ladder), or if
R(Job 1, 5 GiB) is at most half of R(Job 1, 0.1 GiB) (the gap at
least halves across the ladder). REFUTED if R(Job 1, 5 GiB) is
greater than or equal to R(Job 1, 0.1 GiB) (the gap does not narrow
at all). INCONCLUSIVE otherwise.

### H2: small-file effect

At the 1 GiB point, Job 1, cost = (T_small - T_combined) /
T_combined x 100 percent, where T is the median wall time under
each layout at equal total bytes. CONFIRMED if cost is at least
15 percent. REFUTED if cost is at most 5 percent. INCONCLUSIVE
between. File counts for both layouts are reported with the result.

### H3: replication cost

At the 5 GiB point. The subset is ingested twice per replication
factor (1 and 3); the first ingest is a path warm-up (logged, not
timed), the second is timed: W(rf). Job 1 then runs under each
replication factor: T(rf), median wall time. CONFIRMED if the
write penalty (W(3) - W(1)) / W(1) is at least 15 percent AND the
job penalty (T(3) - T(1)) / T(1) is at least 5 percent. REFUTED if
both penalties are below 5 percent. INCONCLUSIVE otherwise.

### H4 (optional arm): Spark on YARN

Only if it does not delay H1 to H3. Spark 3.5.3 on YARN (client
mode, same cluster, same caps) runs Job 1 at 5 GiB with the same
correctness rule. CONFIRMED if the Spark median wall time is at
most 0.70 times the MapReduce median wall time (beats it by at
least 30 percent). REFUTED if the Spark median is greater than or
equal to the MapReduce median. INCONCLUSIVE between. If the arm is
not run, H4 is reported as NOT TESTED with the reason.

## Measurement protocol (frozen)

- Cells: for each job, each scale point (0.1, 1, 5 GiB) on both
  arms; plus the H2 layout cell, the H3 replication cells, and the
  optional H4 cell.
- Every cell gets one untimed warm-up execution of the job at that
  scale (its output checksum is still verified), then exactly three
  timed runs. The reported time is the median; every run appears in
  the raw run table in RESULTS.md and results/raw_runs.jsonl.
- Wall time for MapReduce is the wall clock of the streaming
  command on the client container, submit to completion. Wall time
  for the baseline is the wall clock of the baseline process. Both
  include reading that arm's input store and writing the final
  output. One-time ingest (local disk to HDFS) is not part of job
  wall time; it is measured separately under H3.
- Correctness before timing, always: the SHA-256 of each run's
  canonical output (all output lines sorted bytewise, LC_ALL=C)
  must equal the baseline's canonical SHA-256 for the same job and
  scale exactly. A cell whose checksums differ is void: none of
  its times count, the void is logged in RESULTS.md and the run
  scripts' log, and the cell is re-run after diagnosis.
- Counters recorded for every MapReduce run, from the job counters:
  Reduce shuffle bytes; HDFS bytes read; HDFS bytes written; and
  the number of input files and HDFS blocks for the cell's input
  directory.
- No number is reported from fewer than the registered runs, and
  no number is reported from any machine other than the machine of
  record.
