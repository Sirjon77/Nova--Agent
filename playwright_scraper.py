
from playwright.sync_api import sync_playwright

def fetch_rendered_html(url, wait_for='networkidle', timeout=60000):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=timeout)
            page.wait_for_load_state(wait_for)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"[Playwright Error] {e}")
        return None
