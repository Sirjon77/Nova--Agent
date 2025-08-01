
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

def post_to_youtube(title, description, video_path, tags=[]):
    # You must have authenticated with OAuth and stored credentials
    youtube = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public'
        }
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/*')
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    response = request.execute()
    return response
