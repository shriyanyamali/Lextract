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
import pytest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from scripts import clean_json


def test_clean_file_removes_fences(tmp_path):
    json_file = tmp_path / "mock.json"
    json_file.write_text("```json\n{\"key\": \"value\"}\n```", encoding="utf-8")

    clean_json.clean_file(json_file)

    # Check cleaned content
    cleaned = json_file.read_text(encoding="utf-8")
    assert cleaned.strip() == "{\"key\": \"value\"}"


def test_clean_file_leaves_clean_file_unchanged(tmp_path):
    json_file = tmp_path / "clean.json"
    original = "{\"data\": [1, 2, 3]}"
    json_file.write_text(original, encoding="utf-8")

    clean_json.clean_file(json_file)

    assert json_file.read_text(encoding="utf-8").strip() == original


def test_main_removes_fences_from_multiple_files(tmp_path):
    f1 = tmp_path / "a.json"
    f2 = tmp_path / "b.json"
    f1.write_text("```json\n{\"a\": 1}\n```", encoding="utf-8")
    f2.write_text("```json\n{\"b\": 2}\n```", encoding="utf-8")

    sys.argv = ["clean_json.py", "--indir", str(tmp_path)]
    clean_json.main()

    assert f1.read_text(encoding="utf-8").strip() == "{\"a\": 1}"
    assert f2.read_text(encoding="utf-8").strip() == "{\"b\": 2}"
