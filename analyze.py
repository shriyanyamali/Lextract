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

import argparse
import json
import os
from collections import Counter, defaultdict


def load_data(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array at the top level of the input file.")
    return data


def definitions_per_year(data):
    counts = Counter()
    for item in data:
        year = item.get("year", "Unknown")
        counts[year] += 1
    return dict(sorted(counts.items()))


def definitions_by_policy_area(data):
    counts = Counter()
    for item in data:
        area = item.get("policy_area", "Unknown")
        counts[area] += 1
    return dict(counts.most_common())


def top_sectors(data, n=20):
    counts = Counter()
    for item in data:
        topic = item.get("topic", "").strip()
        if topic:
            counts[topic] += 1
    return dict(counts.most_common(n))


def avg_definition_length_per_year(data):
    word_counts = defaultdict(list)
    for item in data:
        year = item.get("year", "Unknown")
        text = item.get("text", "")
        word_counts[year].append(len(text.split()))
    return {
        year: round(sum(counts) / len(counts), 1)
        for year, counts in sorted(word_counts.items())
    }


def unique_cases(data):
    return len({item.get("case_number") for item in data if item.get("case_number")})


def summary_statistics(data):
    all_lengths = [len(item.get("text", "").split()) for item in data]
    total = len(data)
    return {
        "total_definitions": total,
        "unique_cases": unique_cases(data),
        "mean_definition_length_words": round(sum(all_lengths) / total, 1) if total else 0,
        "min_definition_length_words": min(all_lengths) if all_lengths else 0,
        "max_definition_length_words": max(all_lengths) if all_lengths else 0,
    }


def print_section(title, data_dict, value_label="Count"):
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print(f"{'=' * 55}")
    col_width = max((len(str(k)) for k in data_dict), default=10) + 2
    print(f"  {'Key':<{col_width}} {value_label}")
    print(f"  {'-' * (col_width - 2)}  {'-' * len(value_label)}")
    for k, v in data_dict.items():
        print(f"  {str(k):<{col_width}} {v}")


def main():
    p = argparse.ArgumentParser(
        description="Quantitative analysis of Lextract output JSON"
    )
    p.add_argument(
        "--input", default=os.path.join("data", "output.json"),
        help="Path to the merged output JSON (default: data/output.json)"
    )
    p.add_argument(
        "--output", default=os.path.join("data", "analysis.json"),
        help="Where to save the analysis results (default: data/analysis.json)"
    )
    p.add_argument(
        "--top-n", type=int, default=20,
        help="Number of top sectors to report (default: 20)"
    )
    args = p.parse_args()

    print(f"Loading data from {args.input} ...")
    data = load_data(args.input)
    print(f"Loaded {len(data)} definitions.")

    # Run all analyses
    summary    = summary_statistics(data)
    by_year    = definitions_per_year(data)
    by_area    = definitions_by_policy_area(data)
    sectors    = top_sectors(data, n=args.top_n)
    avg_length = avg_definition_length_per_year(data)

    # Print results
    print(f"\n{'=' * 55}")
    print(f"  SUMMARY")
    print(f"{'=' * 55}")
    for k, v in summary.items():
        label = k.replace("_", " ").title()
        print(f"  {label:<40} {v}")

    print_section("DEFINITIONS PER YEAR", by_year)
    print_section("DEFINITIONS BY POLICY AREA", by_area)
    print_section(f"TOP {args.top_n} MARKET SECTORS", sectors)
    print_section("AVERAGE DEFINITION LENGTH (WORDS) PER YEAR", avg_length, value_label="Avg Words")

    # Save to JSON
    results = {
        "summary": summary,
        "definitions_per_year": by_year,
        "definitions_by_policy_area": by_area,
        f"top_{args.top_n}_sectors": sectors,
        "avg_definition_length_per_year": avg_length,
    }
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    print(f"\n[analyze] Results saved to {args.output}")


if __name__ == "__main__":
    main()