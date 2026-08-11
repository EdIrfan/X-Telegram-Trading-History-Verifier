# 03 — Setup (fresh clone → running tool)

## Prerequisites
- **Docker** (Desktop or Engine).
- **VS Code + Dev Containers extension** (recommended), or plain Docker Compose.
- **A coding-agent login** for whatever AI you'll run inside the container — the
  container ships Claude Code preinstalled (`claude` CLI). Either:
  - a Claude Pro/Max subscription (`claude` → `/login`, $0/token), or
  - `ANTHROPIC_API_KEY` set in the host shell (passed through automatically).
  Auth persists in a named Docker volume across rebuilds.
- **Telegram** (only if analyzing a Telegram channel): a free `api_id`/`api_hash`
  from <https://my.telegram.org>, plus your own membership in the target channel.
- **X/Twitter** (only if analyzing an X account): just an account you can log into
  once, by hand, via the container's noVNC browser.

## Steps
```bash
git clone <repo-url> X-Telegram-Verifier
cd X-Telegram-Verifier
cp .env.example .env      # fill in TG_API_ID / TG_API_HASH / TG_PHONE and/or ANTHROPIC_API_KEY
code .                     # VS Code → "Reopen in Container" when prompted
```
Or without VS Code:
```bash
cp .env.example .env
docker compose up -d --build
```

## Verify the build
Inside the container terminal:
```bash
bash scripts/smoke-test.sh     # expect PASS=14 FAIL=0
```
This checks binaries (`python3`, `node`, `npm`, `claude`, `Xvfb`, `x11vnc`,
`websockify`), Python imports (`playwright`, `telethon`, `requests`), headless
Chromium launch, noVNC assets, `scripts/common.py` + `scripts/prices.py`
importability, auth presence, and live Binance reachability (soft check).

## One-time logins
**Telegram** — no separate login step; the first scrape triggers it:
```bash
python scripts/scrape_telegram.py "@some_signals"
```
Telegram texts a login code to your phone; paste it (and 2FA password if set).
Session is saved to `data/secrets/telegram.session` and reused after that.

**X/Twitter** — must be done via the visible browser (headless trips captchas):
```bash
bash scripts/start-display.sh
# then open http://localhost:6080/vnc.html in your laptop browser, click Connect
python scripts/x_login.py
# log into x.com in that noVNC tab, then return to the terminal and press Enter
```
Session cookies are saved to `data/secrets/x_storage_state.json` and reused after
that. (Alternative: export a storage-state JSON from your own browser and drop it
at that same path, skipping `x_login.py` entirely.)

## Then: start the agent
```bash
claude          # first time: /login (subscription) — or rely on ANTHROPIC_API_KEY
```
Say something like *"Analyze @somecaller"* or *"Analyze the @some_signals Telegram
channel I scraped."* The agent follows `../CLAUDE.md` from there.

## Platform notes
- **Windows:** works via Docker Desktop with the **WSL2** backend + VS Code Dev
  Containers — same `code .` flow. Clone into the WSL2 filesystem (e.g. `\\wsl$`)
  for speed. `.gitattributes` forces LF line endings so in-container shell scripts
  run correctly regardless of host checkout settings.
- **Linux/Mac:** builds and runs directly; smoke-tested 14/14 on Linux (Docker
  Engine) as of the last status update in `../TODO.md`.
