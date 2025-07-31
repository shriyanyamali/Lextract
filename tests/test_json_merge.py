# ------------------------------------------------------------------------------------------
#
# market-def-scraper - Extracts market definitions from European Commission's decision PDFs
#
# Copyright (C) 2025 Shriyan Yamali
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Contact: yamalishriyan@gmail.com
#
# ------------------------------------------------------------------------------------------

import os
import sys
import json
import pytest
import builtins
from pathlib import Path
from unittest import mock

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
    assert sorted(data, key=lambda d: list(d.keys())[0]) == [{"a": 1}, {"b": 2}, {"c": 3}]

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
    assert json.loads(output_file.read_text()) == []

def test_combine_json_files_skips_non_list_json(tmp_path, capsys):
    input_dir = tmp_path / "json"
    input_dir.mkdir()
    bad_file = input_dir / "bad.json"
    bad_file.write_text(json.dumps({"not": "a list"}))

    output_file = tmp_path / "data" / "output.json"
    json_merge.combine_json_files(str(input_dir), str(output_file))

    captured = capsys.readouterr().out
    assert "not a list of dictionaries" in captured
    assert json.loads(output_file.read_text()) == []

def test_combine_json_files_input_folder_missing(tmp_path, capsys):
    missing_dir = tmp_path / "nonexistent"
    output_file = tmp_path / "data" / "output.json"

    json_merge.combine_json_files(str(missing_dir), str(output_file))
    captured = capsys.readouterr().out
    assert f"Input folder {missing_dir}" in captured
    assert not output_file.exists()

def test_combine_json_files_output_ioerror(tmp_path, capsys):
    input_dir = tmp_path / "json"
    input_dir.mkdir()
    good_file = input_dir / "good.json"
    good_file.write_text(json.dumps([{"x": 1}]))

    output_file = tmp_path / "data" / "output.json"

    real_open = open  # Save the original open function

    def mocked_open(*args, **kwargs):
        if 'output.json' in args[0]:
            raise IOError("Disk full")
        return real_open(*args, **kwargs)

    with mock.patch("builtins.open", side_effect=mocked_open):
        json_merge.combine_json_files(str(input_dir), str(output_file))

    captured = capsys.readouterr().out
    assert "Failed to write to" in captured

def test_main_function_runs(tmp_path, monkeypatch):
    input_dir = tmp_path / "json"
    input_dir.mkdir()
    good_file = input_dir / "sample.json"
    good_file.write_text(json.dumps([{"case_number": "M.1234"}]))
    
    output_file = tmp_path / "data" / "output.json"
    output_file.parent.mkdir(parents=True)

    monkeypatch.setattr(json_merge, "combine_json_files", lambda i, o: open(output_file, "w").write("[]"))

    json_merge.main()

    assert output_file.exists()
    assert json.loads(output_file.read_text()) == []