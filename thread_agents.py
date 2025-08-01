
class RedditAgent:
    def fetch_thread(self, url):
        print(f"[RedditAgent] Fetching thread from {url} (mocked)")
        return "Sample Reddit content..."

class YouTubeAgent:
    def fetch_comments(self, video_id):
        print(f"[YouTubeAgent] Fetching comments for {video_id} (mocked)")
        return "Top comments for YouTube video..."

class TwitterAgent:
    def fetch_replies(self, tweet_url):
        print(f"[TwitterAgent] Fetching replies for {tweet_url} (mocked)")
        return "Replies to tweet..."
