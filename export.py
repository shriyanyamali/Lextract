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
import csv
import json
import os
import re
import sqlite3

SUPPORTED_FORMATS = ["csv", "jsonl", "parquet", "sqlite", "bibtex", "ris", "all"]

def load_data(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array at the top level of the input file.")
    return data


def ensure_output_dir(path):
    os.makedirs(path, exist_ok=True)

def export_csv(data, output_dir):
    path = os.path.join(output_dir, "output.csv")
    fieldnames = ["case_number", "year", "policy_area", "link", "topic", "text"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)
    print(f"[export] CSV       → {path}  ({len(data)} rows)")
    return path


def export_jsonl(data, output_dir):
    path = os.path.join(output_dir, "output.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[export] JSONL     → {path}  ({len(data)} records)")
    return path


def export_parquet(data, output_dir):
    try:
        import pandas as pd
    except ImportError:
        print("[export] Parquet skipped — pandas not installed. Run: pip install pandas pyarrow")
        return None
    try:
        import pyarrow
    except ImportError:
        print("[export] Parquet skipped — pyarrow not installed. Run: pip install pyarrow")
        return None

    path = os.path.join(output_dir, "output.parquet")
    df = pd.DataFrame(data)
    df.to_parquet(path, index=False)
    print(f"[export] Parquet   → {path}  ({len(df)} rows, {df.memory_usage(deep=True).sum() // 1024} KB in memory)")
    return path


def export_sqlite(data, output_dir):
    path = os.path.join(output_dir, "output.db")
    if os.path.exists(path):
        os.remove(path)

    conn = sqlite3.connect(path)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE definitions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT,
            year        TEXT,
            policy_area TEXT,
            link        TEXT,
            topic       TEXT,
            text        TEXT
        )
    """)
    cur.execute("CREATE INDEX idx_case   ON definitions (case_number)")
    cur.execute("CREATE INDEX idx_year   ON definitions (year)")
    cur.execute("CREATE INDEX idx_policy ON definitions (policy_area)")

    rows = [
        (
            item.get("case_number", ""),
            item.get("year", ""),
            item.get("policy_area", ""),
            item.get("link", ""),
            item.get("topic", ""),
            item.get("text", ""),
        )
        for item in data
    ]
    cur.executemany(
        "INSERT INTO definitions (case_number, year, policy_area, link, topic, text) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows
    )
    conn.commit()
    conn.close()
    print(f"[export] SQLite    → {path}  ({len(rows)} rows, table: definitions)")
    return path


def _bibtex_key(item, index):
    case = re.sub(r"[^a-zA-Z0-9]", "", item.get("case_number", f"case{index}"))
    year = item.get("year", "0000")
    topic_words = re.findall(r"[a-zA-Z]+", item.get("topic", ""))
    topic_slug = topic_words[0].lower() if topic_words else "def"
    return f"lextract{case}{year}{topic_slug}{index}"


def export_bibtex(data, output_dir):
    path = os.path.join(output_dir, "output.bib")
    with open(path, "w", encoding="utf-8") as f:
        for i, item in enumerate(data):
            key      = _bibtex_key(item, i)
            case     = item.get("case_number", "")
            year     = item.get("year", "")
            topic    = item.get("topic", "").replace("{", "\\{").replace("}", "\\}")
            link     = item.get("link", "")
            area     = item.get("policy_area", "")
            text     = item.get("text", "").replace("{", "\\{").replace("}", "\\}")

            f.write(f"@misc{{{key},\n")
            f.write(f"  author       = {{{{European Commission}}}},\n")
            f.write(f"  title        = {{{topic}}},\n")
            f.write(f"  year         = {{{year}}},\n")
            f.write(f"  howpublished = {{EC {area} Decision {case}}},\n")
            f.write(f"  url          = {{{link}}},\n")
            f.write(f"  abstract     = {{{text}}},\n")
            f.write(f"  note         = {{Extracted by Lextract}}\n")
            f.write("}\n\n")
    print(f"[export] BibTeX    → {path}  ({len(data)} entries)")
    return path


def export_ris(data, output_dir):
    path = os.path.join(output_dir, "output.ris")
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write("TY  - GOVDOC\n")
            f.write(f"AU  - European Commission\n")
            f.write(f"TI  - {item.get('topic', '')}\n")
            f.write(f"PY  - {item.get('year', '')}\n")
            f.write(f"UR  - {item.get('link', '')}\n")
            f.write(f"AB  - {item.get('text', '')}\n")
            f.write(f"N1  - Case: {item.get('case_number', '')} | "
                    f"Policy area: {item.get('policy_area', '')} | "
                    f"Extracted by Lextract\n")
            f.write("ER  - \n\n")
    print(f"[export] RIS       → {path}  ({len(data)} records)")
    return path

EXPORTERS = {
    "csv":     export_csv,
    "jsonl":   export_jsonl,
    "parquet": export_parquet,
    "sqlite":  export_sqlite,
    "bibtex":  export_bibtex,
    "ris":     export_ris,
}


def run_export(fmt, data, output_dir):
    if fmt not in EXPORTERS:
        print(f"[export] Unknown format: {fmt}. Choose from: {', '.join(EXPORTERS)}")
        return
    EXPORTERS[fmt](data, output_dir)

def main():
    p = argparse.ArgumentParser(
        description="Export Lextract output.json to multiple research-friendly formats"
    )
    p.add_argument(
        "--format", "-f",
        choices=SUPPORTED_FORMATS,
        required=True,
        help=(
            "Export format: csv, jsonl, parquet, sqlite, bibtex, ris, or all. "
            "csv=Excel/Stata/R; jsonl=NLP pipelines; parquet=large-scale empirical work; "
            "sqlite=local SQL queries; bibtex/ris=citation managers."
        )
    )
    p.add_argument(
        "--input", "-i",
        default=os.path.join("data", "output.json"),
        help="Path to Lextract output JSON (default: data/output.json)"
    )
    p.add_argument(
        "--output", "-o",
        default="exports",
        help="Directory to write exported files (default: exports/)"
    )
    args = p.parse_args()

    print(f"Loading data from {args.input} ...")
    data = load_data(args.input)
    print(f"Loaded {len(data)} definitions.")

    ensure_output_dir(args.output)

    if args.format == "all":
        for fmt in EXPORTERS:
            run_export(fmt, data, args.output)
    else:
        run_export(args.format, data, args.output)

    print(f"\n[export] Done. Files written to {args.output}/")


if __name__ == "__main__":
    main()