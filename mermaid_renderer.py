import subprocess
import os
import logging
import tempfile

# Set up logging
logger = logging.getLogger(__name__)

def render_mermaid_to_image_local(mermaid_syntax: str) -> bytes:
    """
    Renders the Mermaid syntax to a PNG image using the local 'mmdc' (Mermaid CLI) tool.

    This function requires Node.js and the @mermaid-js/mermaid-cli package to be
    installed and available in the execution environment's PATH.
    """
    logger.info("Starting local Mermaid rendering with mmdc.")

    # Use temporary files for input and output
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.mmd') as input_file:
        input_file.write(mermaid_syntax)
        input_path = input_file.name

    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as output_file:
        output_path = output_file.name

    try:
        # The mmdc command to execute
        # -i: input file
        # -o: output file
        # -t: theme (optional, default is 'default')
        command = [
            "mmdc",
            "-i", input_path,
            "-o", output_path,
            "-t", "neutral", # Use a neutral theme for better contrast
            "--width", "1024",
            "--height", "768"
        ]

        logger.info(f"Executing command: {' '.join(command)}")

        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        logger.info(f"mmdc stdout: {result.stdout}")
        logger.info(f"mmdc stderr: {result.stderr}")

        # Read the generated PNG image bytes
        with open(output_path, 'rb') as f:
            image_bytes = f.read()

        logger.info(f"Successfully generated image of size: {len(image_bytes)} bytes")
        return image_bytes

    except subprocess.CalledProcessError as e:
        logger.error(f"mmdc rendering failed with error code {e.returncode}.")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise RuntimeError(f"Mermaid CLI rendering failed. Stderr: {e.stderr}") from e
    except FileNotFoundError:
        logger.error("mmdc command not found. Is @mermaid-js/mermaid-cli installed and in PATH?")
        raise RuntimeError("Mermaid CLI (mmdc) not found. Please ensure it is installed.")
    finally:
        # Clean up temporary files
        os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
