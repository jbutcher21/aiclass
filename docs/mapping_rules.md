# Mapping Rules and Quick Reference

This document complements the system prompt. Paste this with your schema as user context. It summarizes practical rules, templates, examples, and implementation sketches. The authoritative source remains `senzing_entity_specification.md`.

## Quick Rules Checklist
- Record keys: `DATA_SOURCE` required; `RECORD_ID` strongly desired; construct deterministic IDs if missing.
- JSON structure: prefer the `FEATURES` list structure. One feature family per object; do not mix families; avoid lists inside a single feature object.
- Names: prefer parsed person names; use `NAME_ORG` for organizations; use `NAME_FULL` when type is unknown.
- Addresses: use parsed fields when available; otherwise `ADDR_FULL`. Do not include both parsed fields and `ADDR_FULL` for the same address.
- Phones: map `PHONE_NUMBER`; set `PHONE_TYPE` only when clear; `MOBILE` has special weighting.
- Identifiers: map to specific features (e.g., PASSPORT, SSN, DRLIC) before generic `NATIONAL_ID`/`TAX_ID`/`OTHER_ID`; include issuing country/state where applicable. `NATIONAL_ID_TYPE` and `TAX_ID_TYPE` may be left blank when the issuer country is mapped and the type is not standardized.
- Usage types: include only when present in source. Special meanings: `NAME_TYPE=PRIMARY`, org `ADDR_TYPE=BUSINESS`, `PHONE_TYPE=MOBILE`.
- Group associations vs relationships: use `EMPLOYER`/`GROUP_ASSOCIATION`/`GROUP_ASSN_ID` features to aid resolution; use `REL_ANCHOR/REL_POINTER` features to declare disclosed relationships (see Canonical Relationship Attributes).
- Relationship rules: add exactly one `REL_ANCHOR` feature attributes object per record that can be referenced; put `REL_POINTER` feature attributes on the source of each relationship pointing to the target’s anchor; do not mix anchor/pointer in the same feature object.
- Payload: optional; small and non‑PII; not used for matching.
- Validation: all JSON/JSONL examples must pass the linter before finalizing.

## Deterministic Keys (RECORD_ID and REL_*_KEY)
- When the source lacks a trustworthy primary key, derive a deterministic key instead of using a label or name.
- Rule: `RECORD_ID` is the SHA‑256 of the normalized, concatenated values of all mapped feature attribute values for that record (payload). 
- Alignment: For any record with relationships, set `REL_ANCHOR_KEY` equal to that record’s `RECORD_ID`. Any `REL_POINTER_KEY` that targets it must use the exact same value.
- Normalization (policy, not code):
  - Trim, collapse internal whitespace to a single space, and normalize Unicode (e.g., NFKD).
  - Uppercase; remove punctuation except alphanumerics and spaces.
  - Build canonical tokens per mapped attribute as `FAMILY.ATTR=value`. For repeated features (e.g., multiple phones), include one token per occurrence. Sort all tokens lexicographically and join with a fixed separator (e.g., `|`) before hashing.

## Canonical Relationship Attributes (No Shorthand)
- Allowed keys only: `REL_ANCHOR_DOMAIN`, `REL_ANCHOR_KEY`, `REL_POINTER_DOMAIN`, `REL_POINTER_KEY`, `REL_POINTER_ROLE`.
- Forbidden keys: `REL_ANCHOR`, `REL_POINTER` (these are family names in prose, not attribute names). Do not emit them in JSON.
- One anchor per record max; any number of pointers allowed. Do not mix anchor and pointer attributes in the same feature object.

## Note on Embedded Entities
In single‑schema sources, look for embedded related entities (e.g., employer fields on contacts; sender/receiver in wires). If only a name exists, consider a group association. If resolvable features exist (address, phone, identifiers), consider a separate related entity with a disclosed relationship.

## Templates

### Mapping Table (markdown)
| Source Path | Notes | Senzing Mapping |
| --- | --- | --- |
| customers.id | unique per row | DATA_SOURCE=CUSTOMERS; RECORD_ID=id |
| customers.first_name |  | FEATURES[{ NAME_FIRST }] |
| customers.last_name |  | FEATURES[{ NAME_LAST }] |
| customers.dob | format: YYYY-MM-DD | FEATURES[{ DATE_OF_BIRTH }] |
| customers.home_phone | type derivable | FEATURES[{ PHONE_TYPE=MOBILE?; PHONE_NUMBER }] |

### Relationship Template (anchor/pointer)
- Anchor entity: `FEATURES[{ REL_ANCHOR_DOMAIN=<CODE>, REL_ANCHOR_KEY=<RECORD_ID> }]`
- Pointer entity: `FEATURES[{ REL_POINTER_DOMAIN=<CODE>, REL_POINTER_KEY=<ANCHOR_ID>, REL_POINTER_ROLE=<ROLE> }]`

