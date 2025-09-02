# Senzing Employee Mapper: Source to Senzing Attribute Mapping

## Mapping Table

| Source Field         | Senzing Attribute / Feature           | Notes / Logic                                                                 |
|---------------------|---------------------------------------|-------------------------------------------------------------------------------|
| emp_num             | RECORD_ID                             | Unique employee identifier (root)                                             |
| last_name           | NAME_LAST                             | Employee last name (FEATURE: NAME)                                            |
| first_name          | NAME_FIRST                            | Employee first name (FEATURE: NAME)                                           |
| middle_name         | NAME_MIDDLE                           | Employee middle name (FEATURE: NAME)                                          |
| addr1               | ADDR_LINE1                            | Employee address line 1 (FEATURE: ADDRESS, ADDR_TYPE: HOME)                   |
| city                | ADDR_CITY                             | Employee address city (FEATURE: ADDRESS, ADDR_TYPE: HOME)                     |
| state               | ADDR_STATE                            | Employee address state (FEATURE: ADDRESS, ADDR_TYPE: HOME)                    |
| postal_code         | ADDR_POSTAL_CODE                      | Employee address postal code (FEATURE: ADDRESS, ADDR_TYPE: HOME)              |
| home_phone          | PHONE_NUMBER, PHONE_TYPE: HOME         | Employee home phone (FEATURE: PHONE)                                          |
| dob                 | DATE_OF_BIRTH                         | Employee date of birth (FEATURE: DOB)                                         |
| ssn                 | SSN_NUMBER                            | Employee SSN (FEATURE: SSN)                                                   |
| job_category        | PAYLOAD: job_category                  | Mapped as payload attribute                                                   |
| job_title           | PAYLOAD: job_title                     | Mapped as payload attribute                                                   |
| hire_date           | PAYLOAD: hire_date                     | Mapped as payload attribute                                                   |
| salary              | PAYLOAD: salary                        | Mapped as payload attribute                                                   |
| rehire_flag         | PAYLOAD: rehire_flag                   | Mapped as payload attribute                                                   |
| employer_name       | ORGANIZATION entity: NAME_ORG          | Create separate ORGANIZATION entity; relate employee via REL_POINTER          |
| employer_addr       | ORGANIZATION entity: ADDR_LINE1, etc.  | Create separate ORGANIZATION entity; relate employee via REL_POINTER          |
| other_id_type       | OTHER_ID_TYPE                          | For unmapped identifiers, use OTHER_ID_TYPE                                   |
| other_id_number     | OTHER_ID_NUMBER                        | For unmapped identifiers, use OTHER_ID_NUMBER                                 |
| other_id_country    | OTHER_ID_COUNTRY                       | For unmapped identifiers, use OTHER_ID_COUNTRY                                |
| manager_id          | REL_POINTER (role: REPORTS_TO)         | Create relationship to manager entity                                         |
| sherrifs_card       | SHERRIFS_CARD (feature/attribute)      | Map to new identifier feature SHERRIFS_CARD (per user approval)               |

---

## Special Logic & Directives

- `home_phone` is always mapped as PHONE_TYPE: "HOME".
- For each employee, create a related ORGANIZATION entity using `employer_name` and `employer_addr`, and relate via REL_POINTER (role: "EMPLOYED_BY").
- `sherrifs_card` is mapped to a new identifier feature SHERRIFS_CARD.
- `manager_id` creates a REL_POINTER relationship to another employee (role: "REPORTS_TO").
- All other fields not listed above are excluded from mapping.

---

## User Directives

- Use only the latest Senzing Entity Specification from the provided URL.
- Show mappings for user review before coding.
- Add REL_ANCHOR feature to each employee so they can be referenced.
- Create ORGANIZATION entities for employers and relate employees to them.
- Add new feature for SHERRIFS_CARD as approved.
- Create relationships between employees using manager_id.

---

## Example Senzing JSON Output (Employee)

```json
{
  "DATA_SOURCE": "EMPLOYEES",
  "RECORD_ID": "123",
  "RECORD_TYPE": "PERSON",
  "FEATURES": [
    {"NAME_LAST": "Smith", "NAME_FIRST": "Jane", "NAME_MIDDLE": "A"},
    {"ADDR_TYPE": "HOME", "ADDR_LINE1": "123 Main St", "ADDR_CITY": "Las Vegas", "ADDR_STATE": "NV", "ADDR_POSTAL_CODE": "89132"},
    {"PHONE_TYPE": "HOME", "PHONE_NUMBER": "702-919-1300"},
    {"DATE_OF_BIRTH": "12/11/1978"},
    {"SSN_NUMBER": "477-33-1025"},
    {"REL_ANCHOR_DOMAIN": "EMPLOYEES", "REL_ANCHOR_KEY": "123"},
    {"REL_POINTER_DOMAIN": "EMPLOYERS", "REL_POINTER_KEY": "ABC Company|111 First St, anytown USA", "REL_POINTER_ROLE": "EMPLOYED_BY"},
    {"REL_POINTER_DOMAIN": "EMPLOYEES", "REL_POINTER_KEY": "456", "REL_POINTER_ROLE": "REPORTS_TO"},
    {"SHERRIFS_CARD": "A224-5698"}
  ],
  "job_category": "sales",
  "job_title": "Senior sales person",
  "hire_date": "1/10/10",
  "salary": "75k",
  "rehire_flag": "null"
}
```

---

## Special Logic
- Employer and manager relationships are only created if referenced IDs exist in the data.
- SHERRIFS_CARD is mapped as a dedicated feature per user approval.
- All mapping follows the Senzing specification and user directives above.
