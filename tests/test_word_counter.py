import os
import sys
import tempfile
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from utils import word_counter  # Adjust path if needed

def test_word_count_simple_file():
    content = "Hello world\nThis is a test file\nWith three lines"
    expected_count = len(content.split())

    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = word_counter.count_words(tmp_path)
        assert result == expected_count
    finally:
        os.remove(tmp_path)
