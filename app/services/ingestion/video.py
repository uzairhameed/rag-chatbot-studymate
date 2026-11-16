"""Extract speech from video files."""

from pathlib import Path
from tempfile import TemporaryDirectory

from moviepy import VideoFileClip

from app.services.ingestion.audio import extract_audio


def extract_video(path: Path) -> list[str]:
    """Extract a video's audio track, transcribe it, and return the transcript."""
    video_path = Path(path)

    # Keep the temporary audio outside the project and clean it up afterward.
    with TemporaryDirectory(prefix="studymate-video-") as temp_dir:
        audio_path = Path(temp_dir) / "extracted_audio.mp3"

        # Close the video file before sending its extracted audio for transcription.
        with VideoFileClip(str(video_path)) as video:
            if video.audio is None:
                raise ValueError("This video does not contain an audio track.")

            video.audio.write_audiofile(
                str(audio_path),
                fps=16000,
                codec="libmp3lame",
                bitrate="64k",
                logger=None,
            )

        # Reuse the tested audio extractor so video speech follows the same path.
        return extract_audio(audio_path)
