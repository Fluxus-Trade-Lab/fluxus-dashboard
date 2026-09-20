#!/usr/bin/env bash
# Vercel Ignored Build Step。约定：exit 0 = 跳过部署，exit 1 = 照常构建。
# 只有这些路径变了才值得重新构建产物；其余（研究笔记/契约行/品牌稿/测试）不进产物。
#
# 比较基准是「上一次成功部署的 commit」（Vercel 在 Ignored Build Step 里提供
# VERCEL_GIT_PREVIOUS_SHA），不是 HEAD^。HEAD^ 只看一次推送里的最后一个 commit：
# 2026-09-13 隐私清洗一次推了 5 个 commit，最后一个只改测试，整批被判「未触及产物」
# 跳过，已清洗的数据没有上线。仓库是公开的，基准不在浅克隆里时可以直接加深拉取；
# 仍拿不到基准一律偏向构建。
set -u
WATCH=(frontend data/output vercel.json package.json package-lock.json scripts/vercel_ignore_build.sh)

have_commit() { git cat-file -e "$1^{commit}" 2>/dev/null; }

BASE="${VERCEL_GIT_PREVIOUS_SHA:-}"
if [ -n "$BASE" ]; then
  if ! have_commit "$BASE"; then
    git fetch --quiet --deepen=500 origin >/dev/null 2>&1 || true
  fi
  if ! have_commit "$BASE"; then
    echo "[ignore] 上次部署 ${BASE:0:8} 不在克隆里且加深拉取失败 -> 构建（兜底偏向构建）"; exit 1
  fi
  echo "[ignore] 基准 = 上次成功部署 ${BASE:0:8}"
elif git rev-parse --verify HEAD^ >/dev/null 2>&1; then
  BASE=HEAD^
  echo "[ignore] 没有 VERCEL_GIT_PREVIOUS_SHA，退回 HEAD^"
else
  echo "[ignore] 拿不到父 commit（浅克隆/首次部署）-> 构建（兜底偏向构建）"; exit 1
fi

if git diff --quiet "$BASE" HEAD -- "${WATCH[@]}"; then
  echo "[ignore] 自基准以来未触及前端产物路径 -> 跳过部署"; exit 0
fi
echo "[ignore] 自基准以来触及前端产物路径 -> 构建"
git diff --name-only "$BASE" HEAD -- "${WATCH[@]}" | head -5
exit 1
