
# Matches parsed trend segments with prompt RPM memory
import json

def match_trends_to_prompts(trend_data_path, rpm_log_path):
    with open(trend_data_path, "r") as f:
        trends = json.load(f)
    with open(rpm_log_path, "r") as f:
        rpm_data = json.load(f)

    matches = []
    for trend in trends:
        segment = trend.get("Segment", "").lower()
        for prompt in rpm_data.get("prompts", []):
            if segment in prompt.get("text", "").lower():
                matches.append({
                    "prompt": prompt["text"],
                    "rpm": prompt["rpm"],
                    "trend_segment": segment
                })
    return matches
