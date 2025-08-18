
# Daily scan for new CSVs in research_insights/
import os
import datetime

def scan_research_csvs(brand_folder="research_insights"):
    today = datetime.date.today().isoformat()
    new_files = []
    for brand in os.listdir(brand_folder):
        brand_path = os.path.join(brand_folder, brand)
        if os.path.isdir(brand_path):
            for file in os.listdir(brand_path):
                if file.endswith(".csv") and today in file:
                    new_files.append(os.path.join(brand_path, file))
    return new_files
