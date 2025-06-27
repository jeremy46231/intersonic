from pathlib import Path
from lyrics import process_lyrics

def process_metadata(mp3_path: Path):
    """
    Process metadata for the given MP3 file.
    """
    # Clean lyrics
    process_lyrics(mp3_path)
