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
Baseline: rule-based extraction without any LLM.

1. Section: find the first heading line whose text contains "market definition" or
   "relevant market" (case-insensitive) and take everything up to the next heading of
   the same numbering depth (e.g. "4. PRODUCT MARKET DEFINITION" ... "5. COMPETITIVE
   ASSESSMENT"). Headings are recognised by a leading numbering token (1., 4.1.2., IV.,
   A.) followed by a short title line.
2. Definitions: split the section into numbered paragraphs ("(13) ...") and emit every
   paragraph that contains a scope cue ("market", "left open", "national", "EEA-wide",
   "worldwide", "segment"). The paragraph number and footnote markers are stripped. The
   topic is the nearest preceding sub-heading.

The output has the same JSON shape as the pipeline, so evaluate.py and verify_fidelity.py
apply unchanged. It runs entirely offline on data/extracted_batches/.

Status: prepared, NOT run for the LDA 2026 paper (the batch files of the original run
are not in the repository; re-create them with scripts/scrape_pdf_text.py).

Usage
    python baselines/rule_based.py --indir data/extracted_batches --output baselines/out_rule_based.json
    python evaluate.py --predicted baselines/out_rule_based.json
    python verify_fidelity.py --input baselines/out_rule_based.json
"""

import argparse
import glob
import json
import os
import re

HEADING = re.compile(r"^\s*(?P<num>(?:\d+(?:\.\d+)*\.?)|(?:[IVX]+\.)|(?:[A-Z]\.))\s+(?P<title>[A-Z][^\n]{2,80})\s*$")
PARA = re.compile(r"^\s*\(\s*(\d{1,3})\s*\)\s+")
CUES = ("market", "left open", "national", "eea-wide", "eea -wide", "worldwide", "segment")
FOOTNOTE_MARK = re.compile(r"(?<=[A-Za-z,.;)])\d{1,3}(?=[\s,.;)]|$)")


def depth(num):
    num = num.strip().rstrip(".")
    return num.count(".") + 1 if num[0].isdigit() else 1


def extract_section(text):
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = HEADING.match(line)
        if m and re.search(r"market definition|relevant market", m.group("title"), re.I):
            start, d = i, depth(m.group("num"))
            break
    if start is None:
        return None
    for j in range(start + 1, len(lines)):
        m = HEADING.match(lines[j])
        if m and depth(m.group("num")) <= d and not re.search(r"market", m.group("title"), re.I):
            return "\n".join(lines[start:j])
    return "\n".join(lines[start:])


def split_paragraphs(section):
    paras, current, topic, topics = [], [], "", []
    for line in section.splitlines():
        h = HEADING.match(line)
        if h:
            topic = h.group("title").strip()
            continue
        if PARA.match(line):
            if current:
                paras.append(" ".join(current)); topics.append(topic)
            current = [PARA.sub("", line)]
        elif current:
            current.append(line.strip())
    if current:
        paras.append(" ".join(current)); topics.append(topic)
    return list(zip(topics, paras))


def main():
    p = argparse.ArgumentParser(description="Rule-based extraction baseline (no LLM)")
    p.add_argument("--indir", default=os.path.join("data", "extracted_batches"))
    p.add_argument("--output", default=os.path.join("baselines", "out_rule_based.json"))
    args = p.parse_args()

    records, no_section = [], 0
    for path in sorted(glob.glob(os.path.join(args.indir, "pdf_texts_*_batch_*.txt"))):
        content = open(path, encoding="utf-8").read()
        header, _, body = content.partition("\n\n")
        meta = dict(l.split(": ", 1) for l in header.splitlines() if ": " in l)
        section = extract_section(body)
        if section is None:
            no_section += 1
            continue
        for topic, para in split_paragraphs(section):
            low = para.lower()
            if not any(c in low for c in CUES):
                continue
            text = re.sub(r"\s+", " ", FOOTNOTE_MARK.sub("", para)).strip()
            records.append({"case_number": meta.get("Case Number", ""), "year": meta.get("Year", ""),
                            "policy_area": meta.get("Policy Area", ""), "link": meta.get("Link", ""),
                            "topic": topic or "Market definition", "text": text})
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    json.dump(records, open(args.output, "w", encoding="utf-8"), indent=4, ensure_ascii=False)
    print(f"[rule-based] {len(records)} records written to {args.output}; {no_section} documents without a recognisable section")


if __name__ == "__main__":
    main()