### JSON Skeleton (populate then lint)
```
{
  "DATA_SOURCE": "<CODE>",
  "RECORD_ID": "<UNIQUE_ID>",
  "FEATURES": [
    { "RECORD_TYPE": "PERSON" },
    { "NAME_LAST": "<LAST>", "NAME_FIRST": "<FIRST>" },
    { "DATE_OF_BIRTH": "<YYYY-MM-DD|MM/DD/YYYY>" },
    { "ADDR_LINE1": "<LINE1>", "ADDR_CITY": "<CITY>", "ADDR_STATE": "<STATE>", "ADDR_POSTAL_CODE": "<ZIP>", "ADDR_COUNTRY": "<CC>" },
    { "PHONE_NUMBER": "<NUMBER>", "PHONE_TYPE": "<MOBILE?>" },
    { "REL_ANCHOR_DOMAIN": "<REL_DOMAIN>", "REL_ANCHOR_KEY": "<THIS_RECORD_ID>" },
    { "REL_POINTER_DOMAIN": "<REL_DOMAIN>", "REL_POINTER_KEY": "<TARGET_ANCHOR_ID>", "REL_POINTER_ROLE": "EMPLOYED_BY" }
  ],
  "CUSTOMER_SINCE": "<YYYY-MM-DD>",
  "STATUS": "<Active|Inactive>"
}
```

## REL_POINTER_ROLE Glossary (suggested values)
- `EMPLOYED_BY`: person → organization employment.
- `OFFICER_OF`: person → organization officer/director.
- `OWNER_OF`: person → organization ownership.
- `BENEFICIAL_OWNER_OF`: person → organization beneficial ownership.
- `SPOUSE_OF`: person → person spousal relationship.
- `PARENT_OF` / `CHILD_OF`: directional familial relationships.
- `SUBSIDIARY_OF`: organization → parent organization.
- `PARTNER_OF`: organization ↔ organization partnership.
- `CO_SIGNER_OF`: person → person co-signer (e.g., loans).
- `MEMBER_OF`: person → organization membership (when not using GROUP_ASSOCIATION).

## Validation Commands
- Lint a file: `python3 tools/lint_senzing_json.py path/to/output.jsonl`
- Lint a directory: `python3 tools/lint_senzing_json.py path/to/dir`

## Payload Examples (optional and minimal)
- `CUSTOMER_SINCE`: date the subject became a customer; ISO‑8601 preferred.
- `STATUS`: normalized operational status like Active/Inactive.
- Organization payload: `INDUSTRY`, `ORG_STATUS`.
- Important: `REGISTRATION_DATE` and `REGISTRATION_COUNTRY` are FEATURES, not payload.

Example (organization with payload and registration feature):
```json
{
  "DATA_SOURCE": "ORG",
  "RECORD_ID": "O-100",
  "FEATURES": [
    { "RECORD_TYPE": "ORGANIZATION" },
    { "NAME_ORG": "Acme Tire Inc." },
    { "REGISTRATION_DATE": "2015-03-31" },
    { "REL_ANCHOR_DOMAIN": "CORP", "REL_ANCHOR_KEY": "O-100" },
    { "REL_POINTER_DOMAIN": "CORP", "REL_POINTER_KEY": "O-500", "REL_POINTER_ROLE": "SUBSIDIARY_OF" }
  ],
  "INDUSTRY": "Automotive Retail",
  "ORG_STATUS": "Active"
}
```

## Relationship Examples
Employment (anchor/pointer)
```
Organization (anchor)
{
  "DATA_SOURCE": "ORG",
  "RECORD_ID": "O-100",
  "FEATURES": [
    { "RECORD_TYPE": "ORGANIZATION" },
    { "NAME_ORG": "Acme Tire Inc." },
    { "REL_ANCHOR_DOMAIN": "HR", "REL_ANCHOR_KEY": "O-100" }
  ]
}
```

Spouse (person ↔ person)
```
Person A (anchor)
{
  "DATA_SOURCE": "PEOPLE",
  "RECORD_ID": "P-10",
  "FEATURES": [
    { "RECORD_TYPE": "PERSON" },
    { "NAME_FIRST": "Alex", "NAME_LAST": "Taylor" },
    { "REL_ANCHOR_DOMAIN": "FAMILY", "REL_ANCHOR_KEY": "P-10" }
  ]
}

Person B (anchor + pointer)
{
  "DATA_SOURCE": "PEOPLE",
  "RECORD_ID": "P-11",
  "FEATURES": [
    { "RECORD_TYPE": "PERSON" },
    { "NAME_FIRST": "Sam", "NAME_LAST": "Taylor" },
    { "REL_ANCHOR_DOMAIN": "FAMILY", "REL_ANCHOR_KEY": "P-11" },
    { "REL_POINTER_DOMAIN": "FAMILY", "REL_POINTER_KEY": "P-10", "REL_POINTER_ROLE": "SPOUSE_OF" }
  ]
}
```

