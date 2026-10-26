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
Build a gold-standard annotation sheet for a precision / recall / F1 study.

For N randomly chosen decision documents (seeded, so the sample is reproducible)
the script writes, per decision:

  annotation/<case>/decision.txt      full PyPDF2 text of the decision, with line numbers,
                                      so that the annotator can mark every passage that
                                      counts as a market definition (recall side)
  annotation/<case>/records.csv       every Lextract record for that decision with empty
                                      columns to fill in (precision side)

and one combined sheet  annotation/annotation_sheet.csv  with all records.

Columns to fill in (one row per Lextract record):
  verdict         TP  = correct market-definition passage, boundaries acceptable
                  TP-boundary = right passage but truncated, merged or over-extended
                  FP  = not a market definition, or not from this decision
  missed_count    (per decision, fill once) number of market-definition passages in the
                  decision that no Lextract record covers; list their line ranges in
                  missed_lines
  annotator_note  free text

Scoring (scripts/score_annotation.py is not provided; the arithmetic is simple):
  precision = TP / (TP + TP-boundary + FP)          (strict: count TP-boundary as FP)
  recall    = TP / (TP + missed_count)              (lenient: TP + TP-boundary)
  F1        = 2PR / (P + R)

Annotation unit: a *passage* is the contiguous run of paragraphs in which the Commission
(or, where the Commission adopts it, a party) states, reviews or concludes on the product
or geographic scope of one market. Competitive-assessment, remedies and procedural text
do not count. Record the unit choice in the sheet header if you deviate.

Usage
    python make_annotation_sheet.py --n 10 --seed 20261017
    python make_annotation_sheet.py --n 10 --batches data/extracted_batches   # reuse local text
"""

import argparse
import csv
import json
import os
import random
import re
from collections import defaultdict
from io import BytesIO


def decision_text(link, batches):
    if os.path.isdir(batches):
        for fn in os.listdir(batches):
            if fn.endswith(".txt"):
                with open(os.path.join(batches, fn), encoding="utf-8") as f:
                    content = f.read()
                if re.search(r"^Link:\s*" + re.escape(link) + r"\s*$", content, re.M):
                    return content.split("\n\n", 1)[1] if "\n\n" in content else content
    import requests
    from PyPDF2 import PdfReader
    resp = requests.get(link, timeout=60, allow_redirects=False)
    if resp.status_code != 200:
        return None
    reader = PdfReader(BytesIO(resp.content))
    return "".join(p.extract_text() or "" for p in reader.pages)


def main():
    p = argparse.ArgumentParser(description="Create gold-standard annotation sheets for N decisions")
    p.add_argument("--input", default=os.path.join("data", "output.json"))
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--seed", type=int, default=20261017)
    p.add_argument("--batches", default=os.path.join("data", "extracted_batches"))
    p.add_argument("--outdir", default="annotation")
    p.add_argument("--min-pages-chars", type=int, default=8000,
                   help="Skip documents with fewer characters (short-form decisions have no definitions to annotate)")
    args = p.parse_args()

    records = json.load(open(args.input, encoding="utf-8"))
    by_link = defaultdict(list)
    for i, r in enumerate(records):
        by_link[r["link"]].append((i, r))
    random.seed(args.seed)
    links = sorted(by_link)
    random.shuffle(links)

    os.makedirs(args.outdir, exist_ok=True)
    rows, chosen = [], []
    for link in links:
        if len(chosen) >= args.n:
            break
        text = decision_text(link, args.batches)
        if text is None or len(text) < args.min_pages_chars:
            continue
        case = by_link[link][0][1]["case_number"].replace("/", "_")
        d = os.path.join(args.outdir, case)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "decision.txt"), "w", encoding="utf-8") as f:
            for n, line in enumerate(text.splitlines(), 1):
                f.write(f"{n:5d}  {line}\n")
        with open(os.path.join(d, "records.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["record_index", "case_number", "topic", "text", "verdict", "missed_count", "missed_lines", "annotator_note"])
            for i, r in by_link[link]:
                w.writerow([i, r["case_number"], r["topic"], r["text"], "", "", "", ""])
                rows.append([case, link, i, r["topic"], r["text"], "", "", "", ""])
        chosen.append((case, link, len(by_link[link]), len(text)))
        print(f"[sheet] {case}: {len(by_link[link])} records, {len(text)} chars -> {d}")

    with open(os.path.join(args.outdir, "annotation_sheet.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case", "link", "record_index", "topic", "text", "verdict", "missed_count", "missed_lines", "annotator_note"])
        w.writerows(rows)
    with open(os.path.join(args.outdir, "sample.json"), "w", encoding="utf-8") as f:
        json.dump([{"case": c, "link": l, "records": n, "chars": ch} for c, l, n, ch in chosen], f, indent=2)
    print(f"\n{len(chosen)} decisions, {len(rows)} records -> {args.outdir}/annotation_sheet.csv")


if __name__ == "__main__":
    main()
