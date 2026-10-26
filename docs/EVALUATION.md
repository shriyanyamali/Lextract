# Evaluation and error analysis (October 2026 audit)

This document records how the released collection (`data/jurismercatus_definitions.json`, 4,105 records) was evaluated for the LDA 2026 workshop paper, with the exact commands, so that every number in the paper can be regenerated. Three instruments are used; none of them is a gold-standard precision/recall study (see "What is still missing").

## 1. Structural validity test (`evaluate.py`)

```bash
python evaluate.py --reference evaluation/reference.json --predicted data/jurismercatus_definitions.json --output data/evaluation_report.json
```

The script learns three properties from the 50-record reference set and applies them to every record:

| Check | Threshold (learned from the reference set) |
| --- | --- |
| Length | 26-668 words: the reference range (33-557) widened by 20 % on each side |
| Legal phrase | at least one of 121 word n-grams (n = 2-5) that occur in >= 15 % of reference records |
| Structural marker | at least one of 18 fixed markers: relevant market, product market, geographic market, market definition, left open, EEA-wide, EEA wide, national market, Commission considers, Commission found, Commission has previously, Notifying Party, internal market, serious doubts, plausible market, exact scope, for the purposes of, cannot be excluded |

Result: 3,143 of 4,105 records (76.6 %) pass. Failure combinations: marker only 668; length only 185; length + marker 80; phrase + marker 19; all three 10. Of the 275 length failures, 261 are shorter than 26 words and 14 longer than 668. Seven of the 50 reference records fail their own marker check.

**What it measures:** whether a record *resembles* a verified market-definition passage. **What it does not measure:** whether the text occurs in the decision, whether boundaries are right, whether it is the right passage, or whether definitions were missed.

## 2. Source-fidelity test (`verify_fidelity.py`)

```bash
# the whole collection, as reported in the paper (downloads all 704 documents, ~1 h;
# or point --batches at the batch files of the original run)
python verify_fidelity.py --input data/jurismercatus_definitions.json --output data/fidelity_report.json \
    --drop-absent data/jurismercatus_definitions_clean.json --drop-short-form 3
```

Record and PyPDF2 decision text are normalised to lower-case letters only; *coverage* is the share of 40-letter windows (stride 20) of the record found in the source. Bands: verbatim >= 0.95, near-verbatim 0.80-0.95, partial 0.50-0.80, absent < 0.50. The per-record results of the full run (17 October 2026) are in `evaluation/fidelity_report_full.json`; `evaluation/fidelity_report_sample.json` holds the earlier 40-document pilot on which the failure mechanism was first found.

| | Whole collection | Reference set |
| --- | --- | --- |
| Documents checked (of 704 / 40) | 699 (5 URLs unretrievable: 4 of M.11241 redirect, 1 is an HTML index page) | 38 |
| Records checked (of 4,105 / 50) | 4,067 | 48 |
| Verbatim (>= 0.95) | 3,221 (79.2 %) | 44 |
| of which exact (1.0) | 2,985 (73.4 %) | - |
| Near-verbatim (0.80-0.95) | 349 (8.6 %) | 3 |
| Partial (0.50-0.80) | 26 (0.6 %) | 0 |
| Absent (< 0.50) | 471 (11.6 %) | 1 (M.10993) |
| Documents of <= 3 pages | 136 (19.5 %) | 1 |
| Records from those documents | 380, of which 353 absent (the other 27 are copied boilerplate) | 1 of 1 absent |
| Absent records from longer documents | 118 of 3,687 | 0 of 47 |

Where the 471 absent records come from: 353 from the 136 documents of at most three pages; 30 are copies of the prompt's own examples (26 in longer documents, 4 in short ones); 32 from twelve documents of four to seven pages (eleven of which yielded no copied record at all); 60 from 19 documents longer than seven pages, among them ancillary decisions that refer back to a main clearance decision (purchaser approvals, commitment amendments: M.5364, M.6447, M.8797, M.9554, M.10108, M.10638, ...), whose records restate the earlier decision's definitions in words that do not occur in the document, and a few long decisions (M.10663, M.10896, M.11177, M.9771, M.8889, M.10680) whose records share only fragments with the text (coverage 0.1-0.45). Whether these are paraphrases of real passages or fabrications was not checked by reading the decisions. 151 of the 600 cases contain at least one absent record. The structural test passes 336 of the 471 absent records (71 %), against 2,475 of 3,221 verbatim records (77 %).

Absent share by year of decision: 2017 48 %, 2018 25 %, 2019 13 %, 2020-2024 5-9 % (the short-form decisions that evaded the filter are concentrated in the early years of the collection).

Near-verbatim records: 292 of 349 have at most two missing windows (a single break). Inspection in twelve documents found footnote text interleaved at page breaks in the PyPDF2 text, and the model omitting an intermediate paragraph (e.g. the Notifying Party's submission between the Commission's precedent and its conclusion). No paraphrase was found.

