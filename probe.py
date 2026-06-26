#!/usr/bin/env python3
"""Diagnose: is search rate-limited now? does until: filter work? does the
profile timeline scroll back in time cleanly?"""
import sys, time
from playwright.sync_api import sync_playwright

def log(*a): print(*a, flush=True)

pw = sync_playwright().start()
b = pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
page = b.contexts[0].new_page()
page.set_default_navigation_timeout(40000)

def visible():
    return page.eval_on_selector_all(
        "article[data-testid='tweet']",
        """els => els.map(a => {
            const t=a.querySelector('time');
            const tx=a.querySelector("div[data-testid='tweetText']");
            return {dt:t?t.getAttribute('datetime'):null,
                    txt:tx?tx.innerText.slice(0,60):''};})""")

def errstate():
    body = page.inner_text("body")[:500].lower()
    for k in ["something went wrong","try again","rate limit","caught up",
              "no results","over capacity"]:
        if k in body: return k
    return None

# 1) is a mid-range search returning anything right now?
url=("https://x.com/search?q=from:blockchainedbb%20"
     "since:2026-03-01%20until:2026-03-08&f=live")
log("PROBE1 search 2026-03-01..08:", url)
page.goto(url, wait_until="domcontentloaded"); time.sleep(6)
v=visible(); log("  err:",errstate()," articles:",len(v))
for x in v[:3]: log("   ",x["dt"],x["txt"])

# 2) does until: actually bound results? tight 1-week window
url=("https://x.com/search?q=from:blockchainedbb%20"
     "since:2025-06-01%20until:2025-06-08&f=live")
log("PROBE2 search 2025-06-01..08:", url)
page.goto(url, wait_until="domcontentloaded"); time.sleep(6)
v=visible(); log("  err:",errstate()," articles:",len(v))
dts=[x["dt"] for x in v if x["dt"]]
log("  date span:", (min(dts) if dts else None),"->",(max(dts) if dts else None))

# 3) profile timeline: does it scroll back in time?
log("PROBE3 profile scroll test")
page.goto("https://x.com/blockchainedbb", wait_until="domcontentloaded")
time.sleep(6)
seen=set()
for i in range(8):
    for x in visible():
        if x["dt"]: seen.add(x["dt"])
    page.mouse.wheel(0,5000); time.sleep(2)
if seen:
    log("  after 8 scrolls: count=",len(seen),
        " newest=",max(seen)," oldest=",min(seen))
page.close(); pw.stop()
