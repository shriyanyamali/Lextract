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
from evaluate import tokenize, jaccard, learn_patterns, score_definition, evaluate


REFERENCE = [
    {"case_number": "M.100", "topic": "Widgets",
     "text": ("The Commission considers that the relevant product market for widgets "
              "is global in scope. The exact market definition can be left open since "
              "no serious doubts arise as to compatibility with the internal market "
              "under any plausible market definition. The notifying party submits that "
              "the geographic market is EEA-wide.")},
    {"case_number": "M.200", "topic": "Gadgets",
     "text": ("The Commission has previously found that the relevant market for gadgets "
              "is national in scope. For the purposes of this decision the exact scope "
              "of the product market definition can be left open. The Commission found "
              "that the geographic market is national.")},
    {"case_number": "M.300", "topic": "Sprockets",
     "text": ("The notifying party considers that the relevant market definition for "
              "sprockets encompasses EEA-wide trade. The Commission considers that the "
              "exact market definition can be left open as no serious doubts arise. "
              "The geographic scope of the relevant product market is therefore EEA-wide.")},
]


def test_tokenize_strips_punctuation_and_lowercases():
    tokens = tokenize("The Commission found, inter alia, EEA-wide markets.")
    assert "commission" in tokens
    assert "found" in tokens
    assert "," not in tokens


def test_jaccard_identical():
    s = {"a", "b", "c"}
    assert jaccard(s, s) == 1.0


def test_jaccard_disjoint():
    assert jaccard({"a", "b"}, {"c", "d"}) == 0.0


def test_jaccard_empty():
    assert jaccard(set(), set()) == 1.0


def test_learn_patterns_returns_expected_keys():
    patterns = learn_patterns(REFERENCE)
    assert "min_words" in patterns
    assert "max_words" in patterns
    assert "reference_vocab" in patterns
    assert "legal_phrases" in patterns
    assert "vocab_threshold" in patterns
    assert patterns["min_words"] >= 0
    assert patterns["max_words"] > patterns["min_words"]


def test_learn_patterns_vocab_contains_domain_terms():
    patterns = learn_patterns(REFERENCE)
    assert "commission" in patterns["reference_vocab"]
    assert "market" in patterns["reference_vocab"]


def test_learn_patterns_legal_phrases_nonempty():
    patterns = learn_patterns(REFERENCE)
    assert len(patterns["legal_phrases"]) > 0


def test_score_valid_definition():
    patterns = learn_patterns(REFERENCE)
    valid_text = (
        "The Commission considers that the relevant product market definition "
        "for bolts is EEA-wide in geographic scope. The exact market definition "
        "can be left open as no serious doubts arise as to compatibility with "
        "the internal market under any plausible market definition. The notifying "
        "party submits that national markets apply."
    )
    result = score_definition(valid_text, patterns)
    assert result["checks"]["legal_phrase_present"] is True
    assert result["checks"]["structural_marker_present"] is True
    assert result["word_count"] > 0


def test_score_invalid_short_definition():
    patterns = learn_patterns(REFERENCE)
    result = score_definition("short text", patterns)
    assert result["checks"]["length_in_range"] is False
    assert result["valid"] is False


def test_score_invalid_irrelevant_text():
    patterns = learn_patterns(REFERENCE)
    result = score_definition(
        "The weather today is sunny with a high of twenty degrees celsius "
        "and low humidity across the northern regions of the continent "
        "making it pleasant for outdoor activities and recreation.",
        patterns
    )
    assert result["valid"] is False


def test_evaluate_returns_required_keys():
    predicted = [
        {"case_number": "M.100", "topic": "Widgets", "year": "2020",
         "policy_area": "Merger",
         "text": ("The Commission considers that the relevant product market for widgets "
                  "is EEA-wide. The exact market definition can be left open since no "
                  "serious doubts arise as to compatibility with the internal market.")},
        {"case_number": "M.999", "topic": "Nonsense", "year": "2020",
         "policy_area": "Merger",
         "text": "short irrelevant text"},
    ]
    results = evaluate(REFERENCE, predicted)
    assert "total_definitions" in results
    assert "valid_definitions" in results
    assert "validity_rate_pct" in results
    assert "validity_by_year" in results
    assert "top_failure_reasons" in results
    assert results["total_definitions"] == 2


def test_evaluate_validity_rate_bounded():
    predicted = [
        {"case_number": "M.100", "topic": "Widgets", "year": "2021",
         "policy_area": "Merger",
         "text": ("The Commission considers that the relevant product market for widgets "
                  "is EEA-wide in geographic scope. The exact market definition can be "
                  "left open as no serious doubts arise as to compatibility with the "
                  "internal market under any plausible market definition.")}
    ]
    results = evaluate(REFERENCE, predicted)
    assert 0.0 <= results["validity_rate_pct"] <= 100.0


def test_main_runs_end_to_end(tmp_path):
    ref_path  = tmp_path / "reference.json"
    pred_path = tmp_path / "output.json"
    out_path  = tmp_path / "report.json"

    ref_path.write_text(json.dumps(REFERENCE))
    pred_path.write_text(json.dumps([
        {"case_number": "M.100", "topic": "Widgets", "year": "2020",
         "policy_area": "Merger",
         "text": ("The Commission considers that the relevant product market for widgets "
                  "is EEA-wide. The exact market definition can be left open since no "
                  "serious doubts arise as to compatibility with the internal market "
                  "under any plausible market definition. The notifying party agrees.")}
    ]))

    sys.argv = [
        "evaluate.py",
        "--reference", str(ref_path),
        "--predicted", str(pred_path),
        "--output", str(out_path),
    ]

    import evaluate as ev
    ev.main()

    assert out_path.exists()
    report = json.loads(out_path.read_text())
    assert "validity_rate_pct" in report
    assert report["total_definitions"] == 1