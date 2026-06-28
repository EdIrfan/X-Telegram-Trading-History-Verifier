# TODO / project status — read me first

> Handoff note for whoever opens this repo next — **especially the AI (Claude Code) on a
> fresh machine** that has none of the prior chat history. The tool is **built and pushed**;
> the one open task is the **Windows clean-room acceptance test**.

## Where this project is (as of 2026-06-28)
**X-Telegram-Verifier** — a containerized tool that points at *any* X account or Telegram
channel, scrapes the calls, grades them against real Binance prices, backtests a realistic
account, and reports honestly whether the edge is real (default deliverable: an **alert-only**
bot). The AI drives the analysis from inside the container; the scrapers are the only fixed code.

Done so far:
- Generic scrapers (`scripts/`), the dev container (`.devcontainer/` + `docker-compose.yml`),
  and the AI playbook (`CLAUDE.md`) are complete.
- **Built and smoke-tested 14/14 on Linux** (Docker Engine) — `claude` CLI, Chromium/noVNC,
  Telethon, Binance oracle, subscription auth all verified.
- Pushed to **github.com/EdIrfan/X-Telegram-Trading-History-Verifier** (this repo).
- Two worked examples in `examples/` (Rose Margin = Telegram; blockchainedbb = X). Both
  reached the same verdict: **no harvestable mechanical edge → alert-only**.

## ▶ THE OPEN TASK: Windows clean-room acceptance test
Prove that a fresh `git clone` on Windows yields a working tool (the Linux box where it was
built doesn't prove cross-platform).

1. Docker Desktop running (**WSL2** backend) + VS Code with the **Dev Containers** extension.
2. In a WSL2 terminal:
   ```bash
   git clone https://github.com/EdIrfan/X-Telegram-Trading-History-Verifier.git
   cd X-Telegram-Trading-History-Verifier
   cp .env.example .env      # add Telegram creds only if testing Telegram
   code .                    # → "Reopen in Container"
   ```
3. Inside the container:
   ```bash
   bash scripts/smoke-test.sh     # PASS=14, FAIL=0 expected
   claude                         # /login (subscription), then: "analyze @somehandle"
   ```
**Success** = smoke-test all-green, then a real scrape + analysis writes a `REPORT.md` into
`data/<account>/analysis/`. Read it via VS Code preview, `scripts/md2html.py`, or
`python -m rich.markdown`.

## If you are the AI (Claude Code) on the new machine — start here
- **Read `CLAUDE.md`** — it's your full playbook for *how* to analyze a caller.
- Your immediate job is to help run the acceptance test above and debug anything that breaks
  (build errors, smoke-test ❌, path issues). Likely suspects: Playwright system-deps, the
  `novnc`/`websockify` package paths, or line-ending breakage (mitigated by `.gitattributes`).
- **Repo-specific gotchas (important):**
  - **MERGE, never rebase** on this repo. Old 2025 commits tracked `data/` files that collide
    with on-disk copies, so any rebase onto a new base will choke. Use merge.
  - `data/` is **fully git-ignored**; all outputs go under `data/<account>/analysis/` and are
    visible on the host via the bind mount.
  - **Auth**: `claude` → `/login` inside the container (a named volume persists it across rebuilds).
  - **X login is manual** via noVNC: `bash scripts/start-display.sh` → open
    `http://localhost:6080/vnc.html` → `python scripts/x_login.py`.
  - **No paid APIs.** Prices = free Binance klines. **Alert-only — never wire it to auto-trade.**

## Nice-to-haves (not blocking the acceptance test)
- After Windows passes: drive a real, fresh caller end-to-end to validate the *playbook* (not
  just the plumbing).
- Optional polish: a laddered partial-TP exit in the grader; a small `Makefile`
  (`make build/up/login/shell`); have the playbook also emit `REPORT.html` automatically.
