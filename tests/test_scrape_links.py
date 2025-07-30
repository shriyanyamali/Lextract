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
import tempfile
import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from scripts.scrape_links import get_policy_area, main as scrape_links_main

def test_get_policy_area():
    assert get_policy_area("https://ec.europa.eu/competition/mergers/abc.pdf") == "Merger"
    assert get_policy_area("https://ec.europa.eu/competition/antitrust/abc.pdf") == "Antitrust & Cartels"
    assert get_policy_area("https://ec.europa.eu/competition/state_aid/abc.pdf") == "State Aid"
    assert get_policy_area("https://ec.europa.eu/competition/digital_markets_act/abc.pdf") == "Digital Markets Act"
    assert get_policy_area("https://ec.europa.eu/competition/foreign_subsidies/abc.pdf") == "Foreign Subsidies"
    assert get_policy_area("https://ec.europa.eu/competition/unknownpath/abc.pdf") == "Unknown"

def test_scrape_links_main(tmp_path, capsys):

    # Mock Excel data
    df = pd.DataFrame({
        "Decisions": [
            "Decision text: EN - https://ec.europa.eu/competition/mergers/example.pdf"
        ],
        "Case number": ["M.10000"],
        "Last decision date": ["01.01.2024"]
    })

    input_path = tmp_path / "cases.xlsx"
    output_path = tmp_path / "extracted_links.txt"

    df.to_excel(input_path, index=False)

    # Run logic
    sys.argv = [
        "scrape_links.py",
        "-i", str(input_path),
        "-o", str(output_path)
    ]
    scrape_links_main()

    captured = capsys.readouterr()
    assert "Extracted 1 links" in captured.out

    # Check file content
    output_text = output_path.read_text()
    assert "Case Number: M.10000" in output_text
    assert "Policy Area: Merger" in output_text
    assert "Link: https://ec.europa.eu/competition/mergers/example.pdf" in output_text

def test_missing_required_columns(tmp_path, capsys):
    df = pd.DataFrame({
        "Decisions": ["Some text"],
        "Last decision date": ["01.01.2023"]
    })

    input_path = tmp_path / "bad_cases.xlsx"
    output_path = tmp_path / "should_not_exist.txt"

    df.to_excel(input_path, index=False)

    sys.argv = [
        "scrape_links.py",
        "-i", str(input_path),
        "-o", str(output_path)
    ]
    scrape_links_main()

    captured = capsys.readouterr()
    assert "Missing required columns" in captured.out
    assert not output_path.exists()
