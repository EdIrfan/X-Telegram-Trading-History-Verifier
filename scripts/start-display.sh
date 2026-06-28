#!/usr/bin/env bash
# Start a virtual display + VNC + noVNC so a HEADED browser (x_login.py /
# scrape_twitter.py --headed) is viewable from your laptop at
#     http://localhost:6080/vnc.html
#
# Idempotent: safe to run repeatedly (the devcontainer runs it on start).
set -u
export DISPLAY="${DISPLAY:-:99}"
NUM="${DISPLAY#:}"

start() { pgrep -f "$1" >/dev/null 2>&1 || { eval "$2" >/tmp/${3}.log 2>&1 & }; }

start "Xvfb ${DISPLAY}"        "Xvfb ${DISPLAY} -screen 0 1440x900x24 -ac"      xvfb
sleep 1
start "fluxbox"               "fluxbox"                                         fluxbox
start "x11vnc.*${DISPLAY}"     "x11vnc -display ${DISPLAY} -nopw -forever -shared -rfbport 5900"  x11vnc
# noVNC web client (Debian package installs to /usr/share/novnc)
NOVNC_DIR=$( [ -d /usr/share/novnc ] && echo /usr/share/novnc || echo /usr/share/webapps/novnc )
start "websockify.*6080"      "websockify --web=${NOVNC_DIR} 6080 localhost:5900"  novnc

sleep 1
echo ">> Display ${DISPLAY} up. Open  http://localhost:6080/vnc.html  (click Connect)."
