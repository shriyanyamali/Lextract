# ------------------------------------------------------------------------------------------
#
# Lextract - Extracts market definitions from European Commission's decision PDFs
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

import csv
import json
import os
import re
import sqlite3
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from export import (
    export_csv,
    export_jsonl,
    export_sqlite,
    export_bibtex,
    export_ris,
    load_data,
    _bibtex_key,
)

SAMPLE = [
    {
        "case_number": "M.100",
        "year": "2021",
        "policy_area": "Merger",
        "link": "https://ec.europa.eu/competition/mergers/cases/m100.pdf",
        "topic": "Wholesale supply of widgets",
        "text": "The Commission considers that the relevant product market is the wholesale supply of widgets.",
    },
    {
        "case_number": "M.200",
        "year": "2022",
        "policy_area": "Antitrust",
        "link": "https://ec.europa.eu/competition/antitrust/cases/m200.pdf",
        "topic": "Retail distribution of gadgets",
        "text": "The relevant geographic market is national in scope for the retail distribution of gadgets.",
    },
]

def test_load_data_valid(tmp_path):
    f = tmp_path / "output.json"
    f.write_text(json.dumps(SAMPLE))
    result = load_data(str(f))
    assert len(result) == 2
    assert result[0]["case_number"] == "M.100"


def test_load_data_missing_file():
    with pytest.raises(FileNotFoundError):
        load_data("nonexistent/path/output.json")


def test_load_data_not_a_list(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({"not": "a list"}))
    with pytest.raises(ValueError):
        load_data(str(f))

def test_export_csv_creates_file(tmp_path):
    export_csv(SAMPLE, str(tmp_path))
    out = tmp_path / "output.csv"
    assert out.exists()


def test_export_csv_correct_rows(tmp_path):
    export_csv(SAMPLE, str(tmp_path))
    with open(tmp_path / "output.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["case_number"] == "M.100"
    assert rows[1]["year"] == "2022"


def test_export_csv_has_all_fields(tmp_path):
    export_csv(SAMPLE, str(tmp_path))
    with open(tmp_path / "output.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
    for field in ["case_number", "year", "policy_area", "link", "topic", "text"]:
        assert field in fields

def test_export_jsonl_creates_file(tmp_path):
    export_jsonl(SAMPLE, str(tmp_path))
    assert (tmp_path / "output.jsonl").exists()


def test_export_jsonl_one_record_per_line(tmp_path):
    export_jsonl(SAMPLE, str(tmp_path))
    lines = (tmp_path / "output.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_export_jsonl_valid_json_per_line(tmp_path):
    export_jsonl(SAMPLE, str(tmp_path))
    lines = (tmp_path / "output.jsonl").read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        obj = json.loads(line)
        assert "case_number" in obj
        assert "text" in obj

def test_export_sqlite_creates_file(tmp_path):
    export_sqlite(SAMPLE, str(tmp_path))
    assert (tmp_path / "output.db").exists()


def test_export_sqlite_correct_row_count(tmp_path):
    export_sqlite(SAMPLE, str(tmp_path))
    conn = sqlite3.connect(str(tmp_path / "output.db"))
    count = conn.execute("SELECT COUNT(*) FROM definitions").fetchone()[0]
    conn.close()
    assert count == 2


def test_export_sqlite_correct_schema(tmp_path):
    export_sqlite(SAMPLE, str(tmp_path))
    conn = sqlite3.connect(str(tmp_path / "output.db"))
    cols = [row[1] for row in conn.execute("PRAGMA table_info(definitions)").fetchall()]
    conn.close()
    for col in ["case_number", "year", "policy_area", "link", "topic", "text"]:
        assert col in cols


def test_export_sqlite_queryable(tmp_path):
    export_sqlite(SAMPLE, str(tmp_path))
    conn = sqlite3.connect(str(tmp_path / "output.db"))
    rows = conn.execute(
        "SELECT case_number FROM definitions WHERE year='2021'"
    ).fetchall()
    conn.close()
    assert rows == [("M.100",)]


def test_export_sqlite_overwrites_existing(tmp_path):
    export_sqlite(SAMPLE, str(tmp_path))
    export_sqlite(SAMPLE, str(tmp_path))  # second run should not error or double rows
    conn = sqlite3.connect(str(tmp_path / "output.db"))
    count = conn.execute("SELECT COUNT(*) FROM definitions").fetchone()[0]
    conn.close()
    assert count == 2

def test_export_bibtex_creates_file(tmp_path):
    export_bibtex(SAMPLE, str(tmp_path))
    assert (tmp_path / "output.bib").exists()


def test_export_bibtex_contains_entries(tmp_path):
    export_bibtex(SAMPLE, str(tmp_path))
    content = (tmp_path / "output.bib").read_text(encoding="utf-8")
    assert content.count("@misc{") == 2


def test_export_bibtex_contains_required_fields(tmp_path):
    export_bibtex(SAMPLE, str(tmp_path))
    content = (tmp_path / "output.bib").read_text(encoding="utf-8")
    assert "author" in content
    assert "title" in content
    assert "year" in content
    assert "url" in content
    assert "abstract" in content


def test_bibtex_key_is_unique_for_different_items():
    key1 = _bibtex_key(SAMPLE[0], 0)
    key2 = _bibtex_key(SAMPLE[1], 1)
    assert key1 != key2


def test_bibtex_key_no_special_characters():
    key = _bibtex_key(SAMPLE[0], 0)
    assert re.match(r'^[a-zA-Z0-9]+$', key), f"Key contains invalid chars: {key}"

def test_export_ris_creates_file(tmp_path):
    export_ris(SAMPLE, str(tmp_path))
    assert (tmp_path / "output.ris").exists()


def test_export_ris_contains_records(tmp_path):
    export_ris(SAMPLE, str(tmp_path))
    content = (tmp_path / "output.ris").read_text(encoding="utf-8")
    assert content.count("TY  - GOVDOC") == 2
    assert content.count("ER  - ") == 2


def test_export_ris_contains_required_tags(tmp_path):
    export_ris(SAMPLE, str(tmp_path))
    content = (tmp_path / "output.ris").read_text(encoding="utf-8")
    for tag in ["TY  -", "AU  -", "TI  -", "PY  -", "UR  -", "AB  -", "ER  -"]:
        assert tag in content

def test_main_format_all(tmp_path):
    input_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(SAMPLE))
    output_dir = tmp_path / "exports"

    sys.argv = [
        "export.py",
        "--format", "all",
        "--input", str(input_file),
        "--output", str(output_dir),
    ]

    import export as ex
    ex.main()

    assert (output_dir / "output.csv").exists()
    assert (output_dir / "output.jsonl").exists()
    assert (output_dir / "output.db").exists()
    assert (output_dir / "output.bib").exists()
    assert (output_dir / "output.ris").exists()


def test_main_single_format(tmp_path):
    input_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(SAMPLE))
    output_dir = tmp_path / "exports"

    sys.argv = [
        "export.py",
        "--format", "csv",
        "--input", str(input_file),
        "--output", str(output_dir),
    ]

    import export as ex
    ex.main()

    assert (output_dir / "output.csv").exists()
    assert not (output_dir / "output.jsonl").exists()