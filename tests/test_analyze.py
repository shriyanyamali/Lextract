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

import json
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from analyze import (
    definitions_per_year,
    definitions_by_policy_area,
    top_sectors,
    avg_definition_length_per_year,
    unique_cases,
    summary_statistics,
)

SAMPLE_DATA = [
    {"case_number": "M.100", "year": "2018", "policy_area": "Merger",
     "topic": "Widgets", "text": "the relevant market for widgets is global"},
    {"case_number": "M.100", "year": "2018", "policy_area": "Merger",
     "topic": "Gadgets", "text": "the relevant market for gadgets is national in scope and well established"},
    {"case_number": "M.200", "year": "2020", "policy_area": "Merger",
     "topic": "Sprockets", "text": "sprockets are sold in a narrow regional market"},
    {"case_number": "M.300", "year": "2020", "policy_area": "Antitrust & Cartels",
     "topic": "Widgets", "text": "widget markets are global and highly competitive based on price"},
    {"case_number": "M.400", "year": "2022", "policy_area": "Merger",
     "topic": "Bolts", "text": "the bolt market is EEA wide and covers multiple segments"},
]


def test_definitions_per_year():
    result = definitions_per_year(SAMPLE_DATA)
    assert result["2018"] == 2
    assert result["2020"] == 2
    assert result["2022"] == 1


def test_definitions_by_policy_area():
    result = definitions_by_policy_area(SAMPLE_DATA)
    assert result["Merger"] == 4
    assert result["Antitrust & Cartels"] == 1


def test_top_sectors():
    result = top_sectors(SAMPLE_DATA, n=5)
    assert result["Widgets"] == 2
    assert "Gadgets" in result
    assert "Sprockets" in result


def test_top_sectors_respects_n():
    result = top_sectors(SAMPLE_DATA, n=2)
    assert len(result) <= 2


def test_avg_definition_length_per_year():
    result = avg_definition_length_per_year(SAMPLE_DATA)
    assert "2018" in result
    assert "2020" in result
    assert isinstance(result["2018"], float)


def test_unique_cases():
    assert unique_cases(SAMPLE_DATA) == 4


def test_summary_statistics():
    result = summary_statistics(SAMPLE_DATA)
    assert result["total_definitions"] == 5
    assert result["unique_cases"] == 4
    assert result["mean_definition_length_words"] > 0
    assert result["min_definition_length_words"] > 0
    assert result["max_definition_length_words"] >= result["min_definition_length_words"]


def test_main_runs_end_to_end(tmp_path):
    input_file  = tmp_path / "output.json"
    output_file = tmp_path / "analysis.json"

    input_file.write_text(json.dumps(SAMPLE_DATA))

    sys.argv = [
        "analyze.py",
        "--input", str(input_file),
        "--output", str(output_file),
        "--top-n", "5",
    ]

    import analyze as an
    an.main()

    assert output_file.exists()
    result = json.loads(output_file.read_text())
    assert "summary" in result
    assert "definitions_per_year" in result
    assert "definitions_by_policy_area" in result
    assert "top_5_sectors" in result
    assert "avg_definition_length_per_year" in result