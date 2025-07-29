import os
import sys
import json
import pytest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from scripts import json_merge


def test_combine_json_files_merges_valid_lists(tmp_path):
    input_dir = tmp_path / "json"
    input_dir.mkdir()
    file1 = input_dir / "file1.json"
    file2 = input_dir / "file2.json"

    file1.write_text(json.dumps([{"a": 1}, {"b": 2}]))
    file2.write_text(json.dumps([{"c": 3}]))

    output_file = tmp_path / "data" / "output.json"
    json_merge.combine_json_files(str(input_dir), str(output_file))

    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert sorted(data, key=lambda d: list(d.keys())[0]) == [
    {"a": 1}, {"b": 2}, {"c": 3}
    ]


def test_combine_json_files_skips_invalid_json(tmp_path, capsys):
    input_dir = tmp_path / "json"
    input_dir.mkdir()
    bad_file = input_dir / "bad.json"
    bad_file.write_text("{this is not valid JSON}")

    output_file = tmp_path / "data" / "output.json"
    json_merge.combine_json_files(str(input_dir), str(output_file))

    captured = capsys.readouterr().out
    assert "JSONDecodeError" in captured
    assert output_file.exists()
    assert json.loads(output_file.read_text()) == []  # No valid data


def test_combine_json_files_skips_non_list_json(tmp_path, capsys):
    input_dir = tmp_path / "json"
    input_dir.mkdir()
    bad_file = input_dir / "bad.json"
    bad_file.write_text(json.dumps({"not": "a list"}))

    output_file = tmp_path / "data" / "output.json"
    json_merge.combine_json_files(str(input_dir), str(output_file))

    captured = capsys.readouterr().out
    assert "not a list of dictionaries" in captured
    assert json.loads(output_file.read_text()) == []  # Skip bad file
