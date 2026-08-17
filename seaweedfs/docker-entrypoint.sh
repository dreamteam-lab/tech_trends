#!/bin/sh
# Генерирует s3-config.json из шаблона, подставляя access/secret key
# из переменных окружения (значения приходят из .env, в Git не попадают),
# и запускает SeaweedFS в standalone-режиме "server" (master + volume + filer + S3 API
# в одном процессе) — этого достаточно для MVP.
set -eu

: "${SEAWEEDFS_ACCESS_KEY:?SEAWEEDFS_ACCESS_KEY is required (см. .env.example)}"
: "${SEAWEEDFS_SECRET_KEY:?SEAWEEDFS_SECRET_KEY is required (см. .env.example)}"

CONFIG_TEMPLATE=/etc/seaweedfs/s3-config.json.template
CONFIG_OUT=/etc/seaweedfs/s3-config.json

sed \
  -e "s|__SEAWEEDFS_ACCESS_KEY__|${SEAWEEDFS_ACCESS_KEY}|g" \
  -e "s|__SEAWEEDFS_SECRET_KEY__|${SEAWEEDFS_SECRET_KEY}|g" \
  "$CONFIG_TEMPLATE" > "$CONFIG_OUT"

exec weed server \
  -dir=/data \
  -master.volumeSizeLimitMB=1024 \
  -volume.max=0 \
  -ip=seaweedfs \
  -s3 \
  -s3.port=8333 \
  -s3.config="$CONFIG_OUT"
