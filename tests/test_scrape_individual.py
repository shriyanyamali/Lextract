import os
import sys
import pytest
from unittest import mock
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from scripts import scrape_individual


def test_scrape_individual_main(tmp_path):
    # Setup input + output directories
    indir = tmp_path / "extracted_sections"
    outdir = tmp_path / "json"
    indir.mkdir()
    outdir.mkdir()

    # Create a fake input file that matches the pattern
    input_file = indir / "extract-sections_79_batch_0.txt"
    input_file.write_text(
        "Case Number: M.1234\nYear: 2024\nPolicy Area: merger\nLink: https://fake.url\n\n"
        "This is a mock input text to simulate a real section."
    )

    # Define a fake Gemini JSON response
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

    # Patch generate_content to return fake Gemini response
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

    # Check output file was created
    output_file = outdir / "extract-definitions_79_batch_0.json"
    assert output_file.exists()

    content = output_file.read_text()
    assert '"case_number": "M.1234"' in content
    assert '"topic": "Mock Topic"' in content
