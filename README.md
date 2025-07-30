![Maintained](https://img.shields.io/badge/Maintained-yes-green.svg)
![License](https://img.shields.io/badge/License-AGPL%203.0-green.svg)
![Build Status](https://img.shields.io/github/actions/workflow/status/shriyanyamali/shriyanyamali.github.io/ci.yml?branch=main)
![Last Commit](https://img.shields.io/github/last-commit/shriyanyamali/market-def-scraper)

# European Commission Market Definition Scraper

## Table of Contents

- [<u>Purpose</u>](#purpose)
- [<u>Research Applications</u>](#research-applications)
- [<u>Installation</u>](#installation-and-setup)
   - [<u>API Keys</u>](#api-keys)
   - [<u>Pip</u>](#pip)
   - [<u>Docker</u>](#docker)
   - [<u>Setup</u>](#setup)
   - [<u>Testing</u>](#testing)
- [<u>Example Outputs</u>](#example-outputs)
- [<u>Usage Example</u>](#usage-example)
- [<u>File Descriptions</u>](#pipeline-scripts)
   - [<u>Setup</u>](#pipeline-scripts)
   - [<u>Utility Scripts</u>](#utility-scripts)
- [<u>License</u>](#license)
- [<u>Attribution</u>](#attribution)
- [<u>Contact</u>](#contact)

## Purpose

This repository extracts relevant market definitions from European Commission's competition case decision PDFs, which are available through their [online case search database](https://competition-cases.ec.europa.eu/search), using an automated pipeline. Market definitions help identify the specific market in which a merger is assessed. A market definition is a tool that defines the boundaries of competition between undertakings.

This project uses AI to extract market definitions as the EC's decision PDFs assert the market definitions sections differently each time, making it very difficult to use regex or another form of pattern matching.

## Research Applications

This tool is intended to support research in competition law, antitrust policy, mergers, and economic regulation. Outputs can be filtered, extended, applied, or repurposed to fit a wide range of empirical and legal research projects.

Example use cases include:

* Analyze trends in market definition language and scope
* Support research or policy reports using market definition data
* Find market definition precedents for court use
* Analyze how market definitions have evolved across sectors
* Identify how markets have been defined the in past

## Installation and Setup

> At no point throughout the installation, setup, or usage of this code should you change the location or name of any files as scripts rely on the original names. See [PROJECT_TREE.md](PROJECT_TREE.md) for how the file structure should be.

Make sure that [Git](https://git-scm.com/downloads) and [Python](https://www.python.org/downloads/) are installed on your system.

### API Keys

To run the pipline (specifically `scrape-chunks.py` and `scrape-individual.py`), you'll need a Google Gemini API key. You can get one [here](https://ai.google.dev/). The code defaults to the Gemini 2.0 Flash model for its higher free-tier limits. While Pro models (e.g., 1.5 or 2.5 Pro) offer better accuracy, they have lower rate limits so are less practical to use with a free key.

Gemini 2.0 Flash may be suitable for analyzing 300-600 cases/day depending on the length of the case decisions. See model options [here](https://ai.google.dev/gemini-api/docs/models) and rate limits [here](https://ai.google.dev/gemini-api/docs/rate-limits).

You can use other APIs (e.g., OpenAI), but you'll need to modify the code accordingly. Only use local LLMs (e.g., Ollama, Deepseek) if they’re large models (70B+ recommended); otherwise, accuracy will significantly drop. The code optimized for Gemini models.

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

2. Remove the `.gitkeep` files from the json/, data/extracted_batches/ and data/extracted_sections/ directories.

3. Open the scrape-chunks.py and scrape-individual.py scripts. At the beginning of both files, where it says `ENTER KEY HERE`, replace that with your actual API key.

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

### Testing

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