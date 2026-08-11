# context/ — start here (any agent, any model)

This folder is a **model-agnostic briefing pack**. It exists so that *any* AI agent
(Claude, GPT, Gemini, a local model, or a human skimming fast) can get oriented on
this project without reading git history or prior chat transcripts. It documents
**what the project is and how it's built** — not the analysis methodology, which
lives in [`../CLAUDE.md`](../CLAUDE.md) (currently written for Claude Code but
applicable to any capable coding agent running inside the container).

Read in this order:

1. [`01-overview.md`](01-overview.md) — what this tool is, in one page.
2. [`02-architecture.md`](02-architecture.md) — the container, the fixed scripts,
   the data flow, what's git-ignored.
3. [`03-setup.md`](03-setup.md) — how a human or agent gets this running from a
   fresh clone.
4. [`04-workflow.md`](04-workflow.md) — the scrape → extract → grade → backtest →
   report pipeline any agent executes per account.
5. [`05-file-layout.md`](05-file-layout.md) — where everything lives on disk.
6. [`06-gotchas.md`](06-gotchas.md) — repo-specific traps (merge-not-rebase, git
   history quirks, rate limits, etc).
7. [`07-glossary.md`](07-glossary.md) — terms/abbreviations used throughout.

**Relationship to other docs:**
- [`../README.md`](../README.md) — the human-facing quick start (same facts, more prose).
- [`../CLAUDE.md`](../CLAUDE.md) — the analysis *playbook* (grading rules, backtest
  rules, the honesty checks). Read it before doing an actual account analysis.
- [`../TODO.md`](../TODO.md) — current project status / open tasks (this changes
  over time; check it for what's actually left to do).
- [`../examples/`](../examples/) — two full worked runs (Rose Margin on Telegram,
  @blockchainedbb on X), kept as methodology references.

If something in `context/` ever disagrees with the code or with `CLAUDE.md`/`TODO.md`,
**trust the code and those files** — this folder is a map, not the territory, and can
go stale.
