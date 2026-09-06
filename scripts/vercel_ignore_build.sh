#!/usr/bin/env bash
# Vercel Ignored Build Step。约定：exit 0 = 跳过部署，exit 1 = 照常构建。
# 只有这些路径变了才值得重新构建产物；其余（研究笔记/契约行/品牌稿/测试）不进产物。
set -u
WATCH=(frontend data/output vercel.json package.json package-lock.json)
if ! git rev-parse --verify HEAD^ >/dev/null 2>&1; then
  echo "[ignore] 拿不到父 commit（浅克隆/首次部署）-> 构建（兜底偏向构建）"; exit 1
fi
if git diff --quiet HEAD^ HEAD -- "${WATCH[@]}"; then
  echo "[ignore] 本次 commit 未触及前端产物路径 -> 跳过部署"; exit 0
fi
echo "[ignore] 触及前端产物路径 -> 构建"
git diff --name-only HEAD^ HEAD -- "${WATCH[@]}" | head -5
exit 1
