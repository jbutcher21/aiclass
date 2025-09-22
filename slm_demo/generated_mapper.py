#!/usr/bin/env python3
"""
Auto-generated Senzing JSON mapper
Generated using Mistral 7B via Ollama
"""

import csv
import json
import sys

import csv
from typing import Dict, List

def map_to_senzing(row: Dict) -> Dict:
    """
    Maps a CSV row to Senzing JSON format.
    :param row: A CSV row as a dictionary.
    :return: A Senzing JSON formatted dictionary.
    """
    data_source = "EMPLOYEES"
    record_id = row.get("emp_num", "")
    features = []
    
    if row.get("last_name"):
        name_last = row["last_name"]
        name_first = row.get("first_name", "")
        features.append({"RECORD_TYPE": "PERSON", "NAME_LAST": name_last, "NAME_FIRST": name_first})
    
    if row.get("middle_name"):
        name_mid = row["middle_name"]
        features.append({"RECORD_TYPE": "PERSON", "NAME_MIDDLE": name_mid})
    
    if row.get("addr1"):
        addr_line1 = row["addr1"]
        addr_city = row.get("city", "")
        addr_state = row.get("state", "")
        addr_zip = row.get("zip", "")
        features.append({"RECORD_TYPE": "ADDRESS", "ADDR_LINE1": addr_line1, "ADDR_CITY": addr_city, "ADDR_STATE": addr_state, "ADDR_POSTAL_CODE": addr_zip})
    
    if row.get("dob"):
        date_of_birth = row["dob"]
        features.append({"RECORD_TYPE": "DATE", "DATE_OF_BIRTH": date_of_birth})
    
    if row.get("ssn"):
        ssn_number = row["ssn"]
        features.append({"RECORD_TYPE": "SSN", "SSN_NUMBER": ssn_number})
    
    if row.get("home_phone"):
        phone_number = row["home_phone"]
        features.append({"RECORD_TYPE": "PHONE_NUMBER", "PHONE_NUMBER": phone_number})
    
    if row.get("drivers_license_number") and "-" in row["drivers_license_number"]:
        dl_number = row["drivers_license_number"].split("-", 1)[0].strip()
        dl_state = row["drivers_license_number"].split("-", 1)[1].strip()
        features.append({"RECORD_TYPE": "DRIVERS_LICENSE", "DRIVERS_LICENSE_NUMBER": dl_number, "DRIVERS_LICENSE_STATE": dl_state})
    elif row.get("passport_number"):
        passport_number = row["passport_number"]
        features.append({"RECORD_TYPE": "PASSPORT", "PASSPORT_NUMBER": passport_number, "PASSPORT_COUNTRY": "US"})
    
    if row.get("manager_id"):
        manager_id = row["manager_id"]
        features.append({"RECORD_TYPE": "EMPLOYMENT", "REL_ANCHOR_DOMAIN": "EMP_ID", "REL_ANCHOR_KEY": record_id})
        features.append({"RECORD_TYPE": "EMPLOYMENT", "REL_POINTER_DOMAIN": "EMP_ID", "REL_POINTER_KEY": manager_id, "REL_POINTER_ROLE": "REPORTS_TO"})
    
    return {
        "DATA_SOURCE": data_source,
        "RECORD_ID": record_id,
        "FEATURES": features
    }

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
                outfile.write(json.dumps(senzing_record) + '\n')
            except Exception as e:
                print(f"Error processing row {row.get('emp_num', 'unknown')}: {e}")
                continue
    
    print(f"Conversion complete. Output written to {output_file}")

if __name__ == "__main__":
    main()
