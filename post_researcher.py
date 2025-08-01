
import requests
from bs4 import BeautifulSoup

def scan_trending_posts(topic="video marketing"):
    query = topic.replace(" ", "+")
    url = f"https://www.google.com/search?q={query}+site:youtube.com"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    results = []
    for link in soup.select('a[href^="https://www.youtube.com/watch"]')[:5]:
        title = link.get_text(strip=True)
        href = link['href']
        results.append({"title": title, "url": href})
    return results
