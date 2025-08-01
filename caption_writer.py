
def generate_caption(prompt, platform="Instagram"):
    # Simple format based on platform style
    if platform == "Instagram":
        return f"{prompt} ✨🔥 #reels #viral #foryou"
    elif platform == "YouTube":
        return f"{prompt} | Watch now & subscribe 👉"
    elif platform == "TikTok":
        return f"{prompt} 💥 #fyp #trending"
    return prompt
