import pandas as pd

def diagnose_rpm_issues(csv_path):
    df = pd.read_csv(csv_path)
    low_rpm = df[df["rpm"] < 1.0]
    if not low_rpm.empty:
        print("⚠️ Low RPM detected in:")
        print(low_rpm[["avatar", "hook", "rpm"]])
    else:
        print("✅ No major RPM issues detected")