# generate_summary.py

import csv
import json
from pathlib import Path
from datetime import datetime

FAST_REPORT = Path("test_reports/fast/latest.json")
SLOW_REPORT = Path("test_reports/slow/latest.json")
OUTPUT_CSV = Path("test_reports/combined_summary.csv")
OUTPUT_JSON = Path("test_reports/combined_summary.json")

def load_json(file_path):
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_combined_report(data):
    fieldnames = ["id", "title", "author", "url", "timestamp"]
    OUTPUT_CSV.parent.mkdir(exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in data:
            writer.writerow(item)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():
    fast_data = load_json(FAST_REPORT)
    slow_data = load_json(SLOW_REPORT)
    combined = fast_data + slow_data

    now = datetime.now().isoformat()
    for item in combined:
        item.setdefault("timestamp", now)

    save_combined_report(combined)
    print(f"✅ Combined report saved to:\n→ {OUTPUT_CSV}\n→ {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
