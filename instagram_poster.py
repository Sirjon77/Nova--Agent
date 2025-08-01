
# Meta's Graph API requires business account + page linked
# Alternative: use Metricool or Creator Studio bridge

def post_to_instagram(image_url, caption, access_token, ig_user_id):
    import requests
    media_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media"
    publish_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }
    res = requests.post(media_url, data=params).json()
    if 'id' in res:
        publish_params = {
            "creation_id": res['id'],
            "access_token": access_token
        }
        publish_res = requests.post(publish_url, data=publish_params)
        return publish_res.json()
    return res
