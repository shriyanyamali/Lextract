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

import subprocess
import sys
import glob
import os

# Manually set which chunks to process: "79", "80", or "both"
# "79" for batches with <80,000 characters
# "80" for batches with >80,000 characters
# "both" to process all batches
CHUNKS_SIZE = "both"


def safe_run(cmd, description=None, input_paths=None):
    """
    Run a subprocess command if all input_paths exist; otherwise warn and skip.
    description: human‐readable name of this step (e.g. "scrape‐links")
    input_paths: list of files or directories that must exist to run
    """
    if input_paths:
        missing = [p for p in input_paths if not os.path.exists(p)]
        if missing:
            print(f"Warning: missing {', '.join(missing)}; skipping {description or cmd[1]}.")
            return

    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as e:
        print(f"Warning: file or script not found ({e.filename}); skipping {description or cmd[1]}.")
    except subprocess.CalledProcessError as e:
        print(f"Warning: step {description or cmd[1]} failed (exit {e.returncode}); continuing.")


def main():
    # 1) scrape_links.py
    safe_run(
        [sys.executable, "scripts/scrape_links.py",
         "-i", "data/cases.xlsx",
         "-o", "data/extracted_links.txt"],
        description="scrape_links",
        input_paths=["data/cases.xlsx"]
    )

    # 2) scrape_pdf_text.py
    safe_run(
        [sys.executable, "scripts/scrape_pdf_text.py",
         "-i", "data/extracted_links.txt",
         "--datadir", "data"],
        description="scrape_pdf_text",
        input_paths=["data/extracted_links.txt", "data"]
    )

    # 3) scrape_chunks.py
    safe_run(
        [sys.executable, "scripts/scrape_chunks.py",
         "--indir", "data/extracted_batches",
         "--outdir", "data/extracted_sections",
         "--size", CHUNKS_SIZE],
        description="scrape_chunks",
        input_paths=["data/extracted_batches"]
    )

    # 4) scrape_individual.py
    safe_run(
        [sys.executable, "scripts/scrape_individual.py",
         "--indir", "data/extracted_sections",
         "--outdir", "json"],
        description="scrape_individual",
        input_paths=["data/extracted_sections"]
    )

    # 5) clean_json.py
    safe_run(
        [sys.executable, "scripts/clean_json.py",
         "--indir", "json"],
        description="clean_json",
        input_paths=["json"]
    )

    # 6) json_merge.py
    safe_run(
        [sys.executable, "scripts/json_merge.py"],
        description="json_merge",
        input_paths=["json"]
    )

    batches79 = len(glob.glob(os.path.join('data', 'extracted_batches', 'pdf_texts_79_batch_*.txt')))
    batches80 = len(glob.glob(os.path.join('data', 'extracted_batches', 'pdf_texts_80_batch_*.txt')))
    
    sections = len(glob.glob(os.path.join('data', 'extracted_sections', 'extract-sections_batch_*.txt')))
    
    json_files = len(glob.glob(os.path.join('json', '*.json')))

    # This should always be 1. It will be 0 if the merge fails or is not run.
    merged = 1 if os.path.exists(os.path.join('data', 'output.json')) else 0

    print("\nPipeline complete.")
    print(f"- {batches79} x 79 batches   → data/extracted_batches/")
    print(f"- {batches80} x 80 batches   → data/extracted_batches/")
    print(f"- {sections} section files   → data/extracted_sections/")
    print(f"- {json_files} JSON files     → json/")
    print(f"- {merged} merged file        → data/output.json")


if __name__ == '__main__':
    main()