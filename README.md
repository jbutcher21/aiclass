# AI-Class: Senzing Mapping Assistant

This repository contains an AI-ready Senzing Entity Specification and a production-ready system prompt to guide mapping of source schemata to valid Senzing JSON. It also includes a JSON linter and identifier crosswalk to standardize mappings.

## What’s Inside
- `docs/system_prompt-chatgpt.md`: system prompt to load into your AI assistant.
- `docs/senzing_entity_spec.md`: authoritative, AI-ready Senzing Entity Spec (this repo is the source of truth).
- `docs/lint_senzing_json.py`: linter to validate Senzing JSON/JSONL output.
- `docs/identifier_crosswalk.json`: canonical identifier types, aliases, and mapping guidance.
- `docs/identifier_lookup_log.md`: template to record curated identifier lookups (no PII).

### Employee Demo (use for testing)
- Path: `projects/ai-work/employees-chatgpt/`
- Contents:
  - `data/us-small-employee-raw.csv`: sample input data
  - `schema/us-small-employee-schema.csv`: inferred schema
  - `scripts/transform_employees.py`: hand-written transformer (reference)
  - `examples/person_example.json`, `examples/employer_example.json`: example records
  - `output/employees.jsonl`, `output/employers.jsonl`: expected Senzing JSONL
  - `docs/us-small-employee-mapping.md`: mapping write-up
- How to use:
  - Inspect schema, run the transformer, then compare your mapping results to `output/*.jsonl`.
  - Validate with the linter: `python3 docs/lint_senzing_json.py < projects/ai-work/employees-chatgpt/output/employees.jsonl`

Sample commands:
- Profile the CSV (derive schema and stats):
  - `python3 github/sz-file-analyzer/sz-file-analyzer.py -i projects/ai-work/employees-chatgpt/data/us-small-employee-raw.csv -o /tmp/employee_profile.csv`
- Generate Senzing JSONL from the demo CSV:
  - `python3 projects/ai-work/employees-chatgpt/scripts/transform_employees.py --input projects/ai-work/employees-chatgpt/data/us-small-employee-raw.csv --outdir projects/ai-work/employees-chatgpt/output`
- Lint the outputs:
  - `python3 docs/lint_senzing_json.py < projects/ai-work/employees-chatgpt/output/employees.jsonl`
  - `python3 docs/lint_senzing_json.py < projects/ai-work/employees-chatgpt/output/employers.jsonl`
- Analyze mapped JSONL (mapped/unmapped, warnings, errors):
  - `python3 github/sz-json-analyzer/sz_json_analyzer.py -i projects/ai-work/employees-chatgpt/output/employees.jsonl -o /tmp/employees_report.csv`
  - `python3 github/sz-json-analyzer/sz_json_analyzer.py -i projects/ai-work/employees-chatgpt/output/employers.jsonl -o /tmp/employers_report.csv`

### Tools
- File Analyzer (profile files to derive schema and stats):
  - Path: `github/sz-file-analyzer/`
  - Script: `sz-file-analyzer.py`
  - Purpose: analyze CSV/JSON/Parquet when a schema doesn’t exist; shows attribute name, inferred type, population %, uniqueness %, and top values.
  - Also includes `sz_json_analyzer.py` and `sz_default_config.json` in the same folder for convenience.
- Senzing JSON Analyzer (validate mapped JSONL before loading):
  - Path: `github/sz-json-analyzer/`
  - Script: `sz_json_analyzer.py`
  - Purpose: validates/inspects Senzing JSON/JSONL; highlights mapped vs unmapped attributes, uniqueness/population, warnings, and errors.

Data Handling Guidance
- Do not upload full datasets to an AI. Share schema extracts, field lists, small samples, or analyzer summaries instead.
- Use the File Analyzer to produce schema/stats, then provide that summary to the assistant during mapping.

## Quick Start (Use with your AI of choice)
1) Load the system prompt
   - Option A: Paste the contents of `docs/system_prompt-chatgpt.md` into the AI’s “system” message.
   - Option B: Provide the raw URL and ask the AI to fetch it (if supported):
     - System Prompt (raw): https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/system_prompt-chatgpt.md
2) Supply your source schema as context
   - Describe tables/files, fields, keys, arrays/sub-docs, and any relationship/link tables.
3) Kick off mapping
   - Say: “Begin mapping.”
   - Answer the assistant’s numbered questions and approve decisions as prompted.
4) Validate outputs
   - Use the linter to validate any JSON/JSONL examples and final outputs:
     - Local file: `python3 docs/lint_senzing_json.py < path/to/output.jsonl`
     - Raw URL (for remote use): https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/lint_senzing_json.py

## Important Links (Raw)
- System Prompt: https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/system_prompt-chatgpt.md
- Senzing Entity Spec: https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/senzing_entity_spec.md
- Linter: https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/lint_senzing_json.py
- Identifier Crosswalk: https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/identifier_crosswalk.json

Note: When working inside this repository or forks, prefer relative links so everything works offline.

## Workflow Highlights
- One record per entity: join/aggregate child features and disclosed relationships into the master before output.
- Relationship rules: add `REL_ANCHOR` to any relatable PERSON/ORGANIZATION; place `REL_POINTER` on the source of the relationship pointing to the target’s anchor with a clear `REL_POINTER_ROLE` (e.g., `EMPLOYED_BY`, `SPOUSE_OF`, `SUBSIDIARY_OF`).
- Validation: all examples and final outputs should pass the linter.
- Curated identifier lookups: use authoritative sources only; no PII; add results to the crosswalk.

## Notes
- Treat `docs/senzing_entity_spec.md` in this repository as the single source of truth. Do not substitute external specs unless you intentionally update it here.
