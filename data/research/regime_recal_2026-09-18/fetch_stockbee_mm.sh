#!/usr/bin/env bash
# Pull Stockbee's published Market Monitor sheet (all yearly tabs) into a LOCAL dir.
# Raw sheet is his published data: keep it out of this public repo; commit only derived results.
set -euo pipefail
OUT=${1:-/tmp/stockbee_mm}; mkdir -p "$OUT/mm_tabs"
K=0Am_cU8NLIU20dEhiQnVHN3Nnc3B1S3J6eGhKZFo0N3c   # iframe on stockbee.blogspot.com/p/mm.html
curl -sL -A "Mozilla/5.0" "https://docs.google.com/spreadsheet/pub?key=$K&output=html" -o "$OUT/mmpub.html"
for g in $(grep -oE 'gid=[0-9]+' "$OUT/mmpub.html" | sort -u | cut -d= -f2); do
  curl -sL -A "Mozilla/5.0" "https://docs.google.com/spreadsheets/d/$K/pub?output=csv&gid=$g" -o "$OUT/mm_tabs/$g.csv"; sleep 1
done
(cd "$OUT" && python3 "$(dirname "$0")/stockbee_mm_combine.py")   # -> $OUT/stockbee_mm_all.csv
