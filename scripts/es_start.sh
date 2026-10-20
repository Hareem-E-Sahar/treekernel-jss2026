#!/usr/bin/env bash
# Starts the BM25 Elasticsearch node (localhost:9201, 2 GB heap) in the foreground.
cd "$(dirname "$0")/.."
export ES_PATH_CONF=$PWD/third_party/es/config ES_JAVA_OPTS="-Xms2g -Xmx2g"
exec /home/hareem/treekernel_revision_Oct2026/elasticsearch-8.19.15-linux-x86_64/elasticsearch-8.19.15/bin/elasticsearch
