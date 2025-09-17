# Bootstrap Instructions for Mapping Sessions (v2.20)

Use my system prompt and the Senzing spec from these URLs:

- **System Prompt (rules/workflow):**  
  https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/mapping_instructions.md  

- **Senzing Entity Specification (single source of truth):**  
  https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/senzing_entity_specification.md  

---

## How to Use

1. **Load the system prompt** and treat it as the governing rules for the session.  
   - The assistant must always follow the rules inside the prompt and the linked spec.  
   - No alternate docs are allowed.

2. **Step 0 → Provide schema or sample records.**  
   - Upload either a schema file (JSON/YAML/CSV describing structure) or example records.  
   - You can provide one or both.

3. **Step 1 → Source Summary (follows spec’s *Source Schema Types*).**  
   - Assistant applies the spec’s checklist:
     - Flat table / Multi-table / Nested objects / Arrays / Mixed entity types / Relationship tables / Embedded entities.  
   - Enumerates **all entities and relationships** it detects, with keys, join paths, and evidence.  
   - Explicitly calls out **embedded entities** (e.g., an employer nested inside an employee record).  
   - Ends with a **hard stop**: “Ready to begin mapping?”  

4. **Step 2 → Interactive Draft Mapping.**  
   - Entity by entity.  
   - Confirm `DATA_SOURCE` and `RECORD_ID` first (with a JSON skeleton).  
   - Then feature-by-feature mini tables + spec-true JSON snippets.  
   - Per-feature **hard stops** (`approve` / `adjust:`).  
   - Includes payload-at-root confirmation and ignored-field confirmation.  
   - Every source field must be dispositioned exactly once.

5. **Step 3 → Finalized Mapping + Sample JSONs.**  
   - Full mapping table.  
   - Pretty-printed example JSON(s).  
   - Must validate against the spec’s **Recommended JSON Structure** (payload at root, FEATURES array, RECORD_TYPE inside features).  
   - Hard stop until approved.

6. **Step 4 → Python Mapping Script.**  
   - Assistant generates a Python script that implements the finalized mapping.  
   - You test it on your data; assistant iterates changes until approval.  
   - Hard stop until approved.

7. **Step 5 → Wrap-Up.**  
   - Assistant confirms completion and offers to start the next source system.

---

## Key Enforcement
- **Source Field Inventory**: assistant must echo the exact source field list and use only those fields.  
- **Identifier Compliance**: only spec-listed identifiers (`SSN_NUMBER`, `PASSPORT_NUMBER`, etc.). No generic “IDENTIFIER.”  
- **Recommended JSON Structure**: enforced at every snippet/sample. No `PAYLOAD` wrapper.  
- **No TRUSTED_ID** unless you explicitly ask.  
- **No fabricated fields**.  
- **Per-feature confirmation gates** before proceeding.
