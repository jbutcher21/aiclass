"""
Convert us-small-employee-raw.csv to Senzing JSONL format.
- Creates PERSON and ORGANIZATION entities
- Maps all fields per approved mapping
- Relates employees to employers and managers
"""

import csv
import json
from collections import defaultdict

INPUT_FILE = "data/us-small-employee-raw.csv"
OUTPUT_FILE = "data/senzing-employee.jsonl"

# Helper to create organization key
ORG_KEY_FIELDS = ["employer_name", "employer_addr"]


def org_key(row):
    return f"{row['employer_name']}|{row['employer_addr']}"


def main():
    # First pass: collect all employees and organizations
    employees = {}
    organizations = {}
    manager_map = defaultdict(list)

    with open(INPUT_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            emp_id = row["emp_num"]
            employees[emp_id] = row
            # Build org entity
            org_id = org_key(row)
            if org_id not in organizations:
                organizations[org_id] = {
                    "DATA_SOURCE": "EMPLOYERS",
                    "RECORD_ID": org_id,
                    "RECORD_TYPE": "ORGANIZATION",
                    "FEATURES": [{"NAME_ORG": row["employer_name"]}, {"ADDR_LINE1": row["employer_addr"]}],
                }
            # Track manager relationships
            if row.get("manager_id"):
                manager_map[row["manager_id"]].append(emp_id)

    # Second pass: write JSONL
    with open(OUTPUT_FILE, "w") as out:
        # Write organizations
        for org in organizations.values():
            out.write(json.dumps(org) + "\n")
        # Write employees
        for emp_id, row in employees.items():
            entity = {
                "DATA_SOURCE": "EMPLOYEES",
                "RECORD_ID": emp_id,
                "RECORD_TYPE": "PERSON",
                "FEATURES": [
                    {"NAME_LAST": row["last_name"], "NAME_FIRST": row["first_name"], "NAME_MIDDLE": row["middle_name"]},
                    {
                        "ADDR_TYPE": "HOME",
                        "ADDR_LINE1": row["addr1"],
                        "ADDR_CITY": row["city"],
                        "ADDR_STATE": row["state"],
                        "ADDR_POSTAL_CODE": row["postal_code"],
                    },
                    {"PHONE_TYPE": "HOME", "PHONE_NUMBER": row["home_phone"]},
                    {"DATE_OF_BIRTH": row["dob"]},
                    {"SSN_NUMBER": row["ssn"]},
                    {"REL_ANCHOR_DOMAIN": "EMPLOYEES", "REL_ANCHOR_KEY": emp_id},
                ],
                "job_category": row["job_category"],
                "job_title": row["job_title"],
                "hire_date": row["hire_date"],
                "salary": row["salary"],
                "rehire_flag": row["rehire_flag"],
            }
            # Employer relationship
            org_id = org_key(row)
            entity["FEATURES"].append(
                {"REL_POINTER_DOMAIN": "EMPLOYERS", "REL_POINTER_KEY": org_id, "REL_POINTER_ROLE": "EMPLOYED_BY"}
            )
            # Manager relationship
            if row.get("manager_id") and row["manager_id"] in employees:
                entity["FEATURES"].append(
                    {
                        "REL_POINTER_DOMAIN": "EMPLOYEES",
                        "REL_POINTER_KEY": row["manager_id"],
                        "REL_POINTER_ROLE": "REPORTS_TO",
                    }
                )
            # Other ID
            if row.get("other_id_type") and row.get("other_id_number"):
                entity["FEATURES"].append(
                    {
                        "OTHER_ID_TYPE": row["other_id_type"],
                        "OTHER_ID_NUMBER": row["other_id_number"],
                        "OTHER_ID_COUNTRY": row.get("other_id_country", ""),
                    }
                )
            # SHERRIFS_CARD
            if row.get("sherrifs_card"):
                entity["FEATURES"].append({"SHERRIFS_CARD": row["sherrifs_card"]})
            out.write(json.dumps(entity) + "\n")


if __name__ == "__main__":
    main()
