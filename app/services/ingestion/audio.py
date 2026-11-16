"""Transcribe audio files into searchable text."""

import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# Load the project's environment settings, including GROQ_API_KEY.
load_dotenv()


def extract_audio(path: Path) -> list[str]:
    """Transcribe an audio file and return its transcript as one text section."""
    audio_path = Path(path)

    # Keep uploads within Groq's 25 MB free-tier file limit.
    if audio_path.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("Audio must be 25 MB or smaller.")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing from the project's .env file.")

    client = Groq(api_key=api_key)

    # Whisper detects the spoken language automatically.
    with audio_path.open("rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",
            response_format="json",
            temperature=0.0,
        )

    transcript = transcription.text.strip()
    if not transcript:
        raise ValueError("Groq returned an empty transcript.")

    return [transcript]
