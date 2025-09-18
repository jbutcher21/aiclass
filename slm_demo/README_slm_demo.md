# Small Language Model (SLM) Demo
#### Clair J. Sullivan, PhD
#### clair@clairsullivan.com
#### Last modified: 2025-09-18

This demo shows you how to work with a small language model (SLM) running in a Docker container on your local machine in order to create Senzing-ready JSON.

## 📋 Prerequisites

- Docker installed and running

## 🚀 Getting Started: Run Ollama with Docker

1. Pull the Ollama Docker image:
   ```bash
   docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama:latest
   ```

2. Pull an SLM model
    ```bash
    docker exec -it ollama ollama pull model_name
    ```
    Replace `model_name` with the name of the model you want to use.  You can choose any of the models from the [Ollama model list](https://ollama.com/models).  However, you will want to consider whether your local computer has a GPU or not.  If you do not have a GPU, you will want to choose a smaller model.  Also consider that larger models will require more RAM to run and take longer.  For this demo assuming your are just running on just a CPU, the following models are recommended:

    - `tinyllama`
    - `llama3.2:1b-instruct-q4_K_M`
    - `llama3.2:3b-instruct-q4_K_M`
    - `mistral:7b-instruct-q4_K_M`

3. Verify the model is installed:
    ```bash
    docker exec -it ollama ollama list
    ```

4. Test the model is successfully installed and running:
    ```bash
    curl -s http://localhost:11434/api/generate \
        -d '{
        "model": model_name,
        "prompt": "One-line summary of entity resolution. Keep it under 12 words.",
        "stream": false
        }' | jq -r .response
    ```

Assuming this above all runs correctly and the final step gives you a response from the SLM, you now have your SLM running as a REST API on your local machine.  We can now use this to start mapping data to Senzing JSON!

## 🤖 Using the SLM to Create Senzing JSON Mapping Code

There are many times when you will not want to use a large language model (LLM) like GPT-4 or Claude.  This might be because of cost, data privacy, or other reasons.  Additionally, some SLMs offer you the opportunity to fine-tune the model to your exact use case, which can lead to superior results.  In these cases, you can use a small language model (SLM) running on your local machine or deployed to a cloud instance.  However, SLMs are not as powerful as LLMs and require different prompting techniques to get good results.

There are a few things to keep in mind when creating prompts for SLMs versus LLMs:

- Be More Explicit and Structured
  - SLMs have less contextual understanding, so be very specific about what you want
  - Use clear, step-by-step instructions rather than relying on the model to infer
  - Structure your prompts with clear sections (task, context, format, etc.)

- Simplify Language and Concepts
  - Use simpler vocabulary and shorter sentences
  - Break complex tasks into smaller, discrete steps
  - Avoid idiomatic expressions or implicit references that require broad knowledge

- Provide More Context and Examples
  - Include relevant background information that an LLM might infer on its own
  - Give concrete examples of the input/output format you expect
  - Show the model exactly what good output looks like with 1-2 examples

- Focus on Single Tasks
  - SLMs struggle more with multi-step or complex reasoning
  - Ask for one specific thing at a time rather than combining multiple requests
  - Chain simpler prompts together rather than trying to do everything in one shot

- Use Templates and Patterns
  - Create consistent prompt templates for similar tasks
  - Use formatting like "Task:", "Context:", "Output format:" to help the model parse your request
  - Establish patterns the model can recognize and follow

- Be More Directive
  - Tell the model exactly what to do rather than asking open-ended questions
  - Use imperative language: "Generate X" rather than "Can you help me with X?"
  - Specify constraints clearly (length, format, style)

- Test and Iterate More
  - SLMs are less consistent, so test your prompts multiple times
  - Fine-tune your wording based on what produces the most reliable results
  - Keep successful prompt patterns for reuse

## 🎯 Your Task

Your task in this module is to create a prompt for the SLM that will take the employee demo data (`./employee_demo/data/us-small-employee-raw.csv`) and its associated schema (`./employee_demo/schema/us-small-employee-schema.txt`) and generate Python code that will map the CSV data to Senzing JSON.  You will begin with the code in `./slm_demo/slm_senzing_mapper.py`.  This code contains a class called `SLMSenzingMapper` that you can use to generate mapping code.  In this class, you will need to specifically pay attention to the `create_mapping_prompt` method.  This is where you will create the prompt that you will send to the SLM in order to generate the mapping code.  The code then uses `requests` to send the prompt to the SLM and get the generated code back.  

In order to run the code, use the following command:

```bash
python ./slm_demo/slm_senzing_mapper.py 
```

Be sure to edit the `model` variable in the `SLMSenzingMapper` class to match the model you installed in the previous section.  You can also change the `csv_file` and `schema_file` variables to point to different CSV files and schemas if you want to test with different data.  The output will be a Python script called `generated_mapper.py` that contains the mapping code.  

**Note that this can take several minutes to run, depending on your computer hardware and which model you are using.**

There is some brief unit testing provided in `slm_senzing_mapper.py` to inform you whether the code you generated is viable.  Once those tests successfully pass, you can then run this script to generate Senzing JSON from the CSV data using:

```bash
python generated_mapper.py ./employee_demo/data/us-small-employee-raw.csv ./output.jsonl
```

Assuming this all runs successfully, you will be able to confirm that that the output JSON is valid Senzing JSON by running it through the Senzing JSON analyzer:

```bash
./tools/sz_json_analyzer.py -i ./output.jsonl 
```

## 📝 Notes

Any time you are creating things with LLMs or SLMs, the process is pretty iterative, particularly when you are doing prompt engineering.  Be patient and have fun!  
