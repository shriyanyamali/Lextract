import json
input_file = r'' # Path to the JSON file containing case data

def count_unique_cases(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    unique_cases = { item.get('case_number') for item in data if 'case_number' in item }

    print(f"Found {len(unique_cases)} unique case numbers.")

if __name__ == "__main__":
    count_unique_cases(input_file)