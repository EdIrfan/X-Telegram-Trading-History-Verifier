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


def scrape(user: str, since: str, until: str, port: int, max_idle: int = 8):
    pw, browser, page = connect(port)
    q = f"from:{user} since:{since} until:{until}"
    url = f"https://x.com/search?q={q.replace(' ', '%20')}&f=live"
    print(f">> Navigating to: {url}")
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(5)

    seen = {}
    idle = 0
    while idle < max_idle:
        for t in extract_visible(page):
            key = t.get("permalink") or t.get("datetime")
            if key and key not in seen:
                seen[key] = t
        before = len(seen)
        page.mouse.wheel(0, 4000)
        time.sleep(2.5)
        # re-collect after scroll
        for t in extract_visible(page):
            key = t.get("permalink") or t.get("datetime")
            if key and key not in seen:
                seen[key] = t
        gained = len(seen) - before
        idle = idle + 1 if gained == 0 else 0
        print(f"   collected={len(seen)}  (+{gained})  idle={idle}")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "posts.json")
    posts = sorted(seen.values(), key=lambda x: x.get("datetime") or "")
    with open(out, "w") as f:
        json.dump({"user": user, "since": since, "until": until,
                   "scraped_at": datetime.utcnow().isoformat(),
                   "count": len(posts), "posts": posts}, f, indent=2)
    print(f">> Saved {len(posts)} posts -> {out}")
    pw.stop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="blockchainedbb")
    ap.add_argument("--since", default="2025-06-01")
    ap.add_argument("--until", default="2026-06-26")
    ap.add_argument("--port", type=int, default=9222)
    a = ap.parse_args()
    scrape(a.user, a.since, a.until, a.port)
