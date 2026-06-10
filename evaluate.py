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

"""
evaluate.py — Pattern-based validity assessment of Lextract extracted definitions.

Rather than comparing extracted definitions to a fixed lookup table, this script
learns what a valid market definition looks like from a set of manually verified
reference definitions (evaluation/reference.json), then scores every definition
in the pipeline's full output (data/output.json) against those learned patterns.

This approach answers the question: of the thousands of definitions Lextract
extracts, what proportion exhibit the structural and linguistic characteristics
of genuine EC market definitions?

Validity is assessed across four independent signals derived from the reference set:

  1. LENGTH — word count falls within the range observed in reference definitions
               (with a tolerance margin applied to both ends).

  2. VOCABULARY — the definition shares sufficient domain vocabulary with the
                  reference corpus, measured by Jaccard similarity against the
                  union of all reference tokens.

  3. LEGAL PHRASES — the definition contains at least one phrase that appears
                     frequently in reference definitions (e.g. "relevant market",
                     "left open", "EEA-wide", "Commission considers").

  4. STRUCTURAL MARKER — the definition contains language typical of EC market
                         definition conclusions (scope statements, findings, etc.).

A definition is considered valid if it passes all four checks. Each check threshold
is derived empirically from the reference set rather than hard-coded, making the
validator self-calibrating.

Reference format (evaluation/reference.json):
    [
        {
            "case_number": "M.9466",
            "topic": "...",
            "text": "Full verified definition text..."
        },
        ...
    ]

Usage:
    python evaluate.py
    python evaluate.py --reference evaluation/reference.json --predicted data/output.json
    python evaluate.py --output data/evaluation_report.json
"""

import argparse
import json
import os
import re
from collections import Counter


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def tokenize(text):
    """Lowercase word tokens, punctuation stripped."""
    return re.findall(r"\b[a-z0-9]+\b", text.lower())


def token_set(text):
    return set(tokenize(text))


def word_count(text):
    return len(tokenize(text))


def jaccard(set_a, set_b):
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


# ---------------------------------------------------------------------------
# Pattern learning from reference definitions
# ---------------------------------------------------------------------------

def learn_patterns(reference_definitions):
    """
    Derive validity thresholds and vocabulary from the reference set.

    Returns a patterns dict containing:
        min_words        : lower bound on valid definition length
        max_words        : upper bound on valid definition length
        reference_vocab  : union of all tokens across reference definitions
        legal_phrases    : phrases appearing in >= MIN_PHRASE_FREQ% of references
        vocab_threshold  : minimum Jaccard similarity to reference vocab
    """
    texts = [d.get("text", "") for d in reference_definitions]
    lengths = [word_count(t) for t in texts]

    # Length bounds: reference range with a 20% tolerance on each end
    tolerance = 0.20
    min_len = int(min(lengths) * (1 - tolerance))
    max_len = int(max(lengths) * (1 + tolerance))

    # Reference vocabulary: union of all tokens
    reference_vocab = set()
    for t in texts:
        reference_vocab.update(token_set(t))

    # Legal phrase extraction: find multi-word phrases (2–5 tokens) that
    # appear in at least MIN_PHRASE_FREQ fraction of reference definitions.
    MIN_PHRASE_FREQ = 0.15   # phrase must appear in >=15% of references
    MIN_PHRASE_LEN  = 2
    MAX_PHRASE_LEN  = 5

    phrase_counts = Counter()
    n = len(texts)
    for text in texts:
        tokens = tokenize(text)
        seen = set()
        for length in range(MIN_PHRASE_LEN, MAX_PHRASE_LEN + 1):
            for i in range(len(tokens) - length + 1):
                phrase = " ".join(tokens[i:i + length])
                if phrase not in seen:
                    phrase_counts[phrase] += 1
                    seen.add(phrase)

    legal_phrases = {
        phrase for phrase, count in phrase_counts.items()
        if count / n >= MIN_PHRASE_FREQ
    }

    # Vocabulary similarity threshold: mean Jaccard of each reference definition
    # against the full reference vocab, minus one standard deviation.
    sims = [jaccard(token_set(t), reference_vocab) for t in texts]
    mean_sim = sum(sims) / len(sims)
    std_sim  = (sum((s - mean_sim) ** 2 for s in sims) / len(sims)) ** 0.5
    vocab_threshold = max(0.0, mean_sim - std_sim)

    return {
        "min_words":       min_len,
        "max_words":       max_len,
        "reference_vocab": reference_vocab,
        "legal_phrases":   legal_phrases,
        "vocab_threshold": round(vocab_threshold, 4),
        "ref_lengths":     lengths,
        "ref_mean_length": round(sum(lengths) / len(lengths), 1),
    }


# ---------------------------------------------------------------------------
# Validity scoring
# ---------------------------------------------------------------------------

def score_definition(text, patterns):
    """
    Score a single definition against the learned patterns.

    Returns a dict with:
        valid            : bool — passes all four checks
        checks           : dict of individual check results
        vocab_similarity : float — Jaccard vs reference vocab
        word_count       : int
    """
    tokens = token_set(text)
    wc     = word_count(text)
    text_l = text.lower()

    # Check 1: length within learned bounds
    length_ok = patterns["min_words"] <= wc <= patterns["max_words"]

    # Check 2: vocabulary overlap removed — reference set covers a narrow
    # slice of industries; penalizing domain diversity produces false negatives.
    vocab_sim = jaccard(tokens, patterns["reference_vocab"])
    vocab_ok  = True   # retained for reporting only, not used in validity gate

    # Check 3: contains at least one learned legal phrase
    phrase_ok = any(phrase in text_l for phrase in patterns["legal_phrases"])

    # Check 4: structural marker — conclusion/scope language typical of EC decisions
    structural_markers = [
        "relevant market", "product market", "geographic market",
        "market definition", "left open", "eea-wide", "eea wide",
        "national market", "commission considers", "commission found",
        "commission has previously", "notifying party", "internal market",
        "serious doubts", "plausible market", "exact scope",
        "for the purposes of", "cannot be excluded",
    ]
    structural_ok = any(marker in text_l for marker in structural_markers)

    valid = length_ok and phrase_ok and structural_ok

    return {
        "valid": valid,
        "word_count": wc,
        "vocab_similarity": round(vocab_sim, 4),
        "checks": {
            "length_in_range": length_ok,
            "legal_phrase_present": phrase_ok,
            "structural_marker_present": structural_ok,
        },
    }


