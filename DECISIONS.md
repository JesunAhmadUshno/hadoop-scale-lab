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

## D3. DuckDB version on the machine of record: 1.4.3, not 2.0.0

Recorded during Phase 2 setup, before any timed run. The machine
of record's CPUs (Intel Xeon E5540) have SSE4.2 but no AVX. The
pinned duckdb 2.0.0 wheel (requirements-lock.txt) faults with an
illegal instruction on import there; it runs on the development
machine, which has AVX2. Tested on the R610 on 2026-11-09: every
DuckDB wheel from 0.10.3 through 1.4.3 imports and queries
correctly. The baseline therefore runs DuckDB 1.4.3 on the machine
of record (the newest tested version; it also satisfies
requirements.txt, duckdb>=1.3). Nothing frozen changes: the
baseline's algorithm, tokenizer, thread count (host online cores),
and 32 GiB memory limit are exactly as registered, and correctness
does not rest on the version: the driver's checksum void rule
compares every run against the baseline on the same host, and the
repository's pipe-vs-baseline byte-equivalence suite passes on
the R610 under 1.4.3 (16 of 16 tests). CI keeps the locked 2.0.0
on AVX2-capable runners. This is an environment substitution,
disclosed here and in AUDIT.md, not a protocol change.

## D4. Derived cluster image: yum from vault.centos.org, Python 3.6.8

Recorded during Phase 2 setup, before any timed run. The Phase 1
Dockerfile assumed the pinned apache/hadoop:3.3.6 image was
Debian based and used apt-get; the image is in fact CentOS 7
based, has no apt, and ships only Python 2.7. The first Phase 2
preflight build failed on exactly that (apt-get: exit 127). The
Dockerfile now does the same job with the image's own package
manager: CentOS 7 is end of life and mirror.centos.org is
retired, so the repo files are pointed at vault.centos.org, then
yum installs python3 (3.6.8) and the yum cache is cleaned. The
image's purpose is unchanged (Hadoop 3.3.6 plus a Python 3 for
Streaming tasks), and the install was verified interactively on
the machine of record before the Dockerfile was changed.
Consequence, disclosed: Streaming tasks run Python 3.6.8 while
the baseline runs the host's Python 3.12. Tokenization is the
shared src/common.py in both arms, but the Unicode database
differs between those Pythons, so a tokenizer divergence on
rare codepoints is possible in principle. The frozen checksum
void rule is the guard: every run's output, warm-ups included,
must hash identically to the baseline's or the cell is void,
so any such divergence stops the study loudly instead of
contaminating a number.

## D5. capacity-scheduler.xml added to the mounted conf directory

Recorded during Phase 2 setup, before any timed run. The Compose
stack mounts docker/conf over the image's /opt/hadoop/etc/hadoop,
which shadows every file the image ships there, including
capacity-scheduler.xml. Without it the ResourceManager exited
with "Queue configuration missing child queue names for root"
(first Phase 2 preflight, 2026-11-09). The fix adds the stock
Hadoop 3.3.6 capacity-scheduler.xml (root with a single default
queue at capacity 100) to docker/conf. No scheduler behaviour
beyond the upstream default is introduced. Also recorded:
run_study.py's preflight health check covers HDFS only (safe
mode and live DataNodes); the dead ResourceManager was found by
inspecting container state, and YARN health is verified
explicitly (yarn node -list) before the matrix starts.

## D6. Scale ladder re-anchored: the top point is the full corpus

