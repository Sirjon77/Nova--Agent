def plan(analysis):
    intent = analysis["intent"]
    if intent == "resume":
        return {"action": "resume_loop"}
    if intent == "rpm":
        return {"action": "get_rpm"}
    return {"action": "chat", "msg": analysis.get("msg")}
