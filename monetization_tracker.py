import pandas as pd

def calculate_roi(rpm_log_path, revenue_log_path):
    rpm_data = pd.read_csv(rpm_log_path)
    revenue_data = pd.read_csv(revenue_log_path)
    merged = rpm_data.merge(revenue_data, on="date")
    merged["roi"] = merged["revenue"] / (merged["views"] / 1000)
    print("💰 ROI calculated. Mean ROI:", merged["roi"].mean())
    return merged