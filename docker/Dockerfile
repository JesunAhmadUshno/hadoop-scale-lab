# Derived from the pinned upstream image only to guarantee a
# Python 3 interpreter for Hadoop Streaming tasks on the
# NodeManager and the client. Nothing else changes.
FROM apache/hadoop:3.3.6
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/*
