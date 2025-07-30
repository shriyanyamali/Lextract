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
from unittest import mock
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from scripts import scrape_individual


def test_scrape_individual_main(tmp_path):
    # Setup input and output directories
    indir = tmp_path / "extracted_sections"
    outdir = tmp_path / "json"
    indir.mkdir()
    outdir.mkdir()

    input_file = indir / "extract-sections_79_batch_0.txt"
    input_file.write_text(
        "Case Number: M.1234\nYear: 2024\nPolicy Area: merger\nLink: https://fake.url\n\n"
        "This is a mock input text to simulate a real section."
    )

    fake_response_text = """[
        {
            "case_number": "M.1234",
            "year": "2024",
            "policy_area": "merger",
            "link": "https://fake.url",
            "topic": "Mock Topic",
            "text": "This is the extracted mock market definition."
        }
    ]"""

    mock_response = mock.Mock()
    mock_response.text = fake_response_text

    with mock.patch("scripts.scrape_individual.generate_content", return_value=mock_response):
        sys.argv = [
            "scrape_individual.py",
            "--indir", str(indir),
            "--outdir", str(outdir),
            "--model", "mock-model"
        ]
        scrape_individual.main()

    # Check if output file was created
    output_file = outdir / "extract-definitions_79_batch_0.json"
    assert output_file.exists()

    content = output_file.read_text()
    assert '"case_number": "M.1234"' in content
    assert '"topic": "Mock Topic"' in content
