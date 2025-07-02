import subprocess
import sys
import glob
import os

# Manually set which chunks to process: "79", "80", or "both"
# "79" for batches with <80,000 characters
# "80" for batches with >80,000 characters
# "both" to process all batches
CHUNKS_SIZE = "both"


def run(cmd):
    """
    Helper to run a subprocess and halt on error.
    """
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main():
    # 1) scrape-links.py
    run([
        sys.executable, "scripts/scrape-links.py",
        "-i", "data/cases.xlsx",
        "-o", "data/extracted_links.txt"
    ])

    # 2) scrape-pdf-text.py
    run([
        sys.executable, "scripts/scrape-pdf-text.py",
        "-i", "data/extracted_links.txt",
        "--datadir", "data"
    ])

    # 3) scrape-chunks.py
    run([
        sys.executable, "scripts/scrape-chunks.py",
        "--indir", "data/extracted_batches",
        "--outdir", "data/extracted_sections",
        "--size", CHUNKS_SIZE
    ])

    # 4) scrape-individual.py
    run([
        sys.executable, "scripts/scrape-individual.py",
        "--indir", "data/extracted_sections",
        "--outdir", "json"
    ])

    # 5) clean-json.py
    run([
        sys.executable, "scripts/clean-json.py",
        "--indir", "json"
    ])

    # 6) json-merge.py
    run([
        sys.executable, "scripts/json-merge.py"
    ])

    # Final summary with counts

    batches79 = len(glob.glob(os.path.join('data', 'extracted_batches', 'pdf_texts_79_batch_*.txt')))
    batches80 = len(glob.glob(os.path.join('data', 'extracted_batches', 'pdf_texts_80_batch_*.txt')))

    sections = len(glob.glob(os.path.join('data', 'extracted_sections', 'extract-sections_batch_*.txt')))

    # This number should be the same as the sections count. If it is not, some of the sections may not have been processed,
    json_files = len(glob.glob(os.path.join('json', '*.json')))

    # This should always be 1. It will be 0 if the merge fails or is not run.
    merged = 1 if os.path.exists(os.path.join('data', 'output.json')) else 0

    print("Pipeline complete.")
    print(f"- {batches79} x 79 batches → data/extracted_batches/")
    print(f"- {batches80} x 80 batches → data/extracted_batches/")
    print(f"- {sections} section files      → data/extracted_sections/")
    print(f"- {json_files} JSON files        → json/")
    print(f"- {merged} merged file           → data/output.json")

if __name__ == '__main__':
    main()