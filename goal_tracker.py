def evaluate_goals(current_rpm, target_rpm, days_remaining):
    if current_rpm >= target_rpm:
        return "🎯 Goal achieved"
    elif days_remaining <= 0:
        return "❌ Goal failed"
    else:
        return f"📈 {target_rpm - current_rpm:.2f} RPM to go with {days_remaining} days left"