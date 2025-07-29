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
