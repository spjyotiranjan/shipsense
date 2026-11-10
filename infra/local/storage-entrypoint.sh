#!/bin/sh
set -eu

# Only the host-validated scoped fixture identity may cross this boundary.
# A digest is not a credential transport; raw identity values stay in files.
test "$(stat -f -c %T /run/shipsense)" = tmpfs
id seaweed >/dev/null 2>&1
test -f /run/secrets/s3.json && test -s /run/secrets/s3.json && test -r /run/secrets/s3.json
test "$(stat -c %s /run/secrets/s3.json)" -le 16384
test "${#SHIPSENSE_S3_CONFIG_SHA256}" -eq 64
case "$SHIPSENSE_S3_CONFIG_SHA256" in *[!a-f0-9]*) exit 1 ;; esac
printf '%s  %s\n' "$SHIPSENSE_S3_CONFIG_SHA256" /run/secrets/s3.json | sha256sum -c -s
install -d -m 0700 -o seaweed -g seaweed /run/shipsense
install -m 0600 -o seaweed -g seaweed /run/secrets/s3.json /run/shipsense/s3.json
printf '%s  %s\n' "$SHIPSENSE_S3_CONFIG_SHA256" /run/shipsense/s3.json | sha256sum -c -s
unset SHIPSENSE_S3_CONFIG_SHA256
exec /entrypoint.sh "$@"
