# =============================================================================
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
# =============================================================================

import argparse
import os
import requests
from PyPDF2 import PdfReader
from io import BytesIO
import re

# 1) PDF exclusion phrases
EXCLUSION_PHRASES = [
    "For the reasons set out in the Notice on a simplified",
    "European Commission has decided not to oppose the notified operation",
    "declare it compatible with the internal market",
    "This decision is adopted in application of Article 6(1)(b)",
    "Merger Regulation and Article 57 of the EEA Agreement"
]

def get_pdf_text(url):
    """
    Download the PDF at `url`, extract all text, and decide
    whether to exclude based on page count & exclusion phrases.
    Returns (text or None, exclusion_reason or None).
    """
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
        reader = PdfReader(BytesIO(resp.content))
        full_text = "".join(p.extract_text() or "" for p in reader.pages)
        # if exactly 3 pages, check for any exclusion phrase
        if len(reader.pages) == 3:
            low = full_text.lower()
            for phrase in EXCLUSION_PHRASES:
                if phrase.lower() in low:
                    return None, "Excluded by criteria"
        return full_text, None
    except Exception as e:
        return None, f"Error: {e}"

def main():
    # 2) Argparse
    p = argparse.ArgumentParser(
        description="Download case PDFs, extract text, and batch into files"
    )
    p.add_argument(
        "-i", "--input", required=True,
        help="Path to extracted_links.txt"
    )
    p.add_argument(
        "--datadir", default="data",
        help="Root data directory (batches → data/extracted_batches/)"
    )
    args = p.parse_args()

    # write the pdf batches into data/extracted_batches
    batch_dir = os.path.join(args.datadir, "extracted_batches")
    os.makedirs(batch_dir, exist_ok=True)
    inc_path = os.path.join(args.datadir, "included_cases.txt")
    exc_path = os.path.join(args.datadir, "excluded_cases.txt")

    # 4) Read links
    links = []
    with open(args.input, encoding="utf-8") as f:
        block = []
        for line in f:
            line = line.strip()
            if not line:
                info = {k: v for k, v in (l.split(": ",1) for l in block)}
                links.append((
                    info["Case Number"],
                    info["Year"],
                    info["Policy Area"].lower().replace(" ", "_"),
                    info["Link"]
                ))
                block = []
            else:
                block.append(line)
        # catch any trailing block
        if block:
            info = {k: v for k, v in (l.split(": ",1) for l in block)}
            links.append((
                info["Case Number"],
                info["Year"],
                info["Policy Area"].lower().replace(" ", "_"),
                info["Link"]
            ))

    # 5) Download & classify
    pdf_texts = []
    included  = []
    excluded  = []

    for case, year, area, url in links:
        print(f"[fetch] Case {case} ({area}), URL: {url}")
        text, reason = get_pdf_text(url)
        if text:
            pdf_texts.append((case, year, area, url, text))
            included.append((case, year, area, url))
            print(f"[included] Case {case} → {len(text)} chars")
        else:
            excluded.append((case, year, area, url, reason))
            print(f"[excluded] Case {case} → {reason}")

    # 6) Batch counts by area & size
    batches_79 = {}
    batches_80 = {}

    for case, year, area, url, text in pdf_texts:
        if len(text) > 80_000:
            dct, label = batches_80, "80"
        else:
            dct, label = batches_79, "79"

        dct[area] = dct.get(area, 0) + 1
        num = dct[area]
        fname = f"pdf_texts_{label}_batch_{num}.txt"
        outp = os.path.join(batch_dir, fname)

        with open(outp, "w", encoding="utf-8") as fo:
            fo.write(f"Case Number: {case}\n")
            fo.write(f"Year: {year}\n")
            fo.write(f"Policy Area: {area.capitalize()}\n")
            fo.write(f"Link: {url}\n\n")
            fo.write(text)

        print(f"[batch] wrote {fname}")

    # 7) Write included_cases.txt
    with open(inc_path, "w", encoding="utf-8") as fo:
        for case, year, area, url in included:
            fo.write(f"Case Number: {case}\n")
            fo.write(f"Year: {year}\n")
            fo.write(f"Policy Area: {area.capitalize()}\n")
            fo.write(f"Link: {url}\n\n")
    print(f"[included] {len(included)} → {inc_path}")

    # 8) Write excluded_cases.txt
    with open(exc_path, "w", encoding="utf-8") as fo:
        for case, year, area, url, reason in excluded:
            fo.write(f"Case Number: {case}\n")
            fo.write(f"Year: {year}\n")
            fo.write(f"Policy Area: {area.capitalize()}\n")
            fo.write(f"Link: {url}\n")
            fo.write(f"Reason: {reason}\n\n")
    print(f"[excluded] {len(excluded)} → {exc_path}")

    # 9) Summary
    total_79 = sum(batches_79.values())
    total_80 = sum(batches_80.values())
    total   = total_79 + total_80
    print()
    print(f"Documents <80k chars : {total_79}")
    print(f"Documents >80k chars : {total_80}")
    print(f"Total documents      : {total}")

if __name__ == "__main__":
    main()