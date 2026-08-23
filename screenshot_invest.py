from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:8002")
    time.sleep(2)
    page.evaluate('localStorage.setItem("celeiro_user","Denis William")')
    page.reload()
    time.sleep(2)
    page.evaluate('switchTab("invest")')
    time.sleep(1)
    page.screenshot(path="preview_invest_final.png", full_page=True)
    browser.close()
    print("OK")
