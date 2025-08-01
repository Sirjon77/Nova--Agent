import requests
from bs4 import BeautifulSoup

def scrape_youtube_trending():
    url = "https://www.youtube.com/feed/trending"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    titles = [el.text for el in soup.select("h3")]
    return titles[:10]