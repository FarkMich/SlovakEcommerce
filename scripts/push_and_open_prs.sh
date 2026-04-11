#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== 1/4: self-hosting fonts (P1 vetva) ==="
python3 scripts/download_fonts.py

if ! git diff --quiet || ! git diff --cached --quiet; then
  git add -A
  git commit -m "chore: self-host Sora and DM Mono fonts"
else
  echo "   (no font changes to commit)"
fi

echo
echo "=== 2/4: push chore/p0-audit-plausible ==="
git push -u origin chore/p0-audit-plausible

echo
echo "=== 3/4: push chore/p1-fonts-csp-nav ==="
git push -u origin chore/p1-fonts-csp-nav

echo
echo "=== 4/4: opening PRs via gh ==="

P0_BODY="P0 audit changes: GTM and GA4 removed, Plausible added, inline CSS extracted to css/style.css, Cache-Control headers, CSP, robots.txt, expanded sitemap, privacy.html, onas duplicate removed, Plausible custom event classes on subpage cards and mailto links."

P1_BODY="P1 audit changes: inline nav.js IIFE replaced by static HTML nav and footer. js/nav.js now holds only scroll animations and active-link marker. platformy page finally has nav and footer. Fonts self-hosted via scripts/download_fonts.py."

gh pr create --base main --head chore/p0-audit-plausible \
  --title "P0: audit fixes + GTM/GA4 to Plausible" \
  --body "$P0_BODY"

gh pr create --base main --head chore/p1-fonts-csp-nav \
  --title "P1: static nav, lean nav.js, self-hosted fonts" \
  --body "$P1_BODY"

echo
echo "✅ Done."
