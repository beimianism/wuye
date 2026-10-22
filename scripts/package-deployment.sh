#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project_name="$(basename "$project_dir")"
artifact_dir="$project_dir/artifacts"
stamp="$(date +%Y%m%d)"
archive="$artifact_dir/${project_name}-source-${stamp}.tar.gz"

mkdir -p "$artifact_dir"

tar -czf "$archive" -C "$(dirname "$project_dir")" \
  --exclude="$project_name/artifacts" \
  --exclude='*/.git' --exclude='*/.runtime' --exclude='*/.tools' --exclude='*/.local' \
  --exclude='*/.env' --exclude='*/.env.*' --exclude='*/node_modules' \
  --exclude='*/target' --exclude='*/unpackage' --exclude='*/__pycache__' \
  --exclude='*.log' --exclude='*.pid' --exclude='*.pid.lock' \
  --exclude='*.class' --exclude='*.pyc' --exclude='*:Zone.Identifier' \
  --exclude='*.pem' --exclude='*.key' --exclude='*.p12' --exclude='*.pfx' \
  "$project_name"

(cd "$artifact_dir" && sha256sum "$(basename "$archive")" > "$(basename "$archive").sha256")
printf '%s\n' "$archive"
