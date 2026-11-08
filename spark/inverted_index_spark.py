#!/usr/bin/env python3
"""Optional H4 arm: Job 1 (inverted index) in Spark on YARN.

Same tokenizer, same canonical output line as the Streaming job and
the baseline (imports src/common.py, mounted at /work/src). Postings
are assembled per term from the grouped rows, exactly as the
baseline does, so the checksum rule applies unchanged.

Usage (inside the spark-client container):
  spark-submit --master yarn --deploy-mode client \
      /work/spark/inverted_index_spark.py \
      --input hdfs:///data/docs_5GiB_combined \
      --output hdfs:///out/ii_spark_5GiB
The collector in scripts/run_study.py reads the output back and
canonicalizes it.
"""
import argparse
import sys

sys.path.insert(0, "/work/src")

from common import tokenize  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    from pyspark.sql import SparkSession

    spark = SparkSession.builder.appName("hadoop-scale-lab-ii").getOrCreate()
    sc = spark.sparkContext

    def doc_terms(line):
        docid_s, text = line.split("\t", 1)
        docid = int(docid_s)
        from collections import Counter

        for term, tf in Counter(tokenize(text)).items():
            yield term, (docid, tf)

    lines = sc.textFile(args.input)
    postings = lines.flatMap(doc_terms).groupByKey()
    def render(kv):
        term, pairs = kv
        pairs = sorted(pairs)
        df = len(pairs)
        total = sum(tf for _d, tf in pairs)
        body = ",".join("%d:%d" % (d, tf) for d, tf in pairs)
        return "%s\t%d\t%d\t%s" % (term, df, total, body)

    postings.map(render).coalesce(1).saveAsTextFile(args.output)
    spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
