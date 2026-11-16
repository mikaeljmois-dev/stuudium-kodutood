"""
Logs into Stuudium with a headless browser, collects the homework pages as
plain text (plus screenshots for debugging) and saves them to data/.
Credentials come only from environment variables (GitHub Secrets).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE = os.environ["STUUDIUM_URL"].rstrip("/")   # e.g. https://minukool.ope.ee
USER = os.environ["STUUDIUM_USER"]
PASS = os.environ["STUUDIUM_PASS"]

OUT = Path("data")
OUT.mkdir(exist_ok=True)

# Words that identify homework / task pages in Stuudium's menu
HOMEWORK_LINK = re.compile(r"(kodu|ülesan|todo|tööd)", re.I)
# Candidate direct paths, tried if no menu link is found
CANDIDATE_PATHS = ["/todo", "/s/todo", "/kodutood", "/ylesanded"]


def save_page(page, name, result):
    text = page.inner_text("body")
    (OUT / f"{name}.txt").write_text(text, encoding="utf-8")
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
    result["pages"].append({"name": name, "url": page.url, "chars": len(text)})


def login(page):
    page.goto(f"{BASE}/", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    # Some login pages hide the password form behind a "parooliga" tab/button
    for label in ["Parooliga", "Kasutajanime ja parooliga", "Parool"]:
        try:
            btn = page.get_by_text(label, exact=False).first
            if btn.is_visible(timeout=1000):
                btn.click()
                page.wait_for_timeout(800)
                break
        except Exception:
            pass

    user_box = page.locator(
        "input[type=email], input[name*=user i], input[name*=login i], "
        "input[name*=email i], input[id*=user i], input[type=text]"
    ).first
    pass_box = page.locator("input[type=password]").first
    user_box.fill(USER)
    pass_box.fill(PASS)
    pass_box.press("Enter")
    page.wait_for_load_state("networkidle", timeout=20000)
    page.wait_for_timeout(2000)

    if page.locator("input[type=password]").count() and page.locator(
        "input[type=password]"
    ).first.is_visible():
        raise RuntimeError("Login failed: still on the login form")


def main():
    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "ok": False,
        "pages": [],
        "error": None,
    }
    # Clear old snapshot
    for f in OUT.glob("*"):
        f.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="et-EE", viewport={"width": 1280, "height": 1800})
        try:
            login(page)
            save_page(page, "01_avaleht", result)

            # Follow homework-looking links from the menu
            links = []
            for a in page.locator("a").all():
                try:
                    txt = (a.inner_text(timeout=500) or "").strip()
                    href = a.get_attribute("href") or ""
                except Exception:
                    continue
                if txt and HOMEWORK_LINK.search(txt) and href and not href.startswith("javascript"):
                    links.append(href)
            links = list(dict.fromkeys(links))[:4]
            if not links:
                links = CANDIDATE_PATHS

            for i, href in enumerate(links, start=2):
                url = href if href.startswith("http") else f"{BASE}/{href.lstrip('/')}"
                try:
                    page.goto(url, wait_until="networkidle", timeout=20000)
                    page.wait_for_timeout(1500)
                    save_page(page, f"{i:02d}_kodutood", result)
                except PWTimeout:
                    continue

            # Log out
            try:
                page.get_by_text(re.compile("Logi välja|Välju", re.I)).first.click(timeout=3000)
            except Exception:
                pass
            result["ok"] = True
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {e}"
            try:
                page.screenshot(path=str(OUT / "viga.png"), full_page=True)
            except Exception:
                pass
        finally:
            browser.close()

    # Never write credentials anywhere; scrub just in case
    for f in OUT.glob("*.txt"):
        t = f.read_text(encoding="utf-8").replace(PASS, "***")
        f.write_text(t, encoding="utf-8")

    (OUT / "status.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
