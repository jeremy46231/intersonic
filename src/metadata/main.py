from pathlib import Path
from metadata.tags import process_tags
from metadata.lyrics import process_lyrics
from metadata.album_art import process_album_art

def process_file(mp3_path: Path):
    """
    Process metadata for the given MP3 file.
    """
    process_tags(mp3_path)
    process_lyrics(mp3_path)
    process_album_art(mp3_path)

def process_directory(directory: Path):
    """
    Process all MP3 files in the given directory.
    """
    for mp3_file in directory.rglob("*.mp3"):
        process_file(mp3_file)
