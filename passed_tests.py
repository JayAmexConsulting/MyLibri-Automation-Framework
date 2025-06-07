# Store test results in a dictionary
test_results = {
    "T001": "pass",
    "T002": "fail",
    "T003": "blocked",
    "T004": "pass",
    "T005": "fail",
    "T006": "blocked",
    "T007": "fail",
    "T008": "pass",
    "T009": "blocked"
}

# Loop through and print only failed test cases
for test_id, result in test_results.items():
    if result == "pass":
        print(f"Test Case {test_id} - Result: {result}")

# Count failed tests
fail_count = sum(1 for result in test_results.values() if result == "fail")
print(f"\nTotal failed tests: {fail_count}")
