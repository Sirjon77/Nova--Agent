import pandas as pd

def adapt_avatar_prompts(log_path, prompt_path):
    df = pd.read_csv(log_path)
    rpm_scores = df.groupby("avatar")["rpm"].mean().to_dict()
    prompts = {}

    for avatar, rpm in rpm_scores.items():
        if rpm < 1.5:
            prompts[avatar] = f"Update hook to be more emotional for {avatar}"
        elif rpm > 3:
            prompts[avatar] = f"Double down on the aggressive hook strategy for {avatar}"
        else:
            prompts[avatar] = f"Try curiosity-based hook for {avatar}"

    with open(prompt_path, "w") as f:
        for avatar, prompt in prompts.items():
            f.write(f"{avatar}: {prompt}\n")

    print("🎯 Avatar prompts adapted based on RPM")