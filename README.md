![Maintained](https://img.shields.io/badge/Maintained-yes-green.svg)
![License](https://img.shields.io/badge/License-AGPL%203.0-green.svg)
![Build Status](https://img.shields.io/github/actions/workflow/status/shriyanyamali/shriyanyamali.github.io/ci.yml?branch=main)
![Last Commit](https://img.shields.io/github/last-commit/shriyanyamali/market-def-scraper)

# European Commission Market Definition Scraper

## Table of Contents

- [<u>Purpose</u>](#purpose)
- [<u>Project Tree</u>](#project-tree)
- [<u>API Keys</u>](#api-keys)
- [<u>Installation</u>](#installation-and-setup)
   - [<u>Pip</u>](#pip)
   - [<u>Docker</u>](#docker)
   - [<u>Setup</u>](#setup)
   - [<u>Running Tests</u>](#running-tests)
- [<u>Example Outputs</u>](#example-outputs)
- [<u>Usage Example</u>](#usage-example)
- [<u>File Descriptions</u>](#pipeline-scripts)
   - [<u>Setup</u>](#pipeline-scripts)
   - [<u>Utility Scripts</u>](#utility-scripts)
- [<u>License</u>](#license)
- [<u>Attribution</u>](#attribution)
- [<u>Contact</u>](#contact)

## Purpose

This repository extracts relevant market definitions from European Commission's competition case decision PDFs, which are available through their [online case search database](https://competition-cases.ec.europa.eu/search), using an automated pipeline. Market definitions help identify the specific market in which a merger is assessed. According to [EU](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:C_202401645), a "market definition is a tool that the Commission uses to identify and define the boundaries of competition between undertakings. The main purpose of [a] market definition is to identify in a systematic way the effective and immediate competitive constraints faced by the undertakings involved when they offer particular products in a particular area." You can learn more about market definitions [here](https://www.justice.gov/atr/merger-guidelines/tools/market-definition).

It is imperative to use an LLM in order to extract these market definitions, as the EC's decision PDFs assert the market definitions portion of the PDF differently each time, making it difficult to use regex or another form of pattern matching while still maintaining a high level of reliability.

## Project Tree

Do not change the location of any files or directories as that breaks the pipeline. If you change the location of any files or directories, make sure to reflect the changes in the `run_pipeline.py` file and all affected scripts.

    .
    ├── README.md
    ├── LICENSE
    ├── Dockerfile
    ├── requirements.txt
    ├── run_pipeline.py
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
    │   ├── cases.xlsx*
    │   ├── extracted_links.txt*
    │   ├── excluded_cases.txt*
    │   ├── included_cases.txt*
    │   ├── output.json*
    │   ├── extracted_batches/
    │   │   ├── pdf_texts_79_batch_XX.txt***
    │   │   └── pdf_texts_80_batch_XX.txt***
    │   └── extracted_sections/
    │       ├── extract-sections_79_batch_XX.txt***
    │       └── extract-sections_80_batch_XX.txt***
    └── json/
        ├── extract-definitions_79_batch_XX.json***
        └── extract-definitions_80_batch_XX.json***

`*` File will be created during execution <br>
`***` Multiple files may be created during execution <br>

The "XX" in the file names is a placeholder. When the files are created during execution, "XX" will be replaced by the number 1 in the first file. Subsequent files of the same type will have "XX" replaced by increasing numbers (2, 3, 4, ...)

Eg. `pdf_texts_79_batch_1.txt` will be followed by `pdf_texts_79_batch_2.txt`. If the biggest number is 82, say as the file `pdf_texts_79_batch_82.txt`, then there are 82 batches of pdf_texts_79.

## API Keys

You will need a Google Gemini API key in order to run the `scrape-chunks.py` and `scrape-individual.py` scripts. You can get a free api key [here](https://ai.google.dev/). The code is preset to use the Gemini 2.0 Flash model. Though other models have higher accuracy, the Flash models have higher usage limits, making them the only viable option when using the free API key, as you will run into the rate limit very quickly. If you are paying for an API key and have a high budget, you can use 1.5 Pro or 2.5 Pro models for higher accuracy, but they are less cost-efficient.

Currently, the latest Flash model is Gemini 2.5 Flash. You can use that model if the usage rates increase in the future or if you are only extracting definitions from a few cases (around 5). You can read more about all the Gemini API models [here](https://ai.google.dev/gemini-api/docs/models) and the rate limits [here](https://ai.google.dev/gemini-api/docs/rate-limits).

You are free to use the OpenAI API key or another API key, but you will need to rewrite to code to match the documentation of that API. Note that as of July 2025, this code has only been tested using the Google Gemini API, and accuracy and efficiency using other APIs cannot be guaranteed.

Locally hosted LLMs like Ollama or Deepseek can also work, but only use locally hosted LLMs if you are using a larger model (at least 70b+ but ideally 671b+) or else the accuracy will be depreciated. The installation detailed below, however, will explain how to use a Gemini API key.

## Installation and Setup

Make sure that [Git](https://git-scm.com/downloads) and [Python](https://www.python.org/downloads/) are installed on your system.

### Pip

```bash
# Clone the repo
git clone https://github.com/shriyanyamali/market-def-scraper.git

# Change into the project directory
cd market-def-scraper

# Install the required packages
pip install pandas pytest PyPDF2 google-generativeai requests openpyxl
```

### Docker

```bash
# Clone the repo
git clone https://github.com/shriyanyamali/market-def-scraper.git

# Change into the project directory
cd market-def-scraper

# Build the image:
docker build -t market-def-scraper.
```

### Setup

1. Go to [competition-cases.ec.europa.eu/search](https://competition-cases.ec.europa.eu/search) and export the Merger cases you want to process. Rename the excel file `cases.xlsx`. Move the file into the data directory.

2. Remove the `.gitkeep` files from the data/extracted_batches and data/extracted_sections directories.

3. Open the `scrape-chunks.py` and `scrape-individual.py` scripts. At the beginning of both files, where it says `ENTER KEY HERE`, replace that which your actual API key.

4. Open the `run_pipeline.py` script. On line 10, follow the instructions and set CHUNKS_SIZE equal to `79`, `80`, or `both`.

5. Run the pipeline:

      Pip:

      ```bash
      python run_pipeline.py
      ```

      Docker:

      ```bash
      # macOS / Linux
      docker run --rm -v "$(pwd)/data:/app/data" market-def-scraper

      # PowerShell
      docker run --rm -v ${PWD}\data:/app/data market-def-scraper

      # Command Prompt
      docker run --rm -v "%cd%\data:/app/data" market-def-scraper
      ```

      Wait for the pipeline to finish. You will receive an output detailing how many files of each type were created.

      > Note: Do not change the names of any files, as all scripts require the file names to stay exactly the same as the original.

### Running Tests

```bash
pytest -q
```

With coverage:

```bash
pytest --cov=scripts --cov=tests
```

Using Make:
```bash
make test       # Run all tests
make coverage   # Run tests with coverage report
make format     # Auto-format code
make lint       # Lint code
make clean      # Remove __pycache__ and test artifacts
```

## Example Outputs

After the script finishes running, your database.json should have objects that look like this:

```json
{
   "case_number": "M.9466",
   "year": "2019",
   "policy_area": "Merger",
   "link": "https://ec.europa.eu/competition/mergers/cases/decisions/m9466_208_3.pdf",
   "topic": "Geographic scope of the semiconductor markets",
   "text": "In the Commission found that the geographic scope of the semiconductor markets was..."
},
{
   "case_number": "M.9504",
   "year": "2019",
   "policy_area": "Merger",
   "link": "https://ec.europa.eu/competition/mergers/cases/decisions/m9504_41_3.pdf",
   "topic": "Wholesale distribution of building materials, sanitary, and plumbing materials",
   "text": "The Parties submit that the relevant product markets are the..."
}
```

## Usage Example

This code was used in order to create the database for [JurisMercatus](https://jurismercatus.vercel.app/). JurisMercatus is a market definition database aggregated from the European Commission's merger and antitrust case decisions. It brings all the definitions together natural language searches.

## File Descriptions

### Pipeline Scripts

These scripts are part of the pipeline and are executed alongside `run_pipeline.py`. The scripts run in the following order:

1. **scrape-links.py**

   * Extracts PDF links, case numbers, years, and policy areas from an Excel file.
   * Outputs to `extracted_links.txt`.
   * Excel must have correctly named columns (correct by default).

2. **scrape-pdf-text.py**

   * Downloads PDFs from links.
   * Filters out irrelevant cases.
   * Saves one PDF per text file.
   * Files >80,000 chars: `pdf_texts_80_batch_{n}.txt`.
   * Files ≤79,999 chars: `pdf_texts_79_batch_{n}.txt`.

3. **scrape-chunks.py**

   * Uses Gemini AI to extract "Market Definition" sections.
   * Saves as `extract-sections_79/80_batch_{n}.txt`.
   * Includes metadata at top.

4. **scrape-individual.py**

   * Uses Gemini AI to extract individual market definitions.
   * Saves as `extract-definitions_79/80_batch_{n}.json`.
   * Includes metadata with each object.

5. **clean-json.py**

   * Removes markdown fences ('''json or \`\`\`) from JSON files.
   * Edits in-place, creates no new files.

6. **json-merge.py**

   * Merges all JSON batch files into one.
   * Output is `output.json` in `data/` directory.

### Utility Scripts

These scripts are not part of the pipeline and can be manually executed.

- **unique_cases_counter.py**
- **word_counter.py**

## License

The code in this repository is licensed under the AGPL-3.0 License.

View the full license at [www.gnu.org/licenses/agpl-3.0](https://www.gnu.org/licenses/agpl-3.0).

## Attribution

When using the code from this repo (i.e. shriyanyamali/market-def-scraper) you must provide proper attribution.

Specifically, in any work, including but not limited to public, published, commercialized, or derived work that uses or builds upon this repository's code, you must cite the original repository by including the following citation:

```
This project uses code from the market-def-scraper repository Copyright (c) 2025 Shriyan Yamali,
licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

https://github.com/shriyanyamali/market-def-scraper
```

## Contact

Email: [yamalishriyan@gmail.com](mailto:yamalishriyan@gmail.com)

Copyright © 2025 Shriyan Yamali. All rights reserved.