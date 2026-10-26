# ------------------------------------------------------------------------------------------
#
# Lextract - Extracts market definitions from European Commission's decision PDFs
#
# Copyright (C) 2025 Shriyan Yamali
#
# Licensed under the GNU Affero General Public License v3 (see LICENSE).
#
# ------------------------------------------------------------------------------------------
"""
Baseline: single-call extraction (ablation of the two-stage design).

Sends the WHOLE decision text (a batch file from data/extracted_batches/) to the
model with the definition-extraction prompt of call 2, skipping call 1. The output
has the same JSON shape as the main pipeline, so it can be merged with
scripts/json_merge.py and scored with evaluate.py and verify_fidelity.py in exactly
the same way, which gives a like-for-like comparison of

    two-stage (section identification + extraction)   vs.   single pass

Status: prepared, NOT run for the LDA 2026 paper (requires API budget).

Usage
    export GEMINI_API_KEY=...
    python baselines/single_pass.py --indir data/extracted_batches --outdir baselines/out_single_pass
    python scripts/json_merge.py            # (point it at baselines/out_single_pass, or copy files to json/)
    python evaluate.py --predicted baselines/out_single_pass/merged.json
    python verify_fidelity.py --input baselines/out_single_pass/merged.json

Use --model to try other Gemini models (e.g. gemini-2.5-flash, gemini-2.5-pro).
"""

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import google.generativeai as genai  # noqa: E402
from scripts.scrape_individual import generate_content  # noqa: E402  (reuses the exact call-2 prompt)


def main():
    p = argparse.ArgumentParser(description="Single-pass extraction baseline")
    p.add_argument("--indir", default=os.path.join("data", "extracted_batches"))
    p.add_argument("--outdir", default=os.path.join("baselines", "out_single_pass"))
    p.add_argument("--model", default="gemini-2.0-flash")
    p.add_argument("--limit", type=int, default=0, help="Process only the first N batch files (for a pilot)")
    args = p.parse_args()

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(model_name=args.model)
    os.makedirs(args.outdir, exist_ok=True)

    files = sorted(glob.glob(os.path.join(args.indir, "pdf_texts_*_batch_*.txt")))
    if args.limit:
        files = files[:args.limit]
    merged = []
    for path in files:
        m = re.search(r"pdf_texts_(\d+)_batch_(\d+)\.txt$", os.path.basename(path))
        out_path = os.path.join(args.outdir, f"single-pass_{m.group(1)}_batch_{m.group(2)}.json")
        text = open(path, encoding="utf-8").read()
        response = generate_content(model, text)
        raw = response.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        with open(out_path, "w", encoding="utf-8") as fo:
            fo.write(raw)
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                merged.extend(data)
        except json.JSONDecodeError as e:
            print(f"[single-pass] {os.path.basename(path)}: JSON decode error ({e}); kept raw file")
        print(f"[single-pass] {os.path.basename(path)} -> {os.path.basename(out_path)}")

    with open(os.path.join(args.outdir, "merged.json"), "w", encoding="utf-8") as fo:
        json.dump(merged, fo, indent=4, ensure_ascii=False)
    print(f"[single-pass] {len(merged)} records -> {args.outdir}/merged.json")


if __name__ == "__main__":
    main()
