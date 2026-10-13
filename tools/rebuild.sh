#!/usr/bin/env bash
# Rebuild the published site/ folder from source/.
# Usage: tools/rebuild.sh <domain>      e.g. tools/rebuild.sh example.com   (use - for no domain)
# Needs: python3, pandoc, and pip packages weasyprint, numpy, pillow.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN="${1:--}"
W="$(mktemp -d)"
ln -s "$REPO/source/md" "$W/md"; ln -s "$REPO/source/fig" "$W/fig"; ln -s "$REPO/source/fonts" "$W/fonts"; ln -s "$REPO/source/brand" "$W/brand"
mkdir -p "$W/site"; cp "$REPO/source/page/index.html" "$W/site/index.html"
# Parchment PDFs
python3 "$REPO/tools/build_pdfs.py" "$W"
# White PDFs
OUTDIR="$W/site/chapters-white" TONEDIR="$W/figtone-white" C_INK="#231C15" C_SANG="#7A4B2B" C_INDIGO="#2D5592" \
  C_FADED="#8A7863" C_PAPER="#FFFFFF" C_HAIR="#E4DED5" python3 "$REPO/tools/build_pdfs.py" "$W"
# Reading-view chapters and figures
python3 "$REPO/tools/build_reader.py" "$W"
# Standalone site
python3 "$REPO/tools/make_dist.py" "$W" "$REPO/site" "$DOMAIN"
rm -rf "$W"
echo "site/ rebuilt"