Recorded during Phase 2 setup, before any timed run, under the
re-anchoring rule PREREGISTRATION.md itself freezes for exactly
this case. The full extraction pass over the verified dump
completed on the machine of record on 2026-11-09: the entire
corpus yields 1,984,437,310 bytes of extracted text (648,182
documents; data/extraction_manifest.json, docs SHA-256
f3f42c2e73f34053676683d2d7bc722df50bf7e8a7ab006de5e6e13fe30d0faa),
which is less than the 5 GiB top target (targets_not_reached:
5GiB, in the builder's own manifest). The ladder is therefore
re-anchored as the pre-registration prescribes: the top scale
point becomes the full corpus, labelled "full" in the run logs
and results (1,984,437,310 bytes, about 1.85 GiB). The ladder is
0.1 GiB, 1 GiB, full. Every hypothesis reads unchanged except
that "5 GiB" now denotes the top point: H1 compares R(full)
against R(0.1 GiB) with the same pass lines, H3 runs its
replication cells at the top point, and H4 runs Spark there.
The two scripts that name scale points (scripts/run_study.py,
scripts/make_results.py) were patched to the "full" label in
the same commit as this amendment; no threshold, run count, or
verdict rule changed. data/docs_full.tsv is a byte copy of the
full extracted stream (data/docs.tsv).

## D7. mapred-site.xml: HADOOP_MAPRED_HOME env for the AppMaster

Recorded during Phase 2, before any MapReduce run completed (the
four baseline rows already in results/raw_runs.jsonl are
unaffected: the baseline reads no Hadoop configuration). The
first MapReduce submission failed at application launch: "Could
not find or load main class
org.apache.hadoop.mapreduce.v2.app.MRAppMaster". The job's own
diagnostic prescribes setting HADOOP_MAPRED_HOME in the
AppMaster, map, and reduce environments; with the study's conf
directory mounted over the image's, that setting is absent.
docker/conf/mapred-site.xml now sets yarn.app.mapreduce.am.env,
mapreduce.map.env, and mapreduce.reduce.env to
HADOOP_MAPRED_HOME=/opt/hadoop, exactly as the error prescribes.
No job parameter frozen in PREREGISTRATION.md changes (the
reducer count and memory settings were already present).

## D8. Streaming tasks get PYTHONPATH=. via -cmdenv

Recorded during Phase 2, before any MapReduce run completed.
The first cluster attempts failed in every map task with
"ModuleNotFoundError: No module named '_bootstrap'", even though
_bootstrap.py was present in the task working directory (proven
by a diagnostic streaming job that listed its own directory).
Root cause: YARN localizes each -files entry as a symlink into
its own filecache directory, and Python sets sys.path[0] to the
resolved script directory (that filecache dir, holding only the
one script), while the task working directory is not on
sys.path at all. The driver now passes -cmdenv PYTHONPATH=. to
the streaming job, putting the task working directory (which
holds _bootstrap.py and common.py) on the import path. Path
setup only: no job code, algorithm, or parameter changes.
Because the harness changed, the matrix restarts with a clean
run log; the four baseline rows logged before this fix (Job 1
at 0.1 GiB, 49.8 to 50.3 s) are discarded with the log and
re-measured under the final harness, so every cell's median
rests on exactly the registered three timed runs.

## D9. Streaming tasks get PYTHONIOENCODING=utf-8; counters parsed from stdout

Recorded during Phase 2, after the first MapReduce cells ran and
were voided by the frozen checksum rule, before any MapReduce
cell passed the gate. Evidence: the 0.1 GiB inverted-index cell
produced a self-consistent but wrong output (identical SHA-256
across its runs, different from the baseline). A sorted diff
showed 8,806 lines present only in the baseline, every sampled
one containing a non-ASCII token (10½, 10월, 1949年), and 3,983
lines present only in the MapReduce output, every sampled one
pure ASCII with shifted postings: the tasks were splitting
non-ASCII tokens into ASCII fragments. Root cause: the image's
Python 3.6 under the C locale decodes standard input as ASCII
with surrogateescape; the baseline reads UTF-8. The driver now
also passes -cmdenv PYTHONIOENCODING=utf-8. Tokenizer code is
unchanged; this aligns the task stream encoding with the
baseline's documented UTF-8 read. In the same pass, counter
parsing moved to the client's combined stdout and stderr: the
Hadoop 3.3.6 client prints its counter table to stdout, so the
first cells logged null counters. Counters are report colour
only; no hypothesis reads them. Because the harness changed
again, the matrix restarts with a clean run log and every cell
is re-measured under the final harness (the voided cells were
excluded by the frozen rule in any case).

## D10. The small-file cell (H2) is stopped unmeasured; the rest of the matrix completes

Recorded during Phase 2, at the moment of the stop, before the
H3 block ran. The H2 cell (Job 1, 1 GiB, small layout: 1,055
files, one map task per file) proved impractical to measure
under the frozen configuration on this cluster. Observed
evidence from the warm-up run alone (application
application_1794184489553_0034): progress readings of 13.25,
22.79, 28.77, and 36.6 percent across roughly two hours; the
AppMaster logged completedMapPercent 0.4654 after about two
hours; total map slot time at that point was 57,501,912 ms,
about 117 seconds of slot time per completed map on a mean
input of about 1 MiB; at the stop, at least 640 of 1,055 maps
had completed and the job was still in its warm-up run after
more than 2.5 hours. The mechanism is fixed per-task launch
and scheduling cost under the frozen caps (9 vCores allocated
against 3 configured on the single NodeManager), which is the
small-file phenomenon itself, but at this magnitude the cell's
remaining three timed runs projected past 20 additional hours
on a shared production machine. The operator stopped the cell
(driver and application killed, state verified). The run log
carries a void_cell row for it in the driver's own format, and
H2 is reported NOT MEASURED: the partial counters are recorded
here as observations and are never used as an H2 verdict or as
a substitute median. The H3 block (replication at the top
scale point) runs immediately after this entry, executed
through the driver's own ingest and timed-cell functions with
the same arguments matrix() passes.

## D11. Spark arm: spark-submit is called by absolute path

Recorded during Phase 2, before any Spark run completed (the
four first invocations exited 1 and logged nothing). The
spark-client container (apache/spark:3.5.3) keeps Spark at
/opt/spark/bin, but that directory is added to PATH only by the
image entrypoint's shell setup, which docker exec sessions do
not inherit, so the driver's bare "spark-submit" was not found.
The driver now calls /opt/spark/bin/spark-submit. Path only;
the Spark job, its arguments, and the H4 comparison are
unchanged.

## D12. The R610 working copy's mounted trees are world-readable

Recorded during Phase 2, before any Spark run completed. The
first Spark submissions failed instantly: python3 could not
open /work/spark/inverted_index_spark.py (Errno 13). The repo
files on the R610 are mode 660 under brimwood's group (the
modes the transfer preserved), while the apache/spark image
runs as uid 185, outside that group; the Hadoop containers run
as root, which is why MapReduce never noticed. The mounted
source trees in the R610 working copy only (jobs, src, spark,
docker/conf) were made world-readable (a+rX). No file content
changed, and the Git-tracked modes in the repository are
untouched.

