#!/usr/bin/env bash
set -Eeuo pipefail

# Keep host bind files owner-only. The official entrypoint drops to mongodb
# before reading bootstrap secrets, so copy only its inputs into private tmpfs.
test "$(stat -f -c %T /run/shipsense)" = tmpfs
for input in /run/secrets/mongo-root.txt /run/secrets/mongo-app.json; do
  test -f "$input" && test -s "$input" && test -r "$input"
done
[[ $(< /run/secrets/mongo-root.txt) =~ ^[a-zA-Z0-9]{64}$ ]]
jq -e 'type == "object" and keys == ["pwd", "user"] and .user == "shipsense_fixture" and (.pwd | type == "string" and test("^[a-zA-Z0-9]{32,128}$"))' /run/secrets/mongo-app.json >/dev/null 2>&1
install -d -m 0700 -o mongodb -g mongodb /run/shipsense
install -m 0600 -o mongodb -g mongodb /run/secrets/mongo-root.txt /run/shipsense/mongo-root.txt
install -m 0600 -o mongodb -g mongodb /run/secrets/mongo-app.json /run/shipsense/mongo-app.json
export MONGO_INITDB_ROOT_PASSWORD_FILE=/run/shipsense/mongo-root.txt
exec /usr/local/bin/docker-entrypoint.sh "$@"
