
import requests

def post_video_to_facebook(page_id, access_token, video_url, caption=""):
    upload_url = f"https://graph-video.facebook.com/v18.0/{page_id}/videos"
    payload = {
        "access_token": access_token,
        "file_url": video_url,
        "description": caption,
        "published": "true"
    }

    response = requests.post(upload_url, data=payload)
    return response.json()

# Example:
# post_video_to_facebook("your_page_id", "your_access_token", "https://yourdomain.com/path/video.mp4", "Your Caption Here")