**Cleaned release.** `data/jurismercatus_definitions_clean.json` drops the 471 absent records and all 380 records from documents of at most three pages (498 records in total, since 353 are in both sets): 3,607 records from 455 cases; structural validity on this file is 77.6 %. The 38 unverifiable records are kept. The JurisMercatus index should be rebuilt from this file.

## 3. Manual inspection (`evaluation/manual_inspection_sample.csv`)

50 records that pass the structural test and 50 that fail it were drawn with `random.seed(20261017)` from the per-record results and read **from the record text alone** (the source decision was not consulted). Labels:

* **A1** market-definition statement (precedent, party submission, market-investigation finding, or Commission conclusion on product or geographic scope)
* **A2** reasoning inside a market-definition analysis without a definitional claim
* **B** fragment (e.g. a bare heading)
* **C** not a market definition (competitive assessment, remedies, party description, legal background)

| | A1 | A2 | B | C |
| --- | --- | --- | --- | --- |
| Passing the structural test (50) | 49 | 0 | 0 | 1 |
| Failing the structural test (50) | 38 | 3 | 1 | 8 |

Sample #8 (M.9538, "Detergents and Dispersants") is labelled A1 on its face but is one of the prompt examples (see below), i.e. it is not from the decision. This is a single-annotator face-validity reading, not a gold standard; the `note` column records borderline decisions.

## 4. Error classes found

1. **Short-form decisions evading the exclusion filter.** The five exclusion phrases are matched by exact substring, but PyPDF2 splits words and inserts line breaks ("on a simpli fied procedure", "Merger  Regulation"), and the rule applied only to documents of *exactly* three pages, so two-page decisions bypassed it. In the 40-document pilot sample none of the eight three-page documents matched a phrase. Both LLM prompts presuppose that a market-definition section exists, so for these decisions the model produced plausible, precedent-style passages that do not occur in the decision. Measured on the whole collection: 136 of 699 documents (19.5 %) have at most three pages and 353 of their 380 records are absent from the source; 471 records (11.6 %) are absent overall. **Fix (version 1.1.0):** `scripts/scrape_pdf_text.py` now matches phrases on whitespace- and punctuation-insensitive text and applies the rule to documents of at most `MAX_SHORT_FORM_PAGES = 3` pages; on the nine short-form documents of the pilot sample this excludes all nine; it has not been re-run on all 136. `verify_fidelity.py --drop-absent` removes affected records from an existing collection.
2. **Prompt-example leakage.** The four example passages embedded in the call-2 prompt (detergents, chemical intermediates, flame retardants, trimethylolpropane) appear verbatim as records in 30 records across 11 cases (AT.40940, M.4494, M.8480, M.8831, M.9110, M.9331, M.9538, M.9564, M.9592, M.9741, M.9744), none of which is their source. They pass the structural test. **Planned fix:** remove the examples from the prompt (effect on quality untested).
3. **Boilerplate extraction.** Eight records consist of the simplified-procedure recital itself.
4. **Boundaries.** 261 records under 26 words (mostly single conclusion sentences; seven bare headings), 14 over 668 words; near-verbatim records show skipped paragraphs and footnote splices.
5. **Duplicates.** 117 records repeat another record's text (72 groups); 89 within the same case.
6. **Wording not covered by the markers.** Of the 777 marker failures, 535 contain the word "market", 105 "national", 65 "EEA"; 242 do not mention a market.

## 5. Reference set notes

`evaluation/reference.json` (50 records, 39 cases, all merger decisions, mostly 2022-2024, 33-557 words) was selected by the author from the pipeline output and checked against the source PDFs; it is a convenience sample. The audit found: one duplicated record (M.11234, items 0 and 7); two case numbers without the "M." prefix (items 12 and 13; item 13 reads "11806" but the text is from M.11086); one record (item 29, M.10993) that does not occur in its three-page source decision. The file is left unchanged so that `evaluate.py` reproduces the paper's 76.6 %.

## 6. What is still missing (prepared, not run)

* **Gold standard with precision / recall / F1.** `make_annotation_sheet.py --n 10` writes, for ten random decisions, the full decision text and every pipeline record with columns for TP / TP-boundary / FP and missed definitions. Needs an annotator with competition-law knowledge.
* **Baselines.** `baselines/single_pass.py` (one LLM call on the whole decision, ablating call 1) and `baselines/rule_based.py` (headings + numbered paragraphs, no LLM) produce output in the pipeline's JSON shape so that `evaluate.py` and `verify_fidelity.py` score them identically. Neither has been run. The single-pass baseline and any other-model comparison need a Gemini (or other) API key; the rule baseline needs no API, only the batch files written by `scripts/scrape_pdf_text.py`.
* **Re-run of the short-form documents through the fixed filter.** The fixed exclusion rule was validated on the nine short-form documents of the pilot sample; re-running step 2 over all 704 links would confirm that all 136 are now excluded.
