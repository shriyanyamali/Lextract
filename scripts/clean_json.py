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

import argparse
import os
import glob

def clean_file(path):
    """
    Remove leading ```json and trailing ``` fences from a JSON file.
    """
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Drop leading ```json fence
    if lines and lines[0].strip().startswith('```json'):
        lines = lines[1:]
    # Drop trailing ``` fence
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]

    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"[clean] Cleaned {os.path.basename(path)}")


def main():
    p = argparse.ArgumentParser(
        description="Remove markdown fences from all .json files in a directory"
    )
    p.add_argument(
        "--indir", default="json",
        help="Directory containing .json files to clean"
    )
    args = p.parse_args()

    pattern = os.path.join(args.indir, '*.json')
    files = glob.glob(pattern)
    if not files:
        print(f"No JSON files found in {args.indir}")
        return

    for path in sorted(files):
        clean_file(path)

if __name__ == '__main__':
    main()