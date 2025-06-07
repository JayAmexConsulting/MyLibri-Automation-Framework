import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test_report_utils import print_passed_tests, validate_test_results


def test_pass_count_is_correct(capfd, valid_test_data):
    print_passed_tests(valid_test_data)
    out, _ = capfd.readouterr()
    assert "Total passed tests: 2" in out

def test_invalid_result_triggers_error(capfd, invalid_test_data):
    validate_test_results(invalid_test_data)
    out, _ = capfd.readouterr()
    assert "Invalid result" in out

def test_empty_input_runs_cleanly(capfd, empty_test_data):
    print_passed_tests(empty_test_data)
    out, _ = capfd.readouterr()
    assert "Total passed tests: 0" in out