Subsidiary (org ↔ org)
```
Parent Org (anchor)
{
  "DATA_SOURCE": "ORG",
  "RECORD_ID": "O-500",
  "FEATURES": [
    { "RECORD_TYPE": "ORGANIZATION" },
    { "NAME_ORG": "Global Holdings LLC" },
    { "REL_ANCHOR_DOMAIN": "CORP", "REL_ANCHOR_KEY": "O-500" }
  ]
}

Subsidiary Org (anchor + pointer)
{
  "DATA_SOURCE": "ORG",
  "RECORD_ID": "O-501",
  "FEATURES": [
    { "RECORD_TYPE": "ORGANIZATION" },
    { "NAME_ORG": "Regional Ops Inc." },
    { "REL_ANCHOR_DOMAIN": "CORP", "REL_ANCHOR_KEY": "O-501" },
    { "REL_POINTER_DOMAIN": "CORP", "REL_POINTER_KEY": "O-500", "REL_POINTER_ROLE": "SUBSIDIARY_OF" }
  ]
}
```

## Implementation Tips (optional)

### Pandas sketch
```python
import pandas as pd

persons = pd.read_parquet('persons.parquet')
phones = pd.read_parquet('phones.parquet')
rels = pd.read_parquet('employment.parquet')
orgs = pd.read_parquet('orgs.parquet')

phone_lists = phones.groupby('person_id').apply(lambda df: df.to_dict('records')).rename('phone_features')
persons = persons.join(phone_lists, on='person_id')
persons['phone_features'] = persons['phone_features'].fillna([])

rels = rels.assign(REL_POINTER_ROLE=lambda d: d['role'].fillna('EMPLOYED_BY'))
rel_lists = rels.groupby('person_id').apply(lambda df: [
    {
        'REL_POINTER_DOMAIN': 'HR',
        'REL_POINTER_KEY': str(row.org_id),
        'REL_POINTER_ROLE': row.REL_POINTER_ROLE
    } for row in df.itertuples(index=False)
]).rename('rel_pointers')
persons = persons.join(rel_lists, on='person_id')
persons['rel_pointers'] = persons['rel_pointers'].fillna([])

def to_senzing(row):
    features = [
        {'RECORD_TYPE': 'PERSON'},
        {'NAME_FIRST': row.first_name, 'NAME_LAST': row.last_name},
        {'DATE_OF_BIRTH': row.dob},
        {'REL_ANCHOR_DOMAIN': 'HR', 'REL_ANCHOR_KEY': str(row.person_id)},
    ]
    features += [{'PHONE_NUMBER': p['phone_number'], 'PHONE_TYPE': p.get('phone_type')} for p in row.phone_features]
    features += row.rel_pointers
    return {
        'DATA_SOURCE': 'PEOPLE',
        'RECORD_ID': str(row.person_id),
        'FEATURES': features
    }
```

### PySpark sketch
```python
from pyspark.sql import functions as F
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
persons = spark.read.parquet('persons.parquet')
phones = spark.read.parquet('phones.parquet')
rels = spark.read.parquet('employment.parquet')

phone_features = phones.select(
    F.col('person_id'),
    F.struct(
        F.col('phone_number').alias('PHONE_NUMBER'),
        F.col('phone_type').alias('PHONE_TYPE')
    ).alias('feat')
).groupBy('person_id').agg(F.collect_list('feat').alias('phone_features'))

rel_features = rels.select(
    F.col('person_id'),
    F.struct(
        F.lit('HR').alias('REL_POINTER_DOMAIN'),
        F.col('org_id').cast('string').alias('REL_POINTER_KEY'),
        F.coalesce(F.col('role'), F.lit('EMPLOYED_BY')).alias('REL_POINTER_ROLE')
    ).alias('feat')
).groupBy('person_id').agg(F.collect_list('feat').alias('rel_pointers'))

df = persons.join(phone_features, 'person_id', 'left').join(rel_features, 'person_id', 'left')\
    .fillna({'phone_features': [], 'rel_pointers': []})

def build_features(first_name, last_name, dob, pid, phone_feats, rel_ptrs):
    feats = [
        {'RECORD_TYPE': 'PERSON'},
        {'NAME_FIRST': first_name, 'NAME_LAST': last_name},
        {'DATE_OF_BIRTH': dob},
        {'REL_ANCHOR_DOMAIN': 'HR', 'REL_ANCHOR_KEY': str(pid)}
    ]
    feats.extend(phone_feats or [])
    feats.extend(rel_ptrs or [])
    return feats

build_features_udf = F.udf(build_features, 'array<map<string,string>>')

out = df.withColumn('FEATURES', build_features_udf('first_name','last_name','dob','person_id','phone_features','rel_pointers'))\
         .withColumn('DATA_SOURCE', F.lit('PEOPLE'))\
         .withColumn('RECORD_ID', F.col('person_id').cast('string'))\
         .select('DATA_SOURCE','RECORD_ID','FEATURES')

out.write.mode('overwrite').json('senzing_json')
```
