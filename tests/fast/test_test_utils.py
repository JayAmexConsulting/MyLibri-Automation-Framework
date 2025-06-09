# tests/fast/test_test_utils.py

import pytest
import sys
import os

# Add project root to sys.path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from test_report_utils import print_passed_tests, validate_test_results

# Sample data
valid_test_data = [
    {"function_name": "test_login", "outcome": "passed"},
    {"function_name": "test_logout", "outcome": "passed"},
]

invalid_test_data = [
    {"function_name": "test_login", "outcome": "FAILED"},  # Invalid casing
    {"function_name": "test_logout", "outcome": "invalid"},  # Invalid outcome
]

empty_test_data = []

@pytest.mark.fast
def test_print_passed_tests_valid(capfd):
    print_passed_tests(valid_test_data)
    out = capfd.readouterr().out
    assert "Total passed tests: 2" in out

@pytest.mark.fast
def test_validate_results_invalid(capfd):
    validate_test_results(invalid_test_data)
    out = capfd.readouterr().out
    assert "Invalid result" in out

@pytest.mark.fast
def test_print_passed_tests_empty(capfd):
    print_passed_tests(empty_test_data)
    out = capfd.readouterr().out
    assert "Total passed tests: 0" in out
