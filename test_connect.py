#!/usr/bin/env python3
"""Quick connectivity + login + sample check before the full scrape."""
import sys, time
from playwright.sync_api import sync_playwright

def log(*a): print(*a, flush=True)

log("connecting...")
pw = sync_playwright().start()
browser = pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
log("connected. contexts:", len(browser.contexts))
ctx = browser.contexts[0]
page = ctx.new_page()
page.set_default_navigation_timeout(30000)
log("page opened")

# logged-in check
log("navigating to /home...")
try:
    page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
except Exception as e:
    log("goto /home error:", e)
log("home loaded, url=", page.url)
time.sleep(4)
logged_in = page.locator("a[data-testid='SideNav_NewTweet_Button'], "
                         "a[aria-label='Post']").count() > 0
print("LOGGED_IN:", logged_in)
print("URL:", page.url)

# sample her recent posts
page.goto("https://x.com/blockchainedbb", wait_until="domcontentloaded")
time.sleep(6)
arts = page.locator("article[data-testid='tweet']").count()
print("VISIBLE_ARTICLES:", arts)
sample = page.eval_on_selector_all(
    "article[data-testid='tweet']",
    """els => els.slice(0,5).map(a => {
        const t = a.querySelector('time');
        const tx = a.querySelector("div[data-testid='tweetText']");
        const imgs = a.querySelectorAll("img[src*='/media/']").length;
        const vid = !!a.querySelector("[data-testid='videoPlayer'],video");
        return {dt: t?t.getAttribute('datetime'):null,
                text: tx?tx.innerText.slice(0,280):'', imgs, vid};
    })""")
for i, s in enumerate(sample):
    print(f"--- [{i}] {s['dt']}  imgs={s['imgs']} vid={s['vid']}")
    print("   ", s["text"].replace("\n", " "))
page.close()
pw.stop()
