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
import pandas as pd
import re

def get_policy_area(link):
    """
    Determine the policy area from the URL path.
    """
    if "/mergers/" in link:
        return "Merger"
    elif "/antitrust/" in link:
        return "Antitrust & Cartels"
    elif "/state_aid/" in link:
        return "State Aid"
    elif "/digital_markets_act/" in link:
        return "Digital Markets Act"
    elif "/foreign_subsidies/" in link:
        return "Foreign Subsidies"
    else:
        return "Unknown"

def main():
    # 1) Parse command‐line arguments
    p = argparse.ArgumentParser(
        description="Extract case links from an Excel file")
    p.add_argument(
        "-i", "--input", required=True,
        help="Path to the Excel file (e.g. data/cases.xlsx)")
    p.add_argument(
        "-o", "--output", required=True,
        help="Where to save the extracted links (e.g. data/extracted_links.txt)")
    args = p.parse_args()

    # 2) Debug: show where we’re running from
    print(f"Current Working Directory: {os.getcwd()}")

    # 3) Check that the input file exists
    if not os.path.isfile(args.input):
        print(f"Error: The file {args.input} does not exist.")
        return

    # 4) Load the Excel and normalize column names
    df = pd.read_excel(args.input)
    print("File loaded successfully.")
    df.columns = df.columns.str.strip()
    print("Column Names:", list(df.columns))

    # 5) Verify required columns
    required = {'Decisions', 'Case number', 'Last decision date'}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        print(f"Error: Missing required columns: {missing}")
        return

    all_links = []

    # 6) Iterate rows and extract links + metadata
    for idx, row in df.iterrows():
        decision_text = row['Decisions'] or ""
        case_number    = row['Case number']
        date_str       = str(row['Last decision date'])
        # pull YYYY from DD.MM.YYYY
        m = re.search(r'\d{2}\.\d{2}\.(\d{4})', date_str)
        year = m.group(1) if m else 'Unknown'

        # find links with or without the “published on” prefix
        links_with_date = re.findall(
            r"Decision text: EN published on \d{2}\.\d{2}\.\d{4} - "
            r"(https://ec\.europa\.eu/competition/[^ \n]*\.pdf)",
            decision_text
        )
        links_without_date = re.findall(
            r"Decision text: EN - "
            r"(https://ec\.europa\.eu/competition/[^ \n]*\.pdf)",
            decision_text
        )
        links = links_with_date + links_without_date

        if not links:
            print(f"No links found for case number {case_number}.")
            continue

        for link in links:
            area = get_policy_area(link)
            all_links.append((case_number, year, area, link))

    # 7) Write out the results
    with open(args.output, 'w') as fo:
        for case, year, area, link in all_links:
            fo.write(f"Case Number: {case}\n")
            fo.write(f"Year: {year}\n")
            fo.write(f"Policy Area: {area}\n")
            fo.write(f"Link: {link}\n\n")

    print(f"[scrape-links] Extracted {len(all_links)} links → {args.output}")

if __name__ == "__main__":
    main()