"""Extract searchable text and descriptions from image files."""

import base64
import mimetypes
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# Load settings from the project's .env file.
load_dotenv()


def extract_image(path: Path) -> list[str]:
    """Ask Groq to describe an image and return the result as one text section."""
    image_path = Path(path)

    # Groq's vision request has a 20 MB image limit.
    if image_path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("Image must be 20 MB or smaller.")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing from the project's .env file.")

    # Convert the local image bytes into the data URL format Groq accepts.
    mime_type, _ = mimetypes.guess_type(image_path.name)
    if mime_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise ValueError("Supported image types are PNG, JPG/JPEG, and WEBP.")

    encoded_image = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    image_data_url = f"data:{mime_type};base64,{encoded_image}"

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Describe this image for a study assistant. "
                            "Transcribe all readable text, explain diagrams, "
                            "and include important labels, facts, and relationships. "
                            "Use clear plain text."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url},
                    },
                ],
            }
        ],
        max_completion_tokens=512,
    )

    description = response.choices[0].message.content
    if not description or not description.strip():
        raise ValueError("Groq returned an empty image description.")

    # Match the list-of-text-sections format used by the other extractors.
    return [description.strip()]
