#!/usr/bin/env python3
"""
SLM-based Senzing JSON Mapper
This script uses a local Small Language Model (Mistral 7B) via Ollama to generate
mapping code that transforms CSV data into Senzing JSON format.
"""

import json
import requests
import sys
import os
import csv
from typing import Dict, List, Any

class OllamaSenzingMapper:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "mistral:7b-instruct-q4_K_M"
        # self.model = "tinyllama"
        
    def create_mapping_prompt(self, schema_info: str, sample_data: List[Dict]) -> str:
        """Create a comprehensive prompt for the SLM to generate mapping code."""
        
        prompt = f"""You are a data mapping expert. Generate Python code to convert CSV records to Senzing JSON format.

        INPUT SCHEMA:
        {schema_info}

        SAMPLE INPUT RECORDS (first 3 rows):
        {json.dumps(sample_data[:3], indent=2)}

        SENZING JSON REQUIREMENTS:
        1. Each record must have DATA_SOURCE (use "EMPLOYEES") and RECORD_ID (use emp_num)
        2. Map person names: last_name→NAME_LAST, first_name→NAME_FIRST, middle_name→NAME_MIDDLE
        3. Map address: addr1→ADDR_LINE1, city→ADDR_CITY, state→ADDR_STATE, zip→ADDR_POSTAL_CODE
        4. Map identifiers: ssn→SSN_NUMBER, home_phone→PHONE_NUMBER, dob→DATE_OF_BIRTH
        5. Map employment: employer_name→EMPLOYER, job_title→JOB_TITLE
        6. Handle multiple IDs: if id_type="DL" map to DRIVERS_LICENSE_NUMBER with DRIVERS_LICENSE_STATE
        7. If id_type="PP" map to PASSPORT_NUMBER with PASSPORT_COUNTRY
        8. Handle manager relationships using REL_ANCHOR_DOMAIN="EMP_ID" and REL_POINTER_DOMAIN="EMP_ID"
        9. Skip null/empty values
        10. Output one JSON object per line (JSONL format)

        Generate ONLY the Python function that takes a CSV row dict and returns a Senzing JSON dict.
        You MUST use the provided CSV file, do NOT make one up!
        Include all necessary package imports, but only use standard libraries.
        The function should be named 'map_to_senzing' and handle all mappings cleanly.
        Include proper error handling and data cleaning.
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
                }
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to Ollama. Make sure it's running with:")
            print("docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama:latest")
            sys.exit(1)
    
    def extract_code_from_response(self, response: str) -> str:
        """Extract Python code from the SLM response."""
        # Look for code blocks
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```python'):
                in_code_block = True
                continue
            elif line.strip() == '```' and in_code_block:
                in_code_block = False
                continue
            elif in_code_block:
                code_lines.append(line)
        
        # If no code block found, try to extract function definition
        if not code_lines:
            in_function = False
            for line in lines:
                if line.strip().startswith('def map_to_senzing'):
                    in_function = True
                if in_function:
                    code_lines.append(line)
                    # Simple heuristic: stop at next function or class definition
                    if line.strip() and not line[0].isspace() and not line.strip().startswith('def map_to_senzing'):
                        break
        
        return '\n'.join(code_lines)
    
    def test_generated_code(self, code: str, sample_data: List[Dict]) -> bool:
        """Test if the generated code works correctly."""
        try:
            # Create a namespace for execution
            namespace = {}
            exec(code, namespace)
            
            # Test with first record
            if 'map_to_senzing' in namespace:
                result = namespace['map_to_senzing'](sample_data[0])
                
                # Basic validation
                required_fields = ['DATA_SOURCE', 'RECORD_ID']
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
        with open(schema_file, 'r') as f:
            schema_info = f.read()
        
        print("Reading sample data...")
        sample_data = []
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                sample_data.append(row)
                if i >= 5:  # Get first 6 rows as samples
                    break
        
        print("Creating prompt for SLM...")
        prompt = self.create_mapping_prompt(schema_info, sample_data)
        
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
Generated using Mistral 7B via Ollama
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
            with open(output_file, 'w') as f:
                f.write(complete_script)
            
            print(f"\nComplete mapping script saved to: {output_file}")
            print("To use it: python mapper.py input.csv output.jsonl")
        else:
            print("\nWarning: Generated code failed testing. You may need to manually fix it.")
            print("Saving raw generated code to:", output_file + ".raw")
            with open(output_file + ".raw", 'w') as f:
                f.write(generated_code)

def main():
    """Main function to run the SLM-based mapper generator."""
    
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
    
    # File paths
    csv_file = "employee_demo/data/us-small-employee-raw.csv"
    schema_file = "employee_demo/schema/us-small-employee-schema.csv"
    output_file = "generated_mapper.py"
    
    # Check if files exist
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)
    if not os.path.exists(schema_file):
        print(f"Error: Schema file not found: {schema_file}")
        sys.exit(1)
    
    # Create mapper instance and generate script
    mapper = OllamaSenzingMapper()
    mapper.generate_mapping_script(csv_file, schema_file, output_file)

if __name__ == "__main__":
    main()