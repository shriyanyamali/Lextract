![Maintained](https://img.shields.io/badge/Maintained-yes-green.svg) 
![License](https://img.shields.io/badge/License-MIT-green.svg) 
![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python) 
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-blue) 
![Last Commit](https://img.shields.io/github/last-commit/shriyanyamali/market-def-scraper) 


# European Commission Market Definition Scraper

## Table of Contents

- [<u>Purpose</u>](#purpose)
- [<u>Project Tree</u>](#project-tree)
- [<u>Requirements</u>](#requirements)
- [<u>Installation and Setup</u>](#installation-and-setup)
- [<u>Pipeline Scripts</u>](#pipeline-scripts)
- [<u>Non-Required Scripts</u>](#non-required-scripts)
- [<u>Usage Example</u>](#usage-example)
- [<u>Attribution</u>](#attribution)
- [<u>License</u>](#license)
- [<u>Links</u>](#links)
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

## Requirements

You will need a Google Gemini API key in order to run the `scrape-chunks.py` and `scrape-individual.py` scripts. You can get a free api key [here](https://ai.google.dev/). The code is preset to use the Gemini 2.0 Flash model. Though other models have higher accuracy, the Flash models have higher usage limits, making them the only viable option when using the free API key, as you will run into the rate limit very quickly. If you are paying for an API key and have a high budget, you can use 1.5 Pro or 2.5 Pro models for higher accuracy, but they are less cost-efficient. 

Currently, the latest Flash model is Gemini 2.5 Flash. You can use that model if the usage rates increase in the future or if you are only extracting definitions from a few cases (around 5). You can read more about all the Gemini API models [here](https://ai.google.dev/gemini-api/docs/models) and the rate limits [here](https://ai.google.dev/gemini-api/docs/rate-limits).

You are free to use the OpenAI API key or another API key, but you will need to rewrite to code to match the documentation of that API. Note that as of July 2025, this code has only been tested using the Google Gemini API, and accuracy and efficiency using other APIs cannot be guaranteed.

Locally hosted LLMs like Ollama or Deepseek can also work, but only use locally hosted LLMs if you are using a larger model (at least 70b+ but ideally 671b+) or else the accuracy will be depreciated. The installation detailed below, however, will explain how to use a Gemini API key.

## Installation and Setup

### Native (pip)

Make sure that Git and Python is installed on your system. If not, you can install the latest version of Python from [python.org/downloads](https://www.python.org/downloads/).

For Windows users, make sure that you check "Add to PATH" while installing Python, or else you will not be able to install the following packages.

1. Open your terminal or command prompt.

2. Clone the repo:

    ```
    git clone https://github.com/shriyanyamali/market-def-scraper.git
    ```

3. Move into the project directory:

   ```
   cd market-def-scraper
   ``` 

4. Install the required packages:

    ```
    pip install pandas PyPDF2 google-generativeai requests
    ```

5. Go to [competition-cases.ec.europa.eu/search](https://competition-cases.ec.europa.eu/search) and export the Merger cases you want to process. Rename the excel file `cases.xlsx`. Move the file into the data directory.

6. Remove the `.gitkeep` files from the data/extracted_batches and data/extracted_sections directories.

7. Open the `scrape-chunks.py` and `scrape-individual.py` scripts. At the beginning of both files, where it says `ENTER KEY HERE`, replace that which your actual API key.

8. Open the `run_pipeline.py` script. On line 10, follow the instructions and set `CHUNKS_SIZE` equal to `79`, `80`, or `both`. 79 means that you will only process individual batches with less than 80,000 characters, 80 means that you will only process individual batches with more than 80,000 characters, and both means you will process all batches. `79` uses the least number of tokens, and `both` uses the most.

9. Execute `run_pipeline.py` and wait for the pipeline to finish. You will receive an output detailing how many files of each type were created.

### Docker

1. Open your terminal or command prompt.

2. Clone the repo:

    ```
    git clone https://github.com/shriyanyamali/market-def-scraper.git
    ```

3. Move into the project directory:

   ```
   cd market-def-scraper
   ``` 

4. Build the image:  

    ```
    docker build -t market-def-scraper .
    ```  

5. Go to [competition-cases.ec.europa.eu/search](https://competition-cases.ec.europa.eu/search) and export the Merger cases you want to process. Rename the excel file `cases.xlsx`. Move the file into the data directory.

6. Remove the `.gitkeep` files from the data/extracted_batches and data/extracted_sections directories.

7. Open the `scrape-chunks.py` and `scrape-individual.py` scripts. At the beginning of both files, where it says `ENTER KEY HERE`, replace that which your actual API key.

8. Open the `run_pipeline.py` script. On line 10, follow the instructions and set `CHUNKS_SIZE` equal to `79`, `80`, or `both`. 79 means that you will only process individual batches with less than 80,000 characters, 80 means that you will only process individual batches with more than 80,000 characters, and both means you will process all batches. `79` uses the least number of tokens, and `both` uses the most.

9. Run the container, which will execute `run_pipeline.py`:  

    **macOS / Linux:**

    ```
    docker run --rm -v "$(pwd)/data:/app/data" market-def-scraper
    ```  

    **PowerShell:**

    ```
    docker run --rm -v ${PWD}\data:/app/data market-def-scraper
    ```

    **Command Prompt:**

    ```
    docker run --rm -v "%cd%\data:/app/data" market-def-scraper
    ```

**Note:** Do not change the names of any files, as all scripts require the file names to stay exactly the same as the original.

## Pipeline Scripts

These scripts are part of the pipeline and are executed alongside `run_pipeline.py`. The scripts run in the following order:

1. `scrape-links.py`
Extracts PDF links, case numbers, years, and policy areas from an Excel file and saves them to extracted_links.txt. Note that the excel file must include all of the aforementioned columns titled exactly how they are presented in the code or else the information will not be extracted.

2. `scrape-pdf-text.py`
Downloads decision PDFs from extracted links, filters out irrelevant cases, and saves the full text of valid documents into batch text files based on size. Files greater than 80,000 characters are titled `pdf_texts_80_batch_{batch_num}.txt`. Smaller files are labeled `pdf_texts_79_batch_{batch_num}.txt`. Despite the name, each "batch" contains only 1 extracted decision PDF.

3. `scrape-chunks.py`
Uses Gemini AI to extract the "Market Definition" section from each document and saves it in text files titled `extract-sections_79/80_batch_{batch_num}.txt` with the metadata at the top of the file. If processing just 79 batches, the number of extract-sections_batch files should match the number of pdf_texts_79_batch files. For just 80 batches, it should match the number of pdf_texts_80_batch files. If processing both, it should equal the total of both pdf_texts_79_batch and pdf_texts_80_batch files.

4. `scrape-individual.py`
Uses Gemini AI to extract individual relevant market definitions from each chunked section and outputs them as JSON titled `extract-definitions_79/80_batch_{batch_num}.json` with fields like topic, text, case_number, etc. You should have as many extract-definitions_79/80_batch files as extract-sections_79/80_batch files.

5. `clean-json.py`
Cleans up the JSON files by removing leading and trailing markdown fences ( '''json and  ``` ) which are created by Gemini in the last stage of processing. Does not create any new files.

6. `json-merge.py`
Combines all batch-level JSON files of market definitions and their metadata into a single merged JSON output file titled `output.json` located in the data directory. This is helpful if you plan to put the definitions into a database.

## Non-Required Scripts

These scripts are not part of the pipeline and can be manually executed. They are helpful for debugging, and are aptly placed in the debugging directory.

- `unique_cases_counter.py`
Counts the number of unique case numbers found in the merged JSON output.

- `word_counter.py`
Counts the total number of words in a specific batch text file. Can be helpful to see approximately how many tokens a file is using during processing.

## Usage Example

This code was used in order to create the database for [Verdictr](https://verdictr.shriyanyamali.tech/). Verdictr used the scripts in this repo to extract the market definitions and allows you to search a database of thousands of market definitions.

## Attribution

When using the code from this repo (i.e. shriyanyamali/market-def-scraper) you must provide proper attribution.

Specifically, in any work, including but not limited to public, published, commercialized, or derived work that uses or builds upon this repository's code, you must cite the original repository by including the following citation:

```
This project uses code from the market-def-scraper repository Copyright (c) 2025 Shriyan Yamali, 
licensed under the GNU Affero General Public License v3.0 (AGPL-3.0) License.

https://github.com/shriyanyamali/market-def-scraper
```

Failure to include proper attribution when using Verdictr’s code may be considered a violation of the license terms.

## License

The code in this repository is licensed under the AGPL-3.0 License.

View the full license at [www.gnu.org/licenses/agpl-3.0](https://www.gnu.org/licenses/agpl-3.0).

## Links

Here are all the links, in order, that were referred to in this README:

1. [competition-cases.ec.europa.eu/search/](https://competition-cases.ec.europa.eu/search) - European Commission Case Search Database  

2. [eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:C_202401645/](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:C_202401645) - EU Market Definition Explanation and Use

3. [www.justice.gov/atr/merger-guidelines/tools/market-definition/](https://www.justice.gov/atr/merger-guidelines/tools/market-definition) - DOJ Market Definition Explanation  

4. [www.python.org/downloads/](https://www.python.org/downloads/) - Python Download

5. [ai.google.dev](https://ai.google.dev/) - Google Gemini API Key Signup  

6. [ai.google.dev/gemini-api/docs/models/](https://ai.google.dev/gemini-api/docs/models) - Gemini API Model Documentation  

7. [ai.google.dev/gemini-api/docs/rate-limits/](https://ai.google.dev/gemini-api/docs/rate-limits) - Gemini API Rate Limits 

8. [verdictr.shriyanyamali.tech/](https://verdictr.shriyanyamali.tech/) - Verdictr Usage Example

## Contact

Email: [yamalishriyan@gmail.com](mailto:yamalishriyan@gmail.com)

Personal Website: [shriyanyamali.tech](https://shriyanyamali.tech/)

Copyright © 2025 Shriyan Yamali. All rights reserved.