
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class DeepWebCrawler:
    def __init__(self, base_url, depth=3):
        self.visited = set()
        self.base_url = base_url
        self.depth = depth
        self.results = []

    def crawl(self, url=None, level=0):
        if level > self.depth:
            return
        if url is None:
            url = self.base_url
        if url in self.visited:
            return
        self.visited.add(url)
        try:
            res = requests.get(url, timeout=10)
            html = res.text
            if 'text/html' not in res.headers.get('Content-Type', ''):
                from playwright_scraper import fetch_rendered_html
                html = fetch_rendered_html(url) or html
            soup = BeautifulSoup(html, 'html.parser')
            if 'text/html' not in res.headers.get('Content-Type', ''):
                return
            soup = BeautifulSoup(res.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            self.results.append({'url': url, 'text': text[:1000]})
            links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
            for link in links:
                self.crawl(link, level + 1)
        except Exception as e:
            print(f"Error crawling {url}: {e}")

    def get_results(self):
        return self.results
