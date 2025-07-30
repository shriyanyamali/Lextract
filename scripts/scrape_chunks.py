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
import glob
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)

DEFAULT_MODEL = "gemini-2.0-flash"

model = genai.GenerativeModel(model_name=DEFAULT_MODEL)

def extract_sections(input_path, output_path):
    """
    Read input_path, send to Gemini with the market-definition prompt,
    and write the extracted section to output_path.
    """
    text = open(input_path, encoding="utf-8").read()
    prompt = (
        "For text which I will provide, search for the first instance of the words market definition. "
        "Starting from a line before the first instance of the words market definition extract ONLY the market definition section. "
        "You can find when the market definition section starts as that is a line before the first instance of the words market definition. "
        "You can see when the market definition section ends as that is when you will see another heading. "
        "You might see some subheadings, but do not stop at the subheadings. Instead, stop at the heading. "
        "This heading typically follows the bullet point pattern of the first instance of market definition. "
        "For example, if the first instance of market definition is the following \"A. Market Definition\" then the next heading which you would stop at would be \"B. (Insert heading here)\". "
        "If the first instance of market definition was \"IV. Market Definition\" then the next heading which you would stop at would be \"V. (Insert heading here)\". "
        "Do not include the text of the heading which you stop at in the final output. "
        "Also, at the very start of the document, you will find the words \"Case Number:\" followed by the case number, the word \"Year:\" followed by the year, "
        "the phrase \"Policy Area:\" followed by the policy area, and the word \"Link:\" followed by the link. "
        "Make sure that you keep the same exact case number, year, policy area, and link in your output. "
        "You should have it so that at the top of your output file the case number, year, policy area, and link are listed. "
        "Now, based on what I just told you, extract only the market definition sections (and the case number, year, policy area, and link) from the following text:\n\n"
        + text
    )
    response = model.generate_content([prompt])
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as fo:
        fo.write(response.text)
    print(f"[chunks] Wrote extracted sections → {os.path.basename(output_path)}")


def main():
    p = argparse.ArgumentParser(
        description="Batch-extract market-definition sections from pdf_texts files using Gemini"
    )
    p.add_argument(
        "--indir", default="data/extracted_batches",
        help="Directory containing pdf_texts_<size>_batch_<n>.txt files"
    )
    p.add_argument(
        "--outdir", default="data/extracted_sections",
        help="Directory to write extract-sections_batch_<n>.txt files"
    )
    p.add_argument(
        "--size", choices=["79","80","both"], default="both",
        help="Which batch size to process: '79', '80', or 'both'"
    )
    p.add_argument(
        "--model", default=DEFAULT_MODEL,
        help="Gemini model to use (default: %(default)s)"
    )
    args = p.parse_args()

    global model
    if args.model != DEFAULT_MODEL:
        model = genai.GenerativeModel(model_name=args.model)

    if not os.path.isdir(args.indir):
        print(f"Error: indir not found: {args.indir}")
        return
    os.makedirs(args.outdir, exist_ok=True)

    # determine which size files to process
    sizes = [args.size] if args.size in ["79","80"] else ["79","80"]
    all_files = []
    for size in sizes:
        pattern = os.path.join(args.indir, f"pdf_texts_{size}_batch_*.txt")
        all_files.extend(sorted(glob.glob(pattern)))

    if not all_files:
        print(f"No files matched size={args.size} in {args.indir}")
        return

    for input_path in all_files:
        fname = os.path.basename(input_path)
        match = re.search(r"pdf_texts_(\d+)_batch_(\d+)\.txt$", fname)
        if not match:
            continue
        size_label, batch_num = match.group(1), match.group(2)

        out_fname = f"extract-sections_{size_label}_batch_{batch_num}.txt"
        output_path = os.path.join(args.outdir, out_fname)

        print(f"[chunks] Processing {fname} → {out_fname}")
        extract_sections(input_path, output_path)

if __name__ == '__main__':
    main()