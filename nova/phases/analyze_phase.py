def analyze(message: str):
    # TODO: replace with NLP intent detection
    if message.lower().startswith("resume"):
        return {"intent": "resume"}
    if "rpm" in message.lower():
        return {"intent": "rpm"}
    return {"intent": "generic", "msg": message}
