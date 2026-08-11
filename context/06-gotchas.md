# 06 — Gotchas / repo-specific traps

- **Use `git merge`, never `git rebase` on this repo.** Old commits tracked some
  `data/` files that now collide with on-disk copies; rebasing onto a new base will
  choke on those conflicts. This is called out explicitly in `../TODO.md` — don't
  rebase even if it seems like the cleaner history.

- **`data/` is fully git-ignored, on purpose.** If you (or an agent) find yourself
  wanting to commit something under `data/`, stop — account-specific scraped data,
  session files, and analysis output must never enter git history. Anything that
  should be reusable across accounts belongs in `scripts/` instead.

- **Never commit `.env`, `*.session`, or `*storage_state*` files.** These hold
  Telegram API credentials/session and X/Twitter login cookies respectively.
  They're git-ignored already, but double-check before any broad `git add`.

- **X/Twitter scraping rate-limits hard.** A window coming back empty doesn't mean
  failure — just re-run `scrape_twitter.py`; it dedupes by permalink and resumes.
  Several short runs beat one long run. Headless X login trips captchas — the
  login must happen once, interactively, via noVNC (`x_login.py`).

- **Telegram scraping requires you to actually be a member of the channel.** The
  scraper searches chats you've joined via your own Telegram account (Telethon,
  not a bot).

- **Price granularity is 1 hour**, which can miss rare sub-hour wicks. This is a
  known, accepted limitation, not a bug to "fix" by hardcoding tighter intervals
  everywhere — see `scripts/prices.py`.

- **Chart-reading quality depends on the AI model doing the reading.** Ambiguous
  charts (overlapping lines, unclear which line is entry vs. target) should be
  flagged in the extraction output, not guessed silently.

- **This tool is alert-only by design — do not wire the bot to auto-trade.**
  Even if a backtest looks strongly positive, `../CLAUDE.md` §0 requires it be
  "overwhelmingly and robustly positive" (rare) before even considering anything
  beyond alert-only, and the default recommendation is always alert-only.

- **`examples/*/` scripts are not meant to be re-run as-is.** They were written to
  execute from the *original* repo root of a different, earlier project layout
  (paths like bare `data/telegram_rose.json`, `rose.session` at repo root) before
  the generic `scripts/` tooling existed. Read them for method; don't expect them
  to run unmodified against the current `scripts/` + `data/<slug>/` layout.

- **`TODO.md` is the live status file, not this `context/` folder.** `context/`
  describes stable structure; check `../TODO.md` for what's actually in progress
  or blocking right now (e.g. the Windows acceptance test as of the last update).
