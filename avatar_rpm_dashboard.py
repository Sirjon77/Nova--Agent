import pandas as pd
import matplotlib.pyplot as plt

def render_avatar_performance(data_path):
    df = pd.read_csv(data_path)
    avatars = df["avatar"].unique()
    for avatar in avatars:
        sub_df = df[df["avatar"] == avatar]
        plt.plot(sub_df["date"], sub_df["rpm"], label=avatar)
    plt.legend()
    plt.title("Avatar RPM Over Time")
    plt.xlabel("Date")
    plt.ylabel("RPM")
    plt.savefig("rpm_dashboard.png")
    print("🎯 Dashboard generated: rpm_dashboard.png")