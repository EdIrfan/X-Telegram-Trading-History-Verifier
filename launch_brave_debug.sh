#!/usr/bin/env bash
# Relaunch the (Flatpak) Brave browser with a CDP remote-debugging port so the
# automation can attach to YOUR existing logged-in profile.
#
# NOTE: Chromium ignores --remote-debugging-port if an instance is already
# running against the same profile, so we must fully quit Brave first. This
# WILL close your current Brave windows/tabs (they reopen via "restore session").
set -euo pipefail

PORT="${1:-9222}"

echo ">> Closing any running Brave instances..."
flatpak kill com.brave.Browser 2>/dev/null || true
pkill -f '/app/brave/brave' 2>/dev/null || true
sleep 2

echo ">> Launching Brave with remote-debugging on port ${PORT}..."
nohup flatpak run com.brave.Browser \
  --remote-debugging-port="${PORT}" \
  --remote-allow-origins="http://127.0.0.1:${PORT}" \
  >/tmp/brave-debug.log 2>&1 &

sleep 4
echo ">> Verifying debug endpoint..."
if curl -s "http://127.0.0.1:${PORT}/json/version" | head -c 400; then
  echo ""
  echo ">> OK: Brave is exposing CDP on 127.0.0.1:${PORT}"
else
  echo ">> Could not reach the debug endpoint yet. Check /tmp/brave-debug.log"
fi
