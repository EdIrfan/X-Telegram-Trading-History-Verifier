#!/usr/bin/env python3
"""
Scrape @blockchainedbb posts in a date window by attaching to YOUR running
Brave (over CDP) so we reuse your logged-in X session.

Usage:
    python scrape_posts.py --user blockchainedbb \
        --since 2025-06-01 --until 2026-06-26 --port 9222

Strategy: drive X's search ("from:USER since:.. until:.."), scroll until no new
tweets load, and dump each tweet's text, timestamp, permalink and any image
URLs to data/posts.json. Charts (images) are saved as URLs for later review.
"""
import argparse
import json
import os
import time
from datetime import datetime

from playwright.sync_api import sync_playwright

OUT_DIR = os.path.join(os.path.dirname(__file__), "data")


def connect(port: int):
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return pw, browser, page


def extract_visible(page):
    """Pull tweet articles currently in the DOM."""
    return page.eval_on_selector_all(
        "article[data-testid='tweet']",
        """(articles) => articles.map(a => {
            const timeEl = a.querySelector('time');
            const link = timeEl ? timeEl.closest('a') : null;
            const textEl = a.querySelector("div[data-testid='tweetText']");
            // images only: keep /media/ photos, drop video posters/thumbnails
            const imgs = Array.from(a.querySelectorAll("img"))
                .map(i => i.src)
                .filter(s => s.includes('twimg') && s.includes('/media/')
                    && !s.includes('video_thumb') && !s.includes('amplify'));
            const hasVideo = !!a.querySelector(
                "[data-testid='videoPlayer'], video");
            return {
                datetime: timeEl ? timeEl.getAttribute('datetime') : null,
                permalink: link ? link.href : null,
                text: textEl ? textEl.innerText : '',
                images: imgs,
                has_video: hasVideo,
            };
        })""",
    )


def _windows(since: str, until: str, days: int):
    """Yield (start, end) ISO-date strings in `days`-long windows."""
    from datetime import timedelta
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
    for k in ("something went wrong", "try again", "rate limit",
              "over capacity"):
        if k in body:
            return k
    return None


def _load_existing():
    out = os.path.join(OUT_DIR, "posts.json")
    if os.path.exists(out):
        try:
            data = json.load(open(out))
            return {(p.get("permalink") or p.get("datetime")): p
                    for p in data.get("posts", [])}
        except Exception:
            pass
    return {}


def _save(seen, user, since, until):
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "posts.json")
    posts = sorted(seen.values(), key=lambda x: x.get("datetime") or "")
    with open(out, "w") as f:
        json.dump({"user": user, "since": since, "until": until,
                   "scraped_at": datetime.utcnow().isoformat(),
                   "count": len(posts), "posts": posts}, f, indent=2)
    return out, len(posts)


def _scrape_window(page, user, w_since, w_until, seen, max_idle, max_iters):
    """Scroll one window; returns count gained. Retries once on rate-limit."""
    q = f"from:{user} since:{w_since} until:{w_until}"
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


def scrape(user: str, since: str, until: str, port: int, days: int = 5,
           max_idle: int = 4, max_iters: int = 40, pause: float = 9.0):
    pw, browser, page = connect(port)
    seen = _load_existing()
    print(f">> Resuming with {len(seen)} existing posts", flush=True)
    out = os.path.join(OUT_DIR, "posts.json")
    for w_since, w_until in _windows(since, until, days):
        gained = _scrape_window(page, user, w_since, w_until, seen,
                                max_idle, max_iters)
        out, n = _save(seen, user, since, until)  # checkpoint each window
        print(f">> [{w_since}..{w_until}] +{gained} (total={len(seen)})",
              flush=True)
        time.sleep(pause)  # pace requests to avoid rate-limiting
    print(f">> DONE. Saved {len(seen)} posts -> {out}", flush=True)
    pw.stop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="blockchainedbb")
    ap.add_argument("--since", default="2025-06-01")
    ap.add_argument("--until", default="2026-06-26")
    ap.add_argument("--port", type=int, default=9222)
    ap.add_argument("--days", type=int, default=5, help="window size in days")
    a = ap.parse_args()
    scrape(a.user, a.since, a.until, a.port, days=a.days)
