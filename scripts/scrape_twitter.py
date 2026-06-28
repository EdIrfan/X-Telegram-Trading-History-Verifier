#!/usr/bin/env python3
"""
Scrape ANY public X / Twitter account's posts into JSON, inside the container.

Uses the saved login from scripts/x_login.py (data/secrets/x_storage_state.json),
drives X's live search `from:<handle> since:.. until:..` in small date windows,
scrolls each window until no new tweets load, and dumps text + timestamp +
permalink + image URLs to data/<handle>/twitter_posts.json.

    python scripts/scrape_twitter.py elonmusk
    python scripts/scrape_twitter.py somecaller --since 2025-01-01 --until 2026-06-28
    python scripts/scrape_twitter.py somecaller --headed     # watch it via noVNC

LIMITATIONS (be patient, this is the nature of scraping X):
  * X rate-limits hard. The scraper paces itself and backs off 60s on a limit
    notice; if a window comes back empty, just re-run — it RESUMES (dedupes by
    permalink) and fills the gaps. Running it a few times beats one long run.
  * Only *original* /media/ images are kept (video posters/thumbnails dropped).
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import account_dir, ensure_secrets  # noqa: E402

from playwright.sync_api import sync_playwright  # noqa: E402

STATE = os.path.join(ensure_secrets(), "x_storage_state.json")


def extract_visible(page):
    return page.eval_on_selector_all(
        "article[data-testid='tweet']",
        """(articles) => articles.map(a => {
            const t = a.querySelector('time');
            const link = t ? t.closest('a') : null;
            const txt = a.querySelector("div[data-testid='tweetText']");
            const imgs = Array.from(a.querySelectorAll('img'))
                .map(i => i.src)
                .filter(s => s.includes('twimg') && s.includes('/media/')
                    && !s.includes('video_thumb') && !s.includes('amplify'));
            return {
                datetime: t ? t.getAttribute('datetime') : null,
                permalink: link ? link.href : null,
                text: txt ? txt.innerText : '',
                images: imgs,
                has_video: !!a.querySelector("[data-testid='videoPlayer'], video"),
            };
        })""",
    )


def _windows(since, until, days):
    cur = datetime.strptime(since, "%Y-%m-%d")
    end = datetime.strptime(until, "%Y-%m-%d")
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")
        cur = nxt


def _errstate(page):
    try:
        body = page.inner_text("body")[:600].lower()
    except Exception:
        return None
    for k in ("something went wrong", "try again", "rate limit", "over capacity"):
        if k in body:
            return k
    return None


def _load(out):
    if os.path.exists(out):
        try:
            data = json.load(open(out))
            return {(p.get("permalink") or p.get("datetime")): p
                    for p in data.get("posts", [])}
        except Exception:
            pass
    return {}


def _save(out, seen, handle, since, until):
    posts = sorted(seen.values(), key=lambda x: x.get("datetime") or "")
    json.dump({"handle": handle, "since": since, "until": until,
               "scraped_at": datetime.utcnow().isoformat(),
               "count": len(posts), "posts": posts},
              open(out, "w"), indent=2, ensure_ascii=False)


def _scrape_window(page, handle, w0, w1, seen, max_idle, max_iters):
    q = f"from:{handle} since:{w0} until:{w1}"
    url = f"https://x.com/search?q={q.replace(' ', '%20')}&f=live"
    start = len(seen)
    for attempt in (1, 2):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            print("   goto error:", e, flush=True)
        time.sleep(5)
        err = _errstate(page)
        if err and attempt == 1:
            print(f"   rate-limit/err '{err}', backing off 60s...", flush=True)
            time.sleep(60)
            continue
        idle = it = 0
        while idle < max_idle and it < max_iters:
            it += 1
            before = len(seen)
            for t in extract_visible(page):
                key = t.get("permalink") or t.get("datetime")
                if key and key not in seen:
                    seen[key] = t
            page.mouse.wheel(0, 4200)
            time.sleep(2.3)
            idle = idle + 1 if len(seen) == before else 0
        break
    return len(seen) - start


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("handle", help="X username without @, e.g. blockchainedbb")
    ap.add_argument("--since", default="2025-01-01")
    ap.add_argument("--until", default=datetime.utcnow().strftime("%Y-%m-%d"))
    ap.add_argument("--days", type=int, default=5, help="search window size")
    ap.add_argument("--headed", action="store_true", help="show browser (noVNC)")
    ap.add_argument("--pause", type=float, default=9.0)
    a = ap.parse_args()

    if not os.path.exists(STATE):
        sys.exit("!! No X session. Run `python scripts/x_login.py` first (or drop "
                 "an exported storage state at data/secrets/x_storage_state.json).")

    out = os.path.join(account_dir(a.handle), "twitter_posts.json")
    seen = _load(out)
    print(f">> @{a.handle}: resuming with {len(seen)} existing posts -> {out}", flush=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=not a.headed,
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = browser.new_context(storage_state=STATE,
                                  viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        for w0, w1 in _windows(a.since, a.until, a.days):
            gained = _scrape_window(page, a.handle, w0, w1, seen, 4, 40)
            _save(out, seen, a.handle, a.since, a.until)   # checkpoint each window
            print(f">> [{w0}..{w1}] +{gained} (total={len(seen)})", flush=True)
            time.sleep(a.pause)
        browser.close()
    print(f">> DONE. {len(seen)} posts -> {out}", flush=True)


if __name__ == "__main__":
    main()
