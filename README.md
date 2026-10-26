[![DOI](https://img.shields.io/badge/DOI-10.2139%2Fssrn.5576990-0077B5)](https://doi.org/10.2139/ssrn.5576990)
![Maintained](https://img.shields.io/badge/Maintained-yes-green.svg)
![License](https://img.shields.io/badge/License-AGPL%203.0-green.svg)
[![Test Coverage](https://codecov.io/gh/shriyanyamali/Lextract/branch/main/graph/badge.svg)](https://codecov.io/gh/shriyanyamali/Lextract)
![Tests Status](https://img.shields.io/github/actions/workflow/status/shriyanyamali/lextract/ci.yml?branch=main&label=tests)

# Lextract

Lextract extracts **relevant market definitions** from the European Commission's merger and antitrust decision PDFs (available through the Commission's [case search](https://competition-cases.ec.europa.eu/search)) and stores them as structured JSON records with case metadata. A relevant market definition delineates the product and geographic boundaries within which a merger or conduct is assessed; the Commission discusses it under varying headings, positions and wording, which makes regex-style extraction brittle. Lextract therefore uses a large language model (Google Gemini 2.0 Flash) in two calls, one to locate the market-definition section and one to isolate the individual definitions, and then checks the model's output with deterministic tests.

The released collection (`data/jurismercatus_definitions.json`, 4,105 records from 600 cases, 2016-2025) powers [JurisMercatus](https://jurismercatus.shriyanyamali.com/), a semantic-search interface for market definitions, and is described and evaluated in the LDA 2026 workshop paper in [`paper/`](paper/).

## Contents of this repository

| Path | Purpose |
| --- | --- |
| `run_pipeline.py` | runs the six pipeline steps below |
| `scripts/` | the six step scripts |
| `docs/PROMPTS.md` | the two LLM prompts, **verbatim**, and the model settings |
| `docs/EVALUATION.md` | evaluation protocol, results and error analysis, with the commands that regenerate every number |
| `evaluate.py` | structural validity test (reference-set based) |
| `verify_fidelity.py` | source-fidelity test: is each record present verbatim in its decision? |
| `make_annotation_sheet.py` | builds gold-standard annotation sheets for a precision / recall study |
| `baselines/` | single-pass and rule-based baselines (prepared, not yet run) |
| `analyze.py`, `export.py` | summary statistics; CSV / JSONL / Parquet / SQLite / BibTeX / RIS export |
| `evaluation/` | reference set, manual-inspection labels, fidelity results of the paper |
| `data/jurismercatus_definitions.json` | the released collection used in the paper (unchanged pipeline output, 4,105 records) |
| `data/jurismercatus_definitions_clean.json` | the cleaned release: absent records and records from short-form documents removed (3,607 records) |
| `paper/` | LaTeX source and PDF of the LDA 2026 paper |

## How the pipeline works

| Step | Script | Input -> output | What it does |
| --- | --- | --- | --- |
| 1 | `scripts/scrape_links.py` | `data/cases.xlsx` -> `data/extracted_links.txt` | reads the case-search Excel export; keeps decision URL, case number, year, policy area (from the URL path) |
| 2 | `scripts/scrape_pdf_text.py` | links -> `data/extracted_batches/pdf_texts_<79\|80>_batch_<n>.txt` | downloads each PDF, extracts text with PyPDF2, **excludes short-form decisions** (see below), writes one batch file per decision with a metadata header; files are labelled `79` (<= 80,000 characters) or `80` (> 80,000) so that long decisions can be processed separately |
| 3 | `scripts/scrape_chunks.py` | batch file -> `data/extracted_sections/extract-sections_<size>_batch_<n>.txt` | **LLM call 1**: returns the market-definition section (from the first "market definition" heading to the next heading of the same level) |
| 4 | `scripts/scrape_individual.py` | section -> `json/extract-definitions_<size>_batch_<n>.json` | **LLM call 2**: returns a JSON array of definitions, each with `case_number`, `year`, `policy_area`, `link`, `topic`, `text`; the prompt asks for direct quotes, drops paragraph numbers and footnotes, and lets the model choose the `topic` |
| 5 | `scripts/clean_json.py` | json files | strips Markdown code fences from the model output |
| 6 | `scripts/json_merge.py` | json files -> `data/output.json` | concatenates all arrays; no de-duplication or editing |

**Model and settings.** `gemini-2.0-flash` through the `google-generativeai` SDK with default generation settings: no temperature, top-p, top-k or output-length override, no system instruction, no JSON mode. Both prompts are in [`docs/PROMPTS.md`](docs/PROMPTS.md). Because nothing is seeded, re-running the pipeline will not reproduce the released collection byte for byte.

**Exclusion phrases and their rationale.** Step 2 excludes *short-form* decisions, i.e. clearances under the [simplified procedure](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52013XC1214(02)) that contain no market analysis, so that no "definition" is extracted from them. A document is excluded when it has at most `MAX_SHORT_FORM_PAGES = 3` pages and contains any of these sentences from the standard closing recital:

```
For the reasons set out in the Notice on a simplified
European Commission has decided not to oppose the notified operation
declare it compatible with the internal market
This decision is adopted in application of Article 6(1)(b)
Merger Regulation and Article 57 of the EEA Agreement
```

Matching is whitespace- and punctuation-insensitive (version 1.1.0). In the run that produced the released collection, matching was exact and applied only to documents of *exactly* three pages; PyPDF2 inserts spaces and line breaks inside words ("simpli fied", "Merger  Regulation"), so most short-form decisions were **not** excluded, and the model fabricated plausible definitions for them. See [`docs/EVALUATION.md`](docs/EVALUATION.md) for the measurement (471 of 4,067 verifiable records, 11.6 %, are absent from their source) and `verify_fidelity.py --drop-absent ... --drop-short-form 3` for cleaning an existing collection.

## Quality checks

| Check | Script | What it tells you | What it cannot tell you |
| --- | --- | --- | --- |
| Structural validity | `evaluate.py` | whether a record resembles the 50 manually checked reference definitions in length (26-668 words), legal phrasing (121 learned n-grams) and structural markers (18 fixed phrases); 76.6 % of the released records pass | whether the text is actually in the decision, whether boundaries are right, whether definitions were missed |
| Source fidelity | `verify_fidelity.py` | whether each record occurs verbatim in the PyPDF2 text of its decision (coverage of 40-letter windows; bands verbatim / near-verbatim / partial / absent); over the whole collection 79 % of records are verbatim, 9 % near-verbatim, 12 % absent; three quarters of the absent records come from short-form decisions, 30 are leaked prompt examples | whether the copied passage is the *right* passage, or whether others were missed |
| Manual inspection | `evaluation/manual_inspection_sample.csv` | 100 labelled records (50 passing / 50 failing the structural test): 49/50 passing and 41/50 failing records are market-definition content | not a gold standard; single annotator; text-only reading |
| Gold standard (P/R/F1) | `make_annotation_sheet.py` | **not yet done**: produces the sheets for an expert annotation of N whole decisions | - |
| Baselines | `baselines/` | **not yet run**: single-call ablation and rule-based extraction in the same JSON shape | - |

## Instructions

### Prerequisites

- [Git](https://git-scm.com/downloads)
- [Python](https://www.python.org/downloads/) 3.10 or newer
- [Gemini API key](https://aistudio.google.com/apikey) (steps 3 and 4 only)

The code defaults to Gemini 2.0 Flash for its free-tier rate limits (roughly 50-100 decisions a day depending on length; see [models](https://ai.google.dev/gemini-api/docs/models) and [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)). Other Gemini models can be passed with `--model`; other providers require code changes. The extraction quality of other models has not been measured.

### Installation

> Do not rename or move files; the scripts rely on the layout in [PROJECT_TREE.md](PROJECT_TREE.md).

The code, data and paper described in the LDA 2026 workshop paper are on the `lda2026` branch.

```bash
git clone -b lda2026 https://github.com/shriyanyamali/Lextract.git
cd Lextract
pip install -r requirements.txt
```

### Running the pipeline

1. Remove the `.gitkeep` files from `json/`, `data/extracted_batches/` and `data/extracted_sections/`.
2. Export the merger and antitrust cases you want to process from [competition-cases.ec.europa.eu/search](https://competition-cases.ec.europa.eu/search), rename the file `cases.xlsx` and move it into `data/`.
3. In `run_pipeline.py` set `CHUNKS_SIZE` to `"79"`, `"80"` or `"both"` (which length group of batch files to send to the model).
4. Set the API key: `export GEMINI_API_KEY="..."` (PowerShell: `$env:GEMINI_API_KEY="..."`).
5. `python run_pipeline.py`

The merged result is `data/output.json`. Each record looks like:

```json
{
   "case_number": "M.9324",
   "year": "2019",
   "policy_area": "Merger",
   "link": "https://ec.europa.eu/competition/mergers/cases1/202048/m9324_479_3.pdf",
   "topic": "Wholesale distribution of IT products",
   "text": "In Avnet/Magirus, Tech Data/Scribona , Tech Data/Avnet , the Commission has defined a market for the wholesale distribution of IT products, but left open the question whether the market should be further sub -segmented (i) by product categories (e.g. server, storage, PCs, etc.), (ii) by direct and indirect sales or (iii) by different distribution models (broadline vs value -added distribution (“VAD”))."
}
```

### Checking the output

```bash
# structural validity against the reference set
python evaluate.py --reference evaluation/reference.json --predicted data/output.json --output data/evaluation_report.json

# source fidelity: uses data/extracted_batches/ if present, otherwise downloads the PDFs
python verify_fidelity.py --input data/output.json --output data/fidelity_report.json --drop-absent data/output_clean.json --drop-short-form 3

# summary statistics and exports
python analyze.py --input data/output.json --output data/analysis.json
python export.py --format all --input data/output.json --output exports
```

`pip install -e .` installs the commands `lextract`, `lextract-evaluate`, `lextract-analyze` and `lextract-export`. Parquet export needs `pip install -e ".[parquet]"`.

### Reproducing the paper's numbers

All commands are listed in [`docs/EVALUATION.md`](docs/EVALUATION.md). In short:

```bash
python evaluate.py --predicted data/jurismercatus_definitions.json          # 76.6 % structural validity
python verify_fidelity.py --input data/jurismercatus_definitions.json --output data/fidelity_report.json \
    --drop-absent data/jurismercatus_definitions_clean.json --drop-short-form 3   # downloads all 704 documents
```

The per-record results of the full run are in `evaluation/fidelity_report_full.json` (and the earlier 40-document pilot in `evaluation/fidelity_report_sample.json`).

### Preparing the gold-standard study and the baselines (not yet run)

```bash
python make_annotation_sheet.py --n 10 --seed 20261017          # annotation/ : decision text + record sheet per decision
python baselines/rule_based.py                                   # needs data/extracted_batches/ from step 2
python baselines/single_pass.py --limit 20                       # needs GEMINI_API_KEY; one call per decision
```

Both baselines write the pipeline's JSON shape, so `evaluate.py` and `verify_fidelity.py` score them in the same way as the main pipeline.

### Testing

```bash
pytest -q                          # all tests (mocked network and model calls)
pytest --cov=scripts --cov=tests   # with coverage
```

`make test`, `make coverage` and `make clean` wrap these (use WSL or install make on Windows).

## Known issues (as of the October 2026 audit)

- **Short-form decisions (fixed in version 1.1.0 for new runs).** See *Exclusion phrases* above. 136 of the 699 retrievable documents behind the released collection are short-form; 353 of their 380 records are not in the source. The cleaned release removes them.
- **Prompt-example leakage.** The four example passages in the call-2 prompt appear verbatim as records in 30 records across 11 cases of the released collection. They will be removed from the prompt in the next run.
- **Boundaries and duplicates.** 261 records are shorter than 26 words (mostly one-sentence conclusions, seven bare headings), 14 longer than 668 words, and 117 records duplicate another record's text. No de-duplication is applied.
- **PDF artefacts.** Split words such as "in -house" survive in about 30 % of records.
- **Link rot.** Two decision URLs in the reference set now redirect; the Commission occasionally moves documents.

## Research applications

The records can be filtered, exported and combined for empirical and legal research, for example to find how the Commission has defined a product or geographic market in earlier cases, to trace how often definitions are left open by sector and year, or to build search indexes such as JurisMercatus. Each record carries the decision URL, so every passage can be checked against its source.

## License

The code in this repository is licensed under the AGPL-3.0 License. View the [full license](https://raw.githubusercontent.com/shriyanyamali/Lextract/main/LICENSE).

## Acknowledgements

Lextract was built by Shriyan Yamali under the advisement of Professor Thibault Schrepel. This project received no funding from any government agency, university, company, or non-profit organization.

## Contact

Email: [yamalishriyan@gmail.com](mailto:yamalishriyan@gmail.com)

Copyright © 2026 Shriyan Yamali. All rights reserved.