## D13. Spark executors get a standalone CPython 3.8.19 via the distributed cache

Recorded during Phase 2, before any Spark run completed. With
D11 and D12 fixed, the Spark job started and then lost every
task: PySparkRuntimeError PYTHON_VERSION_MISMATCH, "Python in
worker has different version (3, 6) than that in driver 3.8".
The driver runs in the spark image (Python 3.8); the executors
run in the Hadoop image (Python 3.6.8, DECISIONS.md D4), and
PySpark 3.5 refuses mixed minor versions. Provisioning step on
the machine of record: cpython-3.8.19+20240415
x86_64-unknown-linux-gnu-install_only.tar.gz from
python-build-standalone (release 20240415), SHA-256
b33feb5ce0d7f9c4aca8621a9d231dfd9d2f6e26eccb56b63f07041ff573d5a5,
verified running inside the NodeManager container before use.
The tarball lives only in the R610 working copy at
spark/pbs38.tar.gz (it is not committed to the repository); the
driver ships it to executors with spark.yarn.dist.archives and
points spark.pyspark.python at it. Executor interpreter
provisioning only: the Spark job code, its input, and the H4
comparison against MapReduce are unchanged.

## D13 addendum. The driver interpreter is pinned separately

The first D13 submission failed in the driver: spark.pyspark
.python is the fallback for the driver-side interpreter too,
so the driver tried to run the executor-relative archive path.
spark.pyspark.driver.python is now pinned to the spark image's
own /usr/bin/python3 (3.8), leaving the archive path to
the workers only.

## D13 addendum 2. The worker path is python/python/bin/python3.8

The distributed-cache fragment (#python) names the directory
the archive unpacks into; the tarball itself also has a
top-level python/ directory, so the interpreter lands at
python/python/bin/python3.8 relative to the container working
directory. Both worker settings now use that path.

## D13 addendum 3. The shared tokenizer module ships with the Spark job

The workers then failed with ModuleNotFoundError: No module
named 'common': the job imports tokenize from src/common.py on
the driver, and its closures reference the module by name, so
the executors need the module itself. The submission now also
passes --py-files /work/src/common.py. The job file is
unchanged.
