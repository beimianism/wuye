#!/usr/bin/env bash
set -euo pipefail

env_file="${WUYE_WECHAT_ENV_FILE:-/etc/wuye/wechat.env}"
jar_file="/srv/wuye/source/wuye-b/MicroCommunity-v0.8/service-front/target/service-front.jar"

if [[ ! -r "$env_file" ]]; then
  printf 'Cannot read %s; configure the file and grant read access to the Java application user.\n' "$env_file" >&2
  exit 1
fi
if [[ ! -f "$jar_file" ]]; then
  printf 'Cannot find %s; build the Java project first.\n' "$jar_file" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$env_file"
set +a

exec java -Dfile.encoding=UTF-8 -jar "$jar_file" --spring.profiles.active=prod --server.address=127.0.0.1
