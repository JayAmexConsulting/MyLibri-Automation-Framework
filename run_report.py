from test_report_utils import print_passed_tests, print_failed_tests, validate_test_results

# Sample test results
test_results = {
    "T001": "pass",
    "T002": "fail",
    "T003": "unknown",  # triggers validation error
    "T004": "fail"
}

# Run validation
validate_test_results(test_results)

# Generate reports
print_passed_tests(test_results)
print_failed_tests(test_results)
