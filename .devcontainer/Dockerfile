# Caller-reverse-engineer dev container.
# One image with everything: Python scrapers + a real browser (Playwright/Chromium)
# viewable over noVNC + Node + Claude Code, so the AI drives the whole analysis here.
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DISPLAY=:99

# System packages: git/curl, the noVNC display stack, fonts, process tools.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git curl ca-certificates gnupg jq \
        xvfb x11vnc fluxbox novnc websockify \
        procps net-tools nano \
        fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Node 20 (for the Claude Code CLI) + Claude Code itself.
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @anthropic-ai/claude-code

WORKDIR /workspace

# Python deps + the Chromium browser (with its OS libraries).
COPY requirements.txt /workspace/requirements.txt
RUN pip install -r /workspace/requirements.txt \
    && python -m playwright install --with-deps chromium

EXPOSE 6080
# Devcontainer/compose keep the container alive and run scripts/start-display.sh.
CMD ["sleep", "infinity"]
