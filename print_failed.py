def print_failed_tests(test_results):
    fail_count = 0
    for test_id, result in test_results.items():
        if result == "fail":
            print(f"Test Case {test_id} - Result: {result}")
            fail_count += 1
    print(f"\nTotal failed tests: {fail_count}")


def print_passed_tests(test_results):
    pass_count = 0
    for test_id, result in test_results.items():
        if result == "pass":
            print(f"Test Case {test_id} - Result: {result}")
            pass_count += 1
    print(f"\nTotal passed tests: {pass_count}")


def validate_test_results(test_results):
    valid_values = ["pass", "fail", "blocked"]
    for test_id, result in test_results.items():
        try:
            if result.lower() not in valid_values:
                raise ValueError(f"Invalid result '{result}' in test case {test_id}")
        except ValueError as e:
            print(f"❌ Error: {e}")


# -----------------------
# ONLY CALL THEM ONCE BELOW
# -----------------------

test_results = {
    "T001": "pass",
    "T002": "fail",
    "T003": "unknown",   # ← This will trigger validation error
    "T004": "fail"
}

# Run validation first
validate_test_results(test_results)

# Then print summaries
print_passed_tests(test_results)
print_failed_tests(test_results)
