
import time
from playwright_scraper import fetch_rendered_html

def run_crawl_test_suite():
    test_urls = [
        "https://www.tiktok.com/@garyvee/video/7228579203949845761",
        "https://medium.com/@ai-university/top-10-ai-tools-2024-8e3a29fa2c2b"
    ]
    logs = []
    for url in test_urls:
        logs.append(f"Testing: {url}")
        html = fetch_rendered_html(url)
        if html:
            logs.append(f"[PASS] {url} loaded successfully. Length: {len(html)} chars")
        else:
            logs.append(f"[FAIL] Could not load {url}")
        time.sleep(2)
    return logs
