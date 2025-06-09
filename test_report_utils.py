def print_failed_tests(test_results):
    fail_count = 0
    for test_id, result in test_results.items():
        if result == "fail":
            print(f"Test Case {test_id} - Result: {result}")
            fail_count += 1
    print(f"\nTotal failed tests: {fail_count}")


# test_report_utils.py

def print_passed_tests(test_results):
    pass_count = 0
    for result in test_results:
        if result.get("outcome") == "passed":
            print(f"✅ {result.get('function_name')} passed")
            pass_count += 1
    print(f"Total passed tests: {pass_count}")

def validate_test_results(test_results):
    valid_values = ["passed", "failed", "error", "blocked"]
    for result in test_results:
        outcome = result.get("outcome", "").lower()
        if outcome not in valid_values:
            print(f"❌ Invalid result: {result}")

