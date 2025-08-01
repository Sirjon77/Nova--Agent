
import requests
from bs4 import BeautifulSoup

def scrape_youtube_trends(keyword="AI"):
    url = f"https://www.youtube.com/results?search_query={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    titles = [a.text for a in soup.select("a#video-title")[:5]]
    return titles