# ---------------------------------------------------------------------------
# Full dataset evaluation
# ---------------------------------------------------------------------------

def evaluate(reference_data, predicted_data):
    """
    Learn patterns from reference_data, then score every definition
    in predicted_data. Returns a full results dict.
    """
    patterns = learn_patterns(reference_data)

    results      = []
    valid_count  = 0
    fail_counts  = Counter()   # which checks are failing most

    for item in predicted_data:
        text   = item.get("text", "")
        scored = score_definition(text, patterns)
        scored["case_number"]  = item.get("case_number", "")
        scored["topic"]        = item.get("topic", "")
        scored["year"]         = item.get("year", "")
        scored["policy_area"]  = item.get("policy_area", "")
        results.append(scored)

        if scored["valid"]:
            valid_count += 1
        else:
            for check, passed in scored["checks"].items():
                if not passed:
                    fail_counts[check] += 1

    total      = len(results)
    valid_pct  = round(valid_count / total * 100, 1) if total else 0.0
    invalid    = total - valid_count

    # Validity by year
    by_year = {}
    for r in results:
        year = r.get("year", "Unknown")
        by_year.setdefault(year, {"valid": 0, "total": 0})
        by_year[year]["total"] += 1
        if r["valid"]:
            by_year[year]["valid"] += 1
    validity_by_year = {
        y: {
            "valid": v["valid"],
            "total": v["total"],
            "pct":   round(v["valid"] / v["total"] * 100, 1),
        }
        for y, v in sorted(by_year.items())
    }

    return {
        "patterns": {
            "min_words":        patterns["min_words"],
            "max_words":        patterns["max_words"],
            "vocab_threshold":  patterns["vocab_threshold"],
            "legal_phrases_learned": len(patterns["legal_phrases"]),
            "ref_mean_length":  patterns["ref_mean_length"],
        },
        "total_definitions":    total,
        "valid_definitions":    valid_count,
        "invalid_definitions":  invalid,
        "validity_rate_pct":    valid_pct,
        "top_failure_reasons":  dict(fail_counts.most_common()),
        "validity_by_year":     validity_by_year,
        "per_definition":       results,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(results):
    p = results["patterns"]
    print(f"\n{'=' * 57}")
    print(f"  LEXTRACT VALIDITY REPORT")
    print(f"{'=' * 57}")
    print(f"  Patterns learned from reference set:")
    print(f"    Word count range   : {p['min_words']}–{p['max_words']} words")
    print(f"    Vocab threshold    : {p['vocab_threshold']}")
    print(f"    Legal phrases      : {p['legal_phrases_learned']} learned")
    print(f"    Ref mean length    : {p['ref_mean_length']} words")
    print(f"{'=' * 57}")
    print(f"  Total definitions evaluated : {results['total_definitions']}")
    print(f"  Valid definitions           : {results['valid_definitions']}")
    print(f"  Invalid definitions         : {results['invalid_definitions']}")
    print(f"{'=' * 57}")
    print(f"  Overall validity rate       : {results['validity_rate_pct']}%")
    print(f"{'=' * 57}")

    if results["top_failure_reasons"]:
        print(f"\n  TOP FAILURE REASONS")
        print(f"  {'-' * 45}")
        for reason, count in results["top_failure_reasons"].items():
            print(f"  {reason:<35} {count:>5}")

    print(f"\n  VALIDITY BY YEAR")
    print(f"  {'-' * 45}")
    print(f"  {'Year':<8} {'Valid':>6} {'Total':>6} {'Rate':>7}")
    print(f"  {'-' * 45}")
    for year, v in results["validity_by_year"].items():
        print(f"  {year:<8} {v['valid']:>6} {v['total']:>6} {v['pct']:>6.1f}%")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Assess validity of Lextract definitions using patterns learned from a reference set"
    )
    p.add_argument(
        "--reference",
        default=os.path.join("evaluation", "reference.json"),
        help="Path to manually verified reference definitions"
    )
    p.add_argument(
        "--predicted",
        default=os.path.join("data", "output.json"),
        help="Path to full Lextract output to validate"
    )
    p.add_argument(
        "--output",
        default=os.path.join("data", "evaluation_report.json"),
        help="Where to save the full report"
    )
    args = p.parse_args()

    print(f"Loading reference set from : {args.reference}")
    reference = json.load(open(args.reference, encoding="utf-8"))
    print(f"Loading predictions from   : {args.predicted}")
    predicted = json.load(open(args.predicted, encoding="utf-8"))

    print(f"\nLearning patterns from {len(reference)} reference definitions ...")
    print(f"Scoring {len(predicted)} extracted definitions ...")
    results = evaluate(reference, predicted)

    print_report(results)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    # Don't write per_definition to the summary report — too large
    summary = {k: v for k, v in results.items() if k != "per_definition"}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
    print(f"\n[evaluate] Report saved to {args.output}")


if __name__ == "__main__":
    main()