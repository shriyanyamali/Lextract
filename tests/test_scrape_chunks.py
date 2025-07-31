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

import os
import sys
import pytest
from unittest import mock
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from scripts import scrape_chunks


def test_scrape_chunks_main_with_mock(tmp_path):
    # Setup input and output directories
    indir = tmp_path / "extracted_batches"
    outdir = tmp_path / "extracted_sections"
    indir.mkdir()
    outdir.mkdir()

    input_file = indir / "pdf_texts_79_batch_0.txt"
    input_file.write_text(
        "Case Number: M.5678\nYear: 2023\nPolicy Area: merger\nLink: https://fake.url\n\n"
        "This is a mock input text that contains the Market Definition section and other stuff.\n"
    )

    mock_model = mock.Mock()
    mock_model.generate_content.return_value.text = (
        "Case Number: M.5678\nYear: 2023\nPolicy Area: merger\nLink: https://fake.url\n\n"
        "Extracted Market Definition section goes here."
    )

    with mock.patch("scripts.scrape_chunks.genai.GenerativeModel", return_value=mock_model):
        sys.argv = [
            "scrape_chunks.py",
            "--indir", str(indir),
            "--outdir", str(outdir),
            "--size", "79",
            "--model", "mock-model"
        ]
        scrape_chunks.main()

    # Validate output
    expected_output = outdir / "extract-sections_79_batch_0.txt"
    assert expected_output.exists()

    content = expected_output.read_text()
    assert "Case Number: M.5678" in content
    assert "Extracted Market Definition section" in content
