import json
import os
import sys
import pytest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import unique_cases_counter


def test_count_unique_cases_prints_correct_count(tmp_path, capsys):
    test_data = [
        {"case_number": "M.123"},
        {"case_number": "M.456"},
        {"case_number": "M.123"}, # intentional duplicate
        {"case_number": "M.789"},
        {"no_case": "skip_me"}
    ]

    json_file = tmp_path / "test_cases.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)

    unique_cases_counter.count_unique_cases(json_file)

    captured = capsys.readouterr()
    assert "Found 3 unique case numbers." in captured.out
