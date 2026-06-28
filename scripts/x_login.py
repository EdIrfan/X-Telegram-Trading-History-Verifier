#!/usr/bin/env python3
"""
One-time interactive X / Twitter login, inside the container.

X requires a logged-in session to view a profile's full timeline, and logging in
headlessly trips captchas. So we open a REAL browser on the container's virtual
display and let you log in by hand, exactly once. The resulting cookies are saved
to data/secrets/x_storage_state.json and reused (headless) by scrape_twitter.py.

HOW TO SEE THE BROWSER (noVNC):
    1. Make sure the display is up:   bash scripts/start-display.sh
    2. Open  http://localhost:6080/vnc.html  in your laptop browser, click Connect.
    3. Run this script:               python scripts/x_login.py
    4. A browser window appears in that noVNC tab — log into x.com normally
       (handle the 2FA / captcha there). When your home timeline loads, come back
       to THIS terminal and press Enter. The session is saved.

ALTERNATIVE (no noVNC): log into X in your own laptop browser, export the
storage state (e.g. with a cookie-export extension or Playwright on your host),
and drop the JSON at data/secrets/x_storage_state.json — then skip this script.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ensure_secrets  # noqa: E402

from playwright.sync_api import sync_playwright  # noqa: E402

STATE = os.path.join(ensure_secrets(), "x_storage_state.json")
PROFILE = os.path.join(ensure_secrets(), "x-profile")


def logged_in(page) -> bool:
    """Heuristic: the primary nav (Home/Explore) only renders when logged in."""
    try:
        return page.locator("a[data-testid='AppTabBar_Home_Link']").count() > 0
    except Exception:
        return False


def main():
    headless = "--headless" in sys.argv  # debugging only; real login needs headed
    os.makedirs(PROFILE, exist_ok=True)
    print(">> Launching browser on DISPLAY", os.environ.get("DISPLAY", "(none)"),
          "\n   View it at  http://localhost:6080/vnc.html", flush=True)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, headless=headless,
            viewport={"width": 1280, "height": 820},
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://x.com/login", wait_until="domcontentloaded")
        print("\n>> Log into X in the noVNC browser window now.", flush=True)
        # poll up to ~10 min, but also let the user confirm manually
        deadline = time.time() + 600
        while time.time() < deadline:
            if logged_in(page):
                print(">> Detected a logged-in session.", flush=True)
                break
            time.sleep(3)
        try:
            input(">> When your X home feed is loaded, press Enter here to save... ")
        except EOFError:
            pass
        ctx.storage_state(path=STATE)
        ctx.close()
    print(f">> Saved session -> {STATE}\n   Now run: python scripts/scrape_twitter.py <handle>",
          flush=True)


if __name__ == "__main__":
    main()
