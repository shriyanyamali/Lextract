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

gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)

DEFAULT_MODEL = "gemini-2.0-flash"

model = genai.GenerativeModel(model_name=DEFAULT_MODEL)

def generate_content(model, input_text):
    response = model.generate_content([
        """
        I will provide you with an excerpt of text from a competition case decision. In this excerpt, you will see many market definitions. I want you to extract
        the entirety of each individual market definition. I want the output to be in a json format. 
        Also, at the very start of the document, you will find the words "Case Number:" followed by the case number, the word "Year:" followed by the year, the phrase "Policy Area:" followed by the policy area, and the word "Link:" followed by the link. Make sure that you keep the same exact case number, year, policy area, and link in the your output. It should be that the case number and link should be above each market definition. Make sure that there is not extra text in the json file, above or below the brackets.
        Also, make sure that the bracket are always one indent forward than the brackets. Make sure proper indentation is followed. Also, when you create your output, it should include what the relevant market definition is about. That is up to you to figure out. 
        I will explain more about that below.
        For example, the output should look something like this: 
        [
            {
                "case_number": "10000",
                "year": "2024",
                "policy_area:" "Merger",
                "link": "https://www.example1.com",
                "topic": "Smartphone",
                "text": "market definition text goes here"
            },
            {
                "case_number": "10000",
                "year": "2024",
                "policy_area:" "Merger",
                "link": "https://www.example1.com",
                "topic": "Laptop",
                "text": "market definition text goes here"
            },
            {
                "case_number": "10001",
                "year": "2016",
                "policy_area:" "Merger",
                "link": "https://www.example2.com",
                "topic": "Tablet",
                "text": "market definition text goes here"
            },
            {
                "case_number": "10002",
                "year": "2019",
                "policy_area:" "Merger",
                "link": "https://www.example3.com",
                "topic": "Headphones",
                "text": "market definition text goes here;"
            },
            {
                "case_number": "10003",
                "year": "2023",
                "policy_area:" "Merger",
                "link": "https://www.example4.com",
                "topic": "Smartwatch",
                "text": "market definition text goes here"
            },
            {
                "case_number": "10004",
                "year": "2014",
                "policy_area:" "Merger",
                "link": "https://www.example5.com",
                "topic": "Camera",
                "text": "market definition text goes here"
            }
        ]
        It is possible that any given case number or link can have more than one relevant market definition.
        Now, in the text I will provide you, the market definitions will not be that easy to spot. So, I will explain how to find market definitions and how to format your output. 
        Here are some notes and examples for you to help you find market definitions (may also be referred to as relevant market definitions): Relevant market definitions are typically multiple large paragraphs. Those multiple large paragraphs are part of the relevant market definition and should be included. 
        Sometimes, you will find irrelevant footnotes, notes, or numbers in the relevant market definition. In such a case, remove the numbers that are not actually part of the relevant market definition and the footnotes and any notes that are not part of the relevant market definition.
        Your answer should be a direct quote of the multiple paragraphs. Not a paraphrased or summarized version. It should be direct quotes of paragraphs.
        You may also find phrases such as "the exact market definition was left open." Though it is not exactly a relevant market definition, it should still be considered as one. Make sure to include a definition if you see that phrase.
        For each market definition, there might be some sort or bullet point or listing system within the definitions. For example, there might be numbers like (21) (22) or letters like A. B. or roman numerals like IV or V. If anything like this appears, do not include it in your final output.
        Examples of relevant market definitions include the following:
        Example: Detergents: The Commission has previously considered that there could be a separate segment for detergents, as compared to dispersants, but left the product market definition open.9 The Commission has suggested a possible subsegmentation of detergents based on the chemical group: (i) sulphonates; (ii) phenates; and (iii) salicylates; it however finally left open the product market definition. The Notifying Party considers that it is not necessary to sub-divide the market further.10 
        Example: “3.1.2. Chemical intermediates for the production of lubricant additives (20) There are multiple chemical intermediates used in the production of lubricant additives. Aniline and diphenylamine ("DPA") are two such chemical intermediates, used as an input for aminic primary antioxidants and other lubricant additives. The Commission has not previously analysed the markets for aniline or DPA. The Notifying Party submits that the precise market definition can be left open in this case. 19 (21) Vertically affected markets arise in relation to antioxidants and the sub-segment of aminic antioxidants for which aniline and DPA are inputs and are therefore considered below in the competitive assessment. (22) For the purposes of the present decision, the exact product market definition for chemical intermediates, in particular aniline and DPA, can be left open since the Proposed Transaction does not raise serious doubts as to its compatibility with the internal market,”
        Example: Flame retardants are chemicals incorporated into a variety of manufactured materials to increase their resistance to ignition, or by acting to slow down combustion. (27) The Notifying Party submits that flame retardants should be sub-segmented according to the chemistry used, for example: (i) brominated; (ii) chlorinated; (iii) aluminium tri-hydroxide based; and (iv) phosphorus based. It argues that it would not be appropriate to sub-segment the market further based on end application, for example for use in: (i) PVC; (ii) polyamides; or (iii) polyurethane ("PU"); because the same type of flame retardants can be used for different applications and different types of flame retardants can be used for the same application.21 (28) The Commission has previously noted that flame retardants can differ depending on the chemistry used or on the basis of the application but that manufacturers of flame retardants can use different inputs to achieve flame retardants with comparable characteristics. 22 The Commission found that the market could potentially be sub-segmented by type but it ultimately left the market definition open, undertaking the assessment based on the market broken down by chemistry and end application. 23 (29) The market investigation was inconclusive as to whether it would be appropriate to further segment the market according to chemistry used. The vast majority of respondents consider that flame retardants based on different chemistries can be used for the same end applications in some cases, but not all. 24 (30) In turn, the market investigation was also inconclusive as to whether it could be appropriate to sub-segment either phosphorus or bromine based flame retardants according to end use. The vast majority of respondents consider that products based on a particular chemistry are partially interchangeable in that they can be used for some end-applications, but not all. 25 In particular, a slight majority consider that certain phosphorus based flame retardants are better suited for PVC applications26 and the majority of respondents consider that certain phosphorus based flame retardants are better suited for PU applications. 27 (31) A horizontally affected market arises in relation to bromine based flame retardants and a few market participants raised concerns regarding phosphorus based flame retardants which are therefore considered below in the competitive assessment. For the purpose of the present decision, the exact scope of the product market definition for flame retardants and its sub-segments therein can be left open, since no serious doubts as to the compatibility of the Proposed Transaction with the internal market arise, regardless of whether the market is considered to be broken down by chemistry or further broken down by end application.
        Example: Trimethylolpropane ("TMP") is a polyhydric alcohol that serves, inter alia, as an input into trimethylolpropane branched hydroxyl terminated saturated polyester and it is, thus, a common building block in the polymer industry. Chemtura uses TMP for the production of: (i) resins; (ii) PU-hardeners; and (iii) lubricant products; although it also has other uses.29 (37) The Commission has previously considered whether TMP is part of an overall market for polyhydric alcohols or forms a separate product market but has left the product market definition open.30 It has never considered further segmenting the market for TMP. (38) The Notifying Party considers that TMP is substitutable with other polyhydric alcohols therefore that the relevant market should be defined as including all polyhydric alcohols. Moreover, the Notifying Party submits that it supplies one grade of TMP for all applications.31 (39) A vertically affected market arises in relation to the supply of TMP therefore this market which is therefore considered below in the competitive assessment. (40) For the purpose of the present decision, the exact scope of the product market definition for the supply of TMP can be left open, since no serious doubts as to the compatibility of the Proposed Transaction with the internal market arise even under the narrowest possible market definition (that is TMP).
        Also, the text I provide you might have some words separated by spaces. For example, the word "example" might be displayed as "exa mple". If you see any words like that, remove the space or spaces that are separating both parts of the word and put the word back together. If there are two words that are spelled correctly, and are separated by a space, do not remove the space or spaces. Only put word fragments together if you know that by putting the fragments together, it fixes the word. Lastly, the relevant market definition is always at least 4 sentences long, but never longer than 12 sentences. Also, it is typically the ending part of a certain topic or product.
        Now, based on what I just told you, extract all of the individual relevant market definitions from the following text:
        """ + input_text
    ])
    return response

