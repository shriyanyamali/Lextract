# Project Tree

> Do not change the location of any files or directories as that breaks the pipeline. If you change the location of any files or directories, make sure to reflect the changes in the `run_pipeline.py` file and all affected scripts.

```
.
├── README.md
├── PROJECT_TREE.md
├── LICENSE
├── Dockerfile
├── Makefile
├── requirements.txt
├── run_pipeline.py
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── test.yml
├── scripts/
│   ├── scrape-links.py
│   ├── scrape-pdf-text.py
│   ├── scrape-chunks.py
│   ├── scrape-individual.py
│   ├── clean-json.py
│   └── json-merge.py
├── debugging/
│   ├── word-counter.py
│   └── unique_cases_counter.py
├── data/
│   ├── cases.xlsx
│   ├── extracted_links.txt*
│   ├── excluded_cases.txt*
│   ├── included_cases.txt*
│   ├── output.json*
│   ├── extracted_batches/
│   │   ├── pdf_texts_79_batch_{n}.txt***
│   │   ├── pdf_texts_80_batch_{n}.txt***
│   │   └── .gitkeep
│   └── extracted_sections/
│       ├── extract-sections_79_batch_{n}.txt***
│       ├── extract-sections_80_batch_{n}.txt***
│       └── .gitkeep
├── json/
│   ├── extract-definitions_79_batch_{n}.json***
│   └── extract-definitions_80_batch_{n}.json***
└── tests/
    ├── conftest.py
    ├── test_clean_json.py
    ├── test_json_merge.py
    ├── test_run_pipeline.py
    ├── test_scrape_chunks.py
    ├── test_scrape_individual.py
    ├── test_scrape_links.py
    └── test_scrape_pdf_text.py
```

`*` File will be created during execution <br>
`***` Multiple files may be created during execution <br>

The {n} in the file names is a placeholder. During execution, {n} is replaced with 1 in the first file, then with 2, 3, 4, etc., in subsequent files.