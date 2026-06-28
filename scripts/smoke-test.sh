#!/usr/bin/env bash
# Run INSIDE the container after it builds, to confirm everything is wired up:
#     docker compose exec app bash scripts/smoke-test.sh
# (or just `bash scripts/smoke-test.sh` from a devcontainer terminal)
# Exits non-zero if any hard requirement is missing. Network checks are soft.
set -u
pass=0; fail=0
ok()   { echo "  ✅ $1"; pass=$((pass+1)); }
bad()  { echo "  ❌ $1"; fail=$((fail+1)); }
soft() { echo "  ⚠️  $1"; }

echo "── binaries ──────────────────────────────────────────"
for b in python3 node npm claude Xvfb x11vnc websockify; do
  if command -v "$b" >/dev/null 2>&1; then ok "$b ($(command -v "$b"))"; else bad "$b missing"; fi
done

echo "── python imports ────────────────────────────────────"
for m in playwright telethon requests; do
  if python3 -c "import $m" 2>/dev/null; then ok "import $m"; else bad "import $m FAILED"; fi
done

echo "── playwright chromium ───────────────────────────────"
if python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
  if python3 - <<'PY' 2>/dev/null
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox","--disable-dev-shm-usage"])
    b.close()
print("launched")
PY
  then ok "chromium launches headless"; else bad "chromium present but failed to launch"; fi
else bad "playwright not importable"; fi

echo "── noVNC assets ──────────────────────────────────────"
if [ -f /usr/share/novnc/vnc.html ]; then ok "/usr/share/novnc/vnc.html"; else bad "noVNC web client not found"; fi

echo "── project wiring ────────────────────────────────────"
python3 -c "import sys; sys.path.insert(0,'scripts'); import common, prices; print(common.ROOT)" >/dev/null 2>&1 \
  && ok "scripts/common.py + prices.py import" || bad "scripts import failed"

echo "── claude auth (soft) ────────────────────────────────"
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then soft "ANTHROPIC_API_KEY set (API-key auth)";
elif [ -d /root/.claude ] || [ -d "$HOME/.claude" ]; then soft "~/.claude mounted (subscription auth)";
else soft "no auth detected — set ANTHROPIC_API_KEY or mount ~/.claude before running claude"; fi

echo "── binance reachable (soft) ──────────────────────────"
if python3 -c "import sys;sys.path.insert(0,'scripts');import prices;print(prices.price_at('BTC','2025-06-15T12:00:00Z'))" 2>/dev/null | grep -qE '[0-9]'; then
  ok "Binance klines reachable (price oracle live)"; else soft "Binance fetch failed (network?) — scrapers still fine"; fi

echo "──────────────────────────────────────────────────────"
echo "PASS=$pass  FAIL=$fail"
[ "$fail" -eq 0 ] && echo "✅ container looks good — run scripts/start-display.sh then start scraping." || echo "❌ fix the ❌ items above."
exit "$fail"
