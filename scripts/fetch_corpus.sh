#!/bin/sh
# Fetch the frozen corpus (or verify an existing copy in place),
# check it against the publisher's MD5, record its SHA-256 in
# results/corpus_manifest.json.
#
# Usage: scripts/fetch_corpus.sh [path-to-existing-bz2]
set -eu
cd "$(dirname "$0")/.."

URL="https://dumps.wikimedia.org/enwikisource/20261101/enwikisource-20261101-pages-articles.xml.bz2"
NAME="enwikisource-20261101-pages-articles.xml.bz2"
PUBLISHED_MD5="4f0f5f9704207360eaa9471fb088acd3"
DEST="data/raw/$NAME"

if [ "${1:-}" != "" ]; then
  DEST="$1"
else
  mkdir -p data/raw
  if [ ! -f "$DEST" ]; then
    # -C - resumes a partial file; a plain --retry restarts from
    # zero and cost us one full re-download (see AUDIT.md).
    curl -L -C - --retry 5 --retry-all-errors -o "$DEST" "$URL"
  fi
fi

ACTUAL_MD5=$(md5sum "$DEST" | awk '{print $1}')
if [ "$ACTUAL_MD5" != "$PUBLISHED_MD5" ]; then
  echo "MD5 MISMATCH: got $ACTUAL_MD5, published $PUBLISHED_MD5" >&2
  exit 1
fi
SHA256=$(sha256sum "$DEST" | awk '{print $1}')
BYTES=$(stat -c %s "$DEST")
mkdir -p results
python3 - "$SHA256" "$ACTUAL_MD5" "$BYTES" "$URL" <<'EOF'
import json, sys
sha, md5, nbytes, url = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
path = "results/corpus_manifest.json"
try:
    with open(path) as f:
        m = json.load(f)
except FileNotFoundError:
    m = {}
m["source"] = {
    "url": url,
    "file": "enwikisource-20261101-pages-articles.xml.bz2",
    "bytes": nbytes,
    "md5_published": md5,
    "md5_verified": True,
    "sha256": sha,
}
with open(path, "w") as f:
    json.dump(m, f, indent=2, sort_keys=True)
print("corpus verified:", sha)
EOF
