import logging
import json
import os
import base64
from openai import OpenAI
import azure.functions as func

# Import the local renderer
from ..mermaid_renderer import render_mermaid_to_image_local

# --- Configuration ---
# NOTE: The OpenAI client will automatically pick up the OPENAI_API_KEY
# and OPENAI_API_BASE from the local.settings.json or Azure Function App settings.
# For Azure OpenAI, the API key is typically the 'key' and the base is the 'endpoint'.
# The client must be configured to use the Azure OpenAI API version.
# The model name here should be the deployment name on Azure OpenAI.
AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-mini")

def get_mermaid_syntax(prompt: str) -> str:
    """
    Uses Azure OpenAI to convert a natural language prompt into Mermaid syntax.
    """
    logging.info(f"Sending prompt to OpenAI: {prompt}")

    # The client will automatically use the configured environment variables
    # (OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, OPENAI_API_VERSION)
    # from local.settings.json or Function App settings.
    try:
        # The base_url and default_headers are necessary for Azure OpenAI compatibility
        # when using the standard 'openai' Python library.
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            default_headers={"api-key": os.environ.get("OPENAI_API_KEY")},
        )
    except Exception as e:
        logging.error(f"Error initializing OpenAI client: {e}")
        raise

    # System prompt to guide the model to output only Mermaid syntax
    system_prompt = (
        "You are an expert diagram generator. Your task is to convert a user's natural "
        "language description into a valid Mermaid diagram definition. "
        "The output MUST contain ONLY the Mermaid syntax block, enclosed in a 'mermaid' "
        "code fence (```mermaid...```), and nothing else. "
        "Focus on creating a 'flowchart' (graph) unless another type is explicitly requested. "
        "Example: '```mermaid\\ngraph TD\\n    A[Start] --> B(Process)\\n```'"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.1,
            max_tokens=1024
        )

        mermaid_block = response.choices[0].message.content.strip()

        # Extract content between the ```mermaid and ``` fences
        start_tag = "```mermaid"
        end_tag = "```"
        if start_tag in mermaid_block and end_tag in mermaid_block:
            mermaid_syntax = mermaid_block.split(start_tag, 1)[1].split(end_tag, 1)[0].strip()
        else:
            # If the model didn't use the code fence, assume the whole output is the syntax
            mermaid_syntax = mermaid_block

        return mermaid_syntax

    except Exception as e:
        logging.error(f"OpenAI API call failed: {e}")
        # In a real application, you might want to return a default error diagram
        raise

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # 1. Get the prompt from the request body
        req_body = req.get_json()
        prompt = req_body.get('prompt')
    except ValueError:
        # If not JSON, try to get it from query parameters
        prompt = req.params.get('prompt')

    if not prompt:
        try:
            # Try to get prompt from form data if it's not in JSON or query params
            req_body = req.get_body()
            if req_body:
                # Assuming simple form data or plain text body
                prompt = req_body.decode('utf-8')
        except Exception:
            pass

    if not prompt:
        # If no prompt is provided, return a 400 error
        return func.HttpResponse(
             "Please pass a 'prompt' in the request body (JSON or form data) or as a query parameter.",
             status_code=400
        )

    try:
        # 2. Convert prompt to Mermaid syntax using Azure OpenAI
        mermaid_syntax = get_mermaid_syntax(prompt)
        logging.info(f"Generated Mermaid Syntax: {mermaid_syntax}")

        # 3. Render Mermaid syntax to PNG image using the local renderer
        # This is the key change to ensure privacy/security.
        image_bytes = render_mermaid_to_image_local(mermaid_syntax)
        logging.info(f"Successfully generated image of size: {len(image_bytes)} bytes")

        # 4. Return the image as the HTTP response
        return func.HttpResponse(
            body=image_bytes,
            mimetype="image/png",
            status_code=200
        )

    except Exception as e:
        # Catch all exceptions and return a generic error response
        logging.error(f"An error occurred during processing: {e}")
        return func.HttpResponse(
             f"An error occurred: {str(e)}",
             status_code=500
        )
