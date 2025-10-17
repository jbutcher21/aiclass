#!/usr/bin/env python3
"""
SLM-based Senzing JSON Mapper
This script uses a local Small Language Model (Mistral 7B) via Ollama to generate
mapping code that transforms CSV data into Senzing JSON format.
"""

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List

import requests


class OllamaSenzingMapper:
    def __init__(self, model: str = "mistral:7b-instruct-q4_K_M", ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = model

    def create_mapping_prompt(self, csv_file: str, schema_info: str, sample_data: List[Dict]) -> str:
        """Create a comprehensive prompt for the SLM to generate mapping code."""

        prompt = f"""

Write a simple python program using standard libraries to map the records in a csv source file to json records 
and output them to a jsonl file using the mapping table below.


- all target attribute values must be scalar strings
- add a parameter for input and output files

sample json structure:
{ 
    "DATA_SOURCE": "ABC",
    "RECORD"

}

## Employee Record Mapping (`DATA_SOURCE` = `US_EMPLOYEES`, `RECORD_TYPE` = `PERSON`)
| SourceField | SenzingAttribute | Transform | Constraints | Evidence | Confidence |
| --- | --- | --- | --- | --- | --- |
| DATA_SOURCE | Hard coded to 'US_EMPLOYEES' | | | High |
| emp_num | RECORD_ID | Trim value; emit unchanged | Must remain unique within `US_EMPLOYEES` | [Spec §Attributes for the Record Key: "RECORD_ID"] | High |
| emp_num | REL_ANCHOR_DOMAIN=`US_EMPLOYEES`, REL_ANCHOR_KEY=emp_num | Emit a single REL_ANCHOR per employee | Only one anchor per record | [Spec §Feature: REL_ANCHOR: "REL_ANCHOR_KEY"] | Medium |
| last_name | NAME_LAST | Trim; combine with first/middle in one NAME object | Keep parsed person fields together | [Spec §Feature: NAME: "NAME_LAST"] | High |
| first_name | NAME_FIRST | Trim; combine with last/middle | Skip if blank | [Spec §Feature: NAME: "NAME_FIRST"] | High |
| middle_name | NAME_MIDDLE | Trim; include when present | Exclude literal `null` | [Spec §Feature: NAME: "NAME_MIDDLE"] | Medium |
| addr1 | ADDR_LINE1 | Trim | Do not emit empty strings | [Spec §Feature: ADDRESS: "ADDR_LINE1"] | High |
| city | ADDR_CITY | Trim | — | [Spec §Feature: ADDRESS: "ADDR_CITY"] | High |
| state | ADDR_STATE | Uppercase | Require two-letter code | [Spec §Feature: ADDRESS: "ADDR_STATE"] | High |
| zip | ADDR_POSTAL_CODE | Trim; preserve punctuation | Keep leading zeros | [Spec §Feature: ADDRESS: "ADDR_POSTAL_CODE"] | High |
| home_phone | PHONE_NUMBER (+PHONE_TYPE=`HOME`) | Normalize separators; set PHONE_TYPE from column semantics | One PHONE object per value | [Spec §Feature: PHONE: "PHONE_NUMBER"]; [Spec §Feature: PHONE: "PHONE_TYPE"] | High |
| dob | DATE_OF_BIRTH | Trim; emit as provided | Skip literal `null` | [Spec §Feature: DOB (Date of Birth): "DATE_OF_BIRTH"] | Medium |
| ssn | SSN_NUMBER | Trim; keep format | Validate against SSN pattern before output | [Spec §Feature: SSN (US Social Security Number): "SSN_NUMBER"] | High |
| employer_name + employer_addr | REL_POINTER_DOMAIN=`US_EMPLOYERS`, REL_POINTER_KEY=deterministic employer ID, REL_POINTER_ROLE=`EMPLOYED_BY` | Normalize employer_name/address, compute deterministic ID (e.g., SHA-1 hex of normalized pair) and emit REL_POINTER to matching employer record | Pointer key must match employer anchor key; role string standardized as `EMPLOYED_BY` | [Spec §Feature: REL_POINTER: "REL_POINTER_KEY"]; [Spec §Feature: REL_POINTER: "REL_POINTER_ROLE"] | Medium |
| id_type=`DL`, id_number, id_country | DRIVERS_LICENSE_NUMBER & DRIVERS_LICENSE_STATE | Map number/state when `DL`; uppercase state | Require both number and state | [Spec §Feature: DRLIC (Driver’s License): "DRIVERS_LICENSE_NUMBER"]; [Spec §Feature: DRLIC (Driver’s License): "DRIVERS_LICENSE_STATE"] | Medium |
| id_type=`PP`, id_number, id_country | PASSPORT_NUMBER & PASSPORT_COUNTRY | Map when `PP`; uppercase country | Require issuer country | [Spec §Feature: PASSPORT: "PASSPORT_NUMBER"]; [Spec §Feature: PASSPORT: "PASSPORT_COUNTRY"] | Medium |
| id_type other (e.g., `student_id`) | OTHER_ID_TYPE/NUMBER/COUNTRY | Use `id_type` as OTHER_ID_TYPE; trim values | Skip if number missing | [Spec §Feature: OTHER_ID: "OTHER_ID_TYPE"]; [Spec §Feature: OTHER_ID: "OTHER_ID_NUMBER"]; [Spec §Feature: OTHER_ID: "OTHER_ID_COUNTRY"] | Medium |
| manager_id | REL_POINTER_DOMAIN=`US_EMPLOYEES`, REL_POINTER_KEY=manager_id, REL_POINTER_ROLE=`REPORTS_TO` | Emit pointer when populated | Ensure anchors exist for targets | [Spec §Feature: REL_POINTER: "REL_POINTER_KEY"]; [Spec §Feature: REL_POINTER: "REL_POINTER_ROLE"] | Medium |
| sherrifs_card | OTHER_ID_TYPE=`SHERRIFS_CARD`, OTHER_ID_NUMBER | Split comma-separated tokens; trim each | Ignore blanks; optional country absent | [Spec §Feature: OTHER_ID: "OTHER_ID_TYPE"]; [Spec §Feature: OTHER_ID: "OTHER_ID_NUMBER"] | Medium |
| job_category | Root payload attribute `job_category` | Trim; emit scalar at record root | Keep outside `FEATURES`; store raw category | [Spec §Payload Attributes (Optional): "Optional root level attributes"] | Medium |
| job_title | Root payload attribute `job_title` | Trim; emit scalar at record root | Keep outside `FEATURES`; store raw title | [Spec §Payload Attributes (Optional): "Optional root level attributes"] | Medium |
| hire_date | Root payload attribute `hire_date` | Trim; emit scalar at record root | Keep outside `FEATURES`; store raw date string | [Spec §Payload Attributes (Optional): "Optional root level attributes"] | Medium |
| salary | UNMAPPED | — | Compensation outside registered features | [Spec §What Features to Map] | Medium |
| rehire_flag | UNMAPPED | — | Always `null`; no feature | [Spec §What Features to Map] | High |

"""

        return prompt

    def query_ollama(self, prompt: str) -> str:
        """Send prompt to Ollama and get response."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,  # Lower temperature for more consistent code generation
                    "top_p": 0.9,
                },
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                raise Exception(f"Ollama API error: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to Ollama. Make sure it's running with:")
            print("docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama:latest")
            sys.exit(1)

    def extract_code_from_response(self, response: str) -> str:
        """Extract Python code from the SLM response."""
        # Look for code blocks
        lines = response.split("\n")
        code_lines = []
        in_code_block = False

        for line in lines:
            if line.strip().startswith("```python"):
                in_code_block = True
                continue
            elif line.strip() == "```" and in_code_block:
                in_code_block = False
                continue
            elif in_code_block:
                code_lines.append(line)

        # If no code block found, try to extract function definition
        if not code_lines:
            in_function = False
            for line in lines:
                if line.strip().startswith("def map_to_senzing"):
                    in_function = True
                if in_function:
                    code_lines.append(line)
                    # Simple heuristic: stop at next function or class definition
                    if line.strip() and not line[0].isspace() and not line.strip().startswith("def map_to_senzing"):
                        break

        return "\n".join(code_lines)

    def test_generated_code(self, code: str, sample_data: List[Dict]) -> bool:
        """Test if the generated code works correctly."""
        try:
            # Create a namespace for execution
            namespace = {}
            exec(code, namespace)

            # Test with first record
            if "map_to_senzing" in namespace:
                result = namespace["map_to_senzing"](sample_data[0])

                # Basic validation
                required_fields = ["DATA_SOURCE", "RECORD_ID"]
                for field in required_fields:
                    if field not in result:
                        print(f"Warning: Generated code missing required field: {field}")
                        return False

                print("Generated code test passed!")
                print("Sample output:", json.dumps(result, indent=2))
                return True
            else:
                print("Error: Generated code does not contain 'map_to_senzing' function")
                return False

        except Exception as e:
            print(f"Error testing generated code: {e}")
            return False

    def generate_mapping_script(self, csv_file: str, schema_file: str, output_file: str):
        """Generate a complete mapping script using the SLM."""

        print("Reading schema information...")
        with open(schema_file, "r") as f:
            schema_info = f.read()

        print("Reading sample data...")
        sample_data = []
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                sample_data.append(row)
                if i >= 5:  # Get first 6 rows as samples
                    break

        print("Creating prompt for SLM...")
        prompt = self.create_mapping_prompt(csv_file, schema_info, sample_data)

        print("Querying Ollama (this may take a moment)...")
        response = self.query_ollama(prompt)

        print("Extracting code from response...")
        generated_code = self.extract_code_from_response(response)

        if not generated_code:
            print("Error: Could not extract code from SLM response")
            print("Raw response:", response[:500])
            return

        print("\nGenerated mapping function:")
        print("-" * 50)
        print(generated_code)
        print("-" * 50)

        # Test the generated code
        print("\nTesting generated code...")
        if self.test_generated_code(generated_code, sample_data):
            # Create complete script
            complete_script = f'''#!/usr/bin/env python3
"""
Auto-generated Senzing JSON mapper
"""

import csv
import json
import sys

{generated_code}

def main():
    if len(sys.argv) != 3:
        print("Usage: python mapper.py <input.csv> <output.jsonl>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        reader = csv.DictReader(infile)
        
        for row in reader:
            try:
                senzing_record = map_to_senzing(row)
                outfile.write(json.dumps(senzing_record) + '\\n')
            except Exception as e:
                print(f"Error processing row {{row.get('emp_num', 'unknown')}}: {{e}}")
                continue
    
    print(f"Conversion complete. Output written to {{output_file}}")

if __name__ == "__main__":
    main()
'''

            # Save the complete script
            with open(output_file, "w") as f:
                f.write(complete_script)

            print(f"\nComplete mapping script saved to: {output_file}")
            print("To use it: python mapper.py input.csv output.jsonl")
        else:
            print("\nWarning: Generated code failed testing. You may need to manually fix it.")
            print("Saving raw generated code to:", output_file + ".raw")
            with open(output_file + ".raw", "w") as f:
                f.write(generated_code)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate Senzing JSON mapping code using a Small Language Model")

    parser.add_argument("csv_file", help="Path to the input CSV file containing the data to be mapped")

    parser.add_argument("schema_file", help="Path to the schema file describing the CSV structure")

    parser.add_argument("output_file", help="Path where the generated mapping script will be saved")

    parser.add_argument(
        "--model",
        default="mistral:7b-instruct-q4_K_M",
        help="Ollama model to use (default: mistral:7b-instruct-q4_K_M)",
    )

    return parser.parse_args()


def main():
    """Main function to run the SLM-based mapper generator."""

    # Parse command line arguments
    args = parse_arguments()

    # Check if Ollama is accessible
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code != 200:
            raise Exception("Ollama not responding")
    except:
        print("Error: Cannot connect to Ollama at http://localhost:11434")
        print("Make sure Ollama is running with:")
        print("docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama:latest")
        print("\nThen pull the Mistral model:")
        print("docker exec -it ollama ollama pull mistral:7b-instruct-q4_K_M")
        sys.exit(1)

    # Check if files exist
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file not found: {args.csv_file}")
        sys.exit(1)
    if not os.path.exists(args.schema_file):
        print(f"Error: Schema file not found: {args.schema_file}")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Create mapper instance and generate script
    mapper = OllamaSenzingMapper(model=args.model)
    mapper.generate_mapping_script(args.csv_file, args.schema_file, args.output_file)


if __name__ == "__main__":
    main()
