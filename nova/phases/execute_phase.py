def execute(plan):
    action = plan["action"]
    if action == "resume_loop":
        # placeholder – resume operations
        return "🔄 Resumed The Project."
    if action == "get_rpm":
        # placeholder – fetch real RPM metrics
        return "Current RPM is $0.00 (stub)."
    if action == "chat":
        return f"Nova is thinking… ({plan.get('msg')})"
