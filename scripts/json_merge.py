# =============================================================================
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
# =============================================================================

import json
import os

def combine_json_files(input_folder, output_file):
    combined_data = []

    if not os.path.exists(input_folder):
        print(f"Input folder {input_folder} does not exist.")
        return

    for filename in os.listdir(input_folder):
        if filename.endswith('.json'):
            file_path = os.path.join(input_folder, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        combined_data.extend(data)
                    else:
                        print(f"Skipping {filename}: not a list of dictionaries")
                except json.JSONDecodeError as e:
                    print(f"Skipping {filename}: JSONDecodeError - {e}")

    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as out_f:
            json.dump(combined_data, out_f, indent=4)
        print(f"Combined JSON files saved to {output_file}")
    except IOError as e:
        print(f"Failed to write to {output_file}: IOError - {e}")


def main():
    input_folder = 'json'
    output_file = os.path.join('data', 'output.json') 

    combine_json_files(input_folder, output_file)

if __name__ == '__main__':
    main()
