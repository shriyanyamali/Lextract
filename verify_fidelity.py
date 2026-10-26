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
Source-fidelity check: is each extracted definition actually present, verbatim,
in the text of the decision it is attributed to?

For every record in the output file the script obtains the PyPDF2 text of the
decision (from the local batch files written by scrape_pdf_text.py if present,
otherwise by downloading the PDF from the record's link), normalises both texts
to lower-case letters only (dropping whitespace, digits and punctuation so that
paragraph numbers, footnote markers and split words such as "sub -segmented"
cannot cause mismatches), and measures *coverage*: the fraction of 40-letter
windows (stride 20) of the record that occur in the source text.

Bands: verbatim >= 0.95, near_verbatim 0.80-0.95, partial 0.50-0.80, absent < 0.50.

A record in the "absent" band is not copied from its source. In the October 2026
audit every such record came from a short-form (simplified-procedure) decision
that had slipped through the exclusion filter, after which the model fabricated
plausible definitions. Use --drop-absent to write a cleaned copy of the output, and add --drop-short-form 3 to
also drop every record taken from a document of at most three pages (copied boilerplate
such as party descriptions survives the fidelity test but is not a market definition).

Examples
    python verify_fidelity.py                                   # all records, local batches or download
    python verify_fidelity.py --sample-docs 40 --seed 20261017   # random sample of 40 decision documents
    python verify_fidelity.py --drop-absent data/output_clean.json --drop-short-form 3
"""

import argparse
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from io import BytesIO

WIN, STRIDE = 40, 20
BANDS = (("verbatim", 0.95), ("near_verbatim", 0.80), ("partial", 0.50), ("absent", 0.0))


def normalise(text):
    return re.sub(r"[^a-z]", "", text.lower())


def coverage(record_text, source_norm):
    n = normalise(record_text)
    if not n:
        return 0.0, 0
    if len(n) <= WIN:
        return (1.0, 0) if n in source_norm else (0.0, 1)
    windows = [n[i:i + WIN] for i in range(0, len(n) - WIN + 1, STRIDE)]
    missing = sum(1 for w in windows if w not in source_norm)
    return 1 - missing / len(windows), missing


def band(cov):
    for name, lo in BANDS:
        if cov >= lo:
            return name
    return "absent"


def load_local_batches(batch_dir):
    """Map decision link -> (text, n_pages=None) from data/extracted_batches/*.txt."""
    texts = {}
    if not os.path.isdir(batch_dir):
        return texts
    for fn in os.listdir(batch_dir):
        if not fn.endswith(".txt"):
            continue
        with open(os.path.join(batch_dir, fn), encoding="utf-8") as f:
            content = f.read()
        m = re.search(r"^Link:\s*(\S+)", content, re.M)
        if m:
            body = content.split("\n\n", 1)[1] if "\n\n" in content else content
            texts[m.group(1)] = (body, None)
    return texts


def download_text(url):
    import requests
    from PyPDF2 import PdfReader
    resp = requests.get(url, timeout=60, allow_redirects=False)
    if resp.status_code != 200:
        return None, None, f"HTTP {resp.status_code}"
    reader = PdfReader(BytesIO(resp.content))
    return "".join(p.extract_text() or "" for p in reader.pages), len(reader.pages), None


def main():
    p = argparse.ArgumentParser(description="Check that extracted definitions occur verbatim in their source decisions")
    p.add_argument("--input", default=os.path.join("data", "output.json"), help="Lextract output file")
    p.add_argument("--batches", default=os.path.join("data", "extracted_batches"),
                   help="Directory with pdf_texts_*_batch_*.txt files (used before downloading)")
    p.add_argument("--no-download", action="store_true", help="Never download; skip records whose source is not local")
    p.add_argument("--sample-docs", type=int, default=0, help="Check only N randomly chosen decision documents")
    p.add_argument("--seed", type=int, default=20261017)
    p.add_argument("--output", default=os.path.join("data", "fidelity_report.json"))
    p.add_argument("--drop-absent", metavar="CLEAN_JSON",
                   help="Also write a copy of the input without records in the 'absent' band")
    p.add_argument("--drop-short-form", type=int, default=0, metavar="PAGES",
                   help="With --drop-absent: also drop every record whose source document has at most PAGES pages "
                        "(short-form decisions contain no market analysis; 3 is the value used in the paper)")
    args = p.parse_args()

    records = json.load(open(args.input, encoding="utf-8"))
    by_link = defaultdict(list)
    for i, r in enumerate(records):
        by_link[r.get("link", "")].append(i)
    links = sorted(by_link)
    if args.sample_docs:
        random.seed(args.seed)
        links = random.sample(links, min(args.sample_docs, len(links)))

    local = load_local_batches(args.batches)
    results, doc_info, skipped = [], {}, []
    for k, link in enumerate(links, 1):
        if link in local:
            text, pages = local[link]
            err = None
        elif args.no_download:
            skipped.append(link)
            continue
        else:
            text, pages, err = download_text(link)
        if err or text is None:
            skipped.append(f"{link} ({err})")
            continue
        src = normalise(text)
        doc_info[link] = {"pages": pages, "chars": len(text)}
        for i in by_link[link]:
            cov, missing = coverage(records[i].get("text", ""), src)
            results.append({"index": i, "case_number": records[i].get("case_number"), "year": records[i].get("year"),
                            "topic": records[i].get("topic"), "link": link, "pages": pages,
                            "coverage": round(cov, 3), "missing_windows": missing, "band": band(cov)})
        print(f"[{k}/{len(links)}] {records[by_link[link][0]].get('case_number')}: {len(by_link[link])} records, pages={pages}")

    bands = Counter(r["band"] for r in results)
    short = {l for l, d in doc_info.items() if d["pages"] is not None and d["pages"] <= 3}
    report = {
        "method": "letters-only normalisation; coverage = share of 40-letter windows (stride 20) found in source",
        "documents_checked": len(doc_info), "documents_skipped": skipped,
        "records_checked": len(results), "bands": dict(bands),
        "exact_matches": sum(1 for r in results if r["coverage"] == 1.0),
        "short_form_documents_le3_pages": len(short),
        "absent_records_in_short_form_documents": sum(1 for r in results if r["band"] == "absent" and r["link"] in short),
        "per_record": results,
    }
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    json.dump(report, open(args.output, "w", encoding="utf-8"), indent=2)

    print("\n" + "=" * 57)
    print("  LEXTRACT SOURCE-FIDELITY REPORT")
    print("=" * 57)
    print(f"  Documents checked : {len(doc_info)}  (skipped: {len(skipped)})")
    print(f"  Records checked   : {len(results)}")
    for name, _ in BANDS:
        n = bands.get(name, 0)
        pct = 100 * n / len(results) if results else 0
        print(f"    {name:<14}: {n:>5}  ({pct:5.1f}%)")
    print(f"  Exact matches     : {report['exact_matches']}")
    print(f"  Short-form docs   : {len(short)} (<= 3 pages); absent records in them: "
          f"{report['absent_records_in_short_form_documents']}")
    print(f"  Report saved to   : {args.output}")

    if args.drop_absent:
        drop = {r["index"] for r in results if r["band"] == "absent"}
        if args.drop_short_form:
            drop |= {r["index"] for r in results
                     if r["pages"] is not None and r["pages"] <= args.drop_short_form}
        clean = [r for i, r in enumerate(records) if i not in drop]
        json.dump(clean, open(args.drop_absent, "w", encoding="utf-8"), indent=4, ensure_ascii=False)
        print(f"  Cleaned output    : {args.drop_absent} ({len(records) - len(clean)} records dropped)")


if __name__ == "__main__":
    main()
