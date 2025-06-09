# tests/conftest.py

import csv, json
from datetime import datetime
from pathlib import Path

def pytest_sessionfinish(session, exitstatus):
    results = getattr(session.config, "_results", [])

    if not results:
        print("⚠️ No test results to export.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("test_reports").mkdir(exist_ok=True)

    csv_path = f"test_reports/test_report_{timestamp}.csv"
    json_path = f"test_reports/test_report_{timestamp}.json"

    with open(csv_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("📝 Test results exported to:")
    print(f" - CSV:  {csv_path}")
    print(f" - JSON: {json_path}")
