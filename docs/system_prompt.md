# Bootstrap Instructions for Mapping Sessions

Use my system prompt and linter from these URLs:

- **System Prompt (rules/workflow):**  
  https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/mapping_instructions.md

- **Linter (authoritative validator, optional run):**  
  https://raw.githubusercontent.com/jbutcher21/aiclass/main/tools/lint_senzing_json.py

Instructions:
1. Load the system prompt and treat it as the governing rules for this session.  
2. Always follow the spec rules linked inside that prompt.  
3. Use the linter at the given URL as the authoritative reference.  
   - If I upload the linter file here, you should actually run it on any Preview JSON:  
     ```bash
     python3 tools/lint_senzing_json.py preview.jsonl
     ```  
   - If not uploaded, just reason from the linter’s code at the URL, and ask me to run it locally if needed.  
4. Summarize the mapping instructions work flow and wait for schema or data file to be uploaded.
