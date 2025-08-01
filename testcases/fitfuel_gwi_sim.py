
# Simulate GWI CSV + FitFuel prompt rewrite
import csv, json, random

def generate_mock_gwi_csv(filepath):
    rows = [
        ["Segment", "Age", "Motivation", "Best Platform", "Preferred Content"],
        ["LatAm Young Males", "18-24", "Fitness hacks", "IG/TikTok", "Short, bold reels"],
        ["LatAm Women", "25-34", "Body positivity", "Facebook", "Empowering stories"],
    ]
    with open(filepath, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def evolve_prompts_from_insights():
    base_prompt = "Here's a tip to stay fit and energized..."
    return [
        base_prompt,
        "🔥 Quick fitness hack for LatAm guys 18–24 — feel the pump in 20 sec!",
        "💪 Confidence is strength — your journey, your pace. #FitFuelWomen",
    ]

if __name__ == "__main__":
    filepath = "research_insights/fitfuel/gwi_fitness_latam_2025-06-28.csv"
    generate_mock_gwi_csv(filepath)
    prompts = evolve_prompts_from_insights()
    with open("testcases/fitfuel_evolved_prompts.json", "w") as f:
        json.dump(prompts, f, indent=2)
