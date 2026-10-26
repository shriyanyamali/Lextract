# Project Tree

> Do not change the location of any files or directories as that breaks the pipeline. If you change the location of any files or directories, make sure to reflect the changes in the `run_pipeline.py` file and all affected scripts.

```
.
├── README.md
├── PROJECT_TREE.md
├── LICENSE
├── Makefile
├── requirements.txt
├── pyproject.toml
├── run_pipeline.py              # runs steps 1-6 below
├── analyze.py                   # summary statistics of data/output.json
├── evaluate.py                  # structural validity test (reference-set based)
├── verify_fidelity.py           # source-fidelity test: is each record verbatim in its decision?
├── export.py                    # CSV / JSONL / Parquet / SQLite / BibTeX / RIS export
├── make_annotation_sheet.py     # gold-standard annotation sheets (precision / recall study)
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── test.yml
├── scripts/
│   ├── scrape_links.py          # step 1: links + metadata from the case-search export
│   ├── scrape_pdf_text.py       # step 2: download PDFs, extract text, exclude short-form decisions
│   ├── scrape_chunks.py         # step 3: LLM call 1 - market-definition section
│   ├── scrape_individual.py     # step 4: LLM call 2 - individual definitions as JSON
│   ├── clean_json.py            # step 5: strip Markdown fences
│   └── json_merge.py            # step 6: merge into data/output.json
├── baselines/
│   ├── single_pass.py           # ablation: one LLM call on the whole decision (prepared, not run)
│   └── rule_based.py            # heading / paragraph rules, no LLM (prepared, not run)
├── docs/
│   ├── PROMPTS.md               # the two prompts, verbatim, plus model settings
│   └── EVALUATION.md            # evaluation protocol, results and error analysis
├── evaluation/
│   ├── reference.json           # 50 manually checked definitions (structural test)
│   ├── manual_inspection_sample.csv   # 100 labelled records (50 pass / 50 fail)
│   └── fidelity_report_sample.json    # per-record fidelity results (40-doc sample + reference set)
├── paper/                       # LDA 2026 workshop paper (LaTeX source and PDF)
├── utils/
│   ├── word_counter.py
│   └── unique_cases_counter.py
├── data/
│   ├── jurismercatus_definitions.json   # released collection (4,105 records) used in the paper
│   ├── cases.xlsx*
│   ├── extracted_links.txt*
│   ├── excluded_cases.txt*
│   ├── included_cases.txt*
│   ├── output.json*
│   ├── analysis.json*
│   ├── evaluation_report.json*
│   ├── fidelity_report.json*
│   ├── extracted_batches/
│   │   ├── pdf_texts_79_batch_{n}.txt†
│   │   └── pdf_texts_80_batch_{n}.txt†
│   └── extracted_sections/
│       ├── extract-sections_79_batch_{n}.txt†
│       └── extract-sections_80_batch_{n}.txt†
├── json/
│   ├── extract-definitions_79_batch_{n}.json†
│   └── extract-definitions_80_batch_{n}.json†
└── tests/
    ├── conftest.py
    ├── test_analyze.py
    ├── test_clean_json.py
    ├── test_evaluate.py
    ├── test_export.py
    ├── test_json_merge.py
    ├── test_run_pipeline.py
    ├── test_scrape_chunks.py
    ├── test_scrape_individual.py
    ├── test_scrape_links.py
    ├── test_scrape_pdf_text.py
    ├── test_unique_cases_counter.py
    ├── test_verify_fidelity.py
    └── test_word_counter.py
```

`*` File will be created during execution <br>
`†` Multiple files may be created during execution <br>

The {n} in the file names is a placeholder. During execution, {n} is replaced with 1 in the first file, then with 2, 3, 4, etc., in subsequent files.
