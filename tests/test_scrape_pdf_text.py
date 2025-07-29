import os
import sys
import tempfile
import builtins
import pytest
from unittest import mock
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from scripts import scrape_pdf_text

class MockPage:
    def extract_text(self):
        return "This is a mock PDF content with market definitions."

class MockPdfReader:
    def __init__(self, stream):
        self.pages = [MockPage(), MockPage(), MockPage()]  # simulate 3 pages

@pytest.fixture
def fake_pdf():
    return b"%PDF-1.4 fake pdf binary content"

@pytest.fixture
def input_links(tmp_path):
    input_file = tmp_path / "extracted_links.txt"
    input_file.write_text(
        "Case Number: M.1234\n"
        "Year: 2024\n"
        "Policy Area: merger\n"
        "Link: https://ec.europa.eu/competition/mergers/fake.pdf\n\n"
    )
    return input_file

@pytest.fixture
def setup_mock_requests_and_pypdf2(fake_pdf):
    with mock.patch("requests.get") as mock_get, \
         mock.patch("scripts.scrape_pdf_text.PdfReader", MockPdfReader):

        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.content = fake_pdf
        mock_get.return_value = mock_resp
        yield

def test_scrape_pdf_text_main(tmp_path, input_links, setup_mock_requests_and_pypdf2, capsys):
    data_dir = tmp_path
    extracted_batches = data_dir / "extracted_batches"
    included_path = data_dir / "included_cases.txt"
    excluded_path = data_dir / "excluded_cases.txt"

    sys.argv = [
        "scrape_pdf_text.py",
        "-i", str(input_links),
        "--datadir", str(data_dir)
    ]

    scrape_pdf_text.main()

    out = capsys.readouterr().out
    assert "included" in out
    assert extracted_batches.exists()
    assert included_path.exists()
    assert not excluded_path.read_text().strip().endswith("Excluded by criteria")

    # Check that a batch file was made
    batch_files = list(extracted_batches.glob("*.txt"))
    assert len(batch_files) == 1
    content = batch_files[0].read_text()
    assert "M.1234" in content
    assert "This is a mock PDF content" in content

def test_exclusion_phrase_causes_exclusion(tmp_path, fake_pdf, capsys):
    input_file = tmp_path / "extracted_links.txt"
    input_file.write_text(
        "Case Number: M.5678\n"
        "Year: 2023\n"
        "Policy Area: merger\n"
        "Link: https://ec.europa.eu/competition/mergers/exclude.pdf\n\n"
    )

    class ExclusionPage:
        def extract_text(self):
            return "This decision is adopted in application of Article 6(1)(b)"

    class ExclusionReader:
        def __init__(self, stream):
            self.pages = [ExclusionPage(), ExclusionPage(), ExclusionPage()]

    with mock.patch("requests.get") as mock_get, \
         mock.patch("scripts.scrape_pdf_text.PdfReader", ExclusionReader):

        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.content = fake_pdf
        mock_get.return_value = mock_resp

        sys.argv = [
            "scrape_pdf_text.py",
            "-i", str(input_file),
            "--datadir", str(tmp_path)
        ]

        scrape_pdf_text.main()

    out = capsys.readouterr().out
    assert "[excluded] Case M.5678" in out

    # Make sure the case was excluded
    excluded_path = tmp_path / "excluded_cases.txt"
    included_path = tmp_path / "included_cases.txt"
    batch_dir = tmp_path / "extracted_batches"

    assert excluded_path.exists()
    assert "Excluded by criteria" in excluded_path.read_text()
    assert included_path.read_text().strip() == ""
    assert not batch_dir.exists() or not any(batch_dir.iterdir())