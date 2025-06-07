import pytest

import csv
import json
import os
from datetime import datetime

results = []


@pytest.fixture
def valid_test_data():
    return {
        "T001": "pass",
        "T002": "fail",
        "T003": "pass",
        "T004": "blocked"
    }

@pytest.fixture
def invalid_test_data():
    return {
        "T001": "invalid",
        "T002": "FAIL",
        "T003": "ok"
    }

@pytest.fixture
def empty_test_data():
    return {}

import csv
import pytest
from datetime import datetime

results = []

def pytest_runtest_logreport(report):
    if report.when == 'call':
        # Split the full test node ID into module + function
        module, func_name = report.nodeid.split("::")
        results.append({
            "test": report.nodeid,
            "module": module,
            "function_name": func_name,
            "outcome": report.outcome,
            "duration": round(report.duration, 3)
        })


def pytest_sessionfinish(session, exitstatus):
    os.makedirs("test_reports", exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_filename = f"test_report_{timestamp}"
    csv_path = f"test_reports/{base_filename}.csv"
    json_path = f"test_reports/{base_filename}.json"

    # Write CSV
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    # Write JSON
    with open(json_path, mode='w') as file:
        json.dump(results, file, indent=2)

    print(f"\n📝 Test results exported to:\n - CSV:  {csv_path}\n - JSON: {json_path}")
