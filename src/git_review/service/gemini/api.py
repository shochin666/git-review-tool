import os

from dotenv import load_dotenv
from google import genai
from jinja2 import Environment, FileSystemLoader


def get_gemini_response(prompt: str) -> str:
    """
    Generate content using Gemini API.

    Args:
        prompt (str): The input prompt for content generation.

    Returns:
        str: The generated content from Gemini API.
    """

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(model=model, contents=prompt)
    return response.text
