def print_failed_tests(test_results):
    fail_count = 0
    for test_id, result in test_results.items():
        if result == "fail":
            print(f"Test Case {test_id} - Result: {result}")
            fail_count += 1
    print(f"\nTotal failed tests: {fail_count}")