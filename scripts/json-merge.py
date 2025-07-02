#!/usr/bin/env python3
# scripts/json-merge.py

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
