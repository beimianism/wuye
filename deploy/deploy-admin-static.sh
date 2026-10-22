#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -d $1 || ! -f $1/user.html ]]; then
  echo '用法: deploy-admin-static.sh <已部署业主 H5 的站点根目录>' >&2
  exit 2
fi

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
admin_public=$repo_root/wuye-f/MicroCommunityWeb-v0.8/public
if [[ ! -f $admin_public/admin.html || ! -f $admin_public/staff-login.html ]]; then
  echo '管理后台页面缺失' >&2
  exit 1
fi

# Both clients use root-relative asset paths. Keep the owner's index.html and user.html.
rsync -a --exclude '/index.html' --exclude '/user.html' "$admin_public/" "$1/"
echo '管理后台静态页面已同步；请验证 OpenResty 认证及 /callComponent/ 代理。'
