
from deep_web_crawler import DeepWebCrawler

def process_prompt_for_crawl(prompt):
    if "http" in prompt:
        print(f"[Web Hook] Detected URL in prompt: {prompt}")
        crawler = DeepWebCrawler(prompt, depth=3)
        crawler.crawl()
        results = crawler.get_results()
        for r in results:
            print(f"[Crawled] {r['url']} -> {len(r['text'])} chars")
        return results
    return []
