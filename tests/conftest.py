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