# find input files with extracted sections
def main():
    parser = argparse.ArgumentParser(
        description="Batch-extract each market definition as JSON from section files using Gemini"
    )
    parser.add_argument(
        "--indir", default="data/extracted_sections",
        help="Directory containing extract-sections_<_size_>_batch_<n>.txt files"
    )
    parser.add_argument(
        "--outdir", default="json",
        help="Directory to write extract-definitions_<size>_batch_<n>.json files"
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help="Gemini model to use"
    )
    args = parser.parse_args()

    global model
    if args.model != DEFAULT_MODEL:
        model = genai.GenerativeModel(model_name=args.model)

    os.makedirs(args.indir, exist_ok=True)
    os.makedirs(args.outdir, exist_ok=True)

    pattern = os.path.join(args.indir, 'extract-sections_*_batch_*.txt')
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"No section files found in {args.indir} matching pattern")
        return

    # extract definitions with Gemini and save as JSON with metadata
    for path in files:
        fname = os.path.basename(path)

        m = re.search(r"extract-sections_(\d+)_batch_(\d+)\.txt$", fname)
        if not m:
            continue
        size_label, batch = m.group(1), m.group(2)
        out_fname = f"extract-definitions_{size_label}_batch_{batch}.json"
        out_path = os.path.join(args.outdir, out_fname)

        print(f"Processing {fname} → {out_fname}")
        with open(path, encoding='utf-8') as f:
            input_text = f.read()
        response = generate_content(model, input_text)
        with open(out_path, 'w', encoding='utf-8') as fo:
            fo.write(response.text)
        print(f"Saved JSON → {out_fname}")

if __name__ == '__main__':
    main()