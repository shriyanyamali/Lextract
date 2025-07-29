import pytest
import os
from io import BytesIO
from PyPDF2 import PdfWriter

class DummyResponse:
    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code

class DummyReader:
    def __init__(self, pages):
        self.pages = pages

class DummyPage:
    def __init__(self, text):
        self._text = text
    def extract_text(self):
        return self._text

@pytest.fixture(autouse=True)
def preserve_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    yield

@pytest.fixture
def sample_pdf_bytes():
    writer = PdfWriter()
    for _ in range(4):
        writer.add_blank_page(width=72, height=72)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()

@pytest.fixture
def short_pdf_bytes():
    writer = PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=72, height=72)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()
