# src/metadata/tags.py
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from mutagen.id3 import ID3
from mutagen.id3._frames import (
    COMM,
    POPM,
    TALB,
    TCOP,
    TCON,
    TDRC,
    TENC,
    TIT2,
    TPE1,
    TPE2,
    TPOS,
    TRCK,
    TSRC,
    TSSE,
    WOAS,
    TextFrame,
)

# Regex to find Spotify or YouTube Music URLs
URL_REGEX = re.compile(r"(https?://(?:open\.spotify\.com|music\.youtube\.com)/[^\s]+)")

# A set of tags handled by dedicated modules (lyrics, album art)
MANAGED_EXTERNALLY = {"APIC", "USLT", "SYLT"}

# A set of tags explicitly managed by this module in the Tags dataclass
MANAGED_INTERNALLY = {
    "TIT2",
    "TPE1",
    "TALB",
    "TPE2",
    "TRCK",
    "TPOS",
    "TDRC",
    "TCOP",
    "TCON",
    "TSRC",
    "TENC",
    "TSSE",
    "WOAS",
    "COMM",
    "POPM",
}


@dataclass
class Tags:
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    track: Optional[str] = None
    disc: Optional[str] = None
    recording_date: Optional[str] = None
    copyright: Optional[str] = None
    genre: Optional[str] = None
    isrc: Optional[str] = None
    encoder: Optional[str] = None
    encoder_settings: Optional[str] = None
    popularity: Optional[int] = None
    comment: Optional[str] = None

    spotify_url: Optional[str] = None
    youtube_url: Optional[str] = None

    other_tags: Dict[str, Any] = field(default_factory=dict, repr=False)


def tags_to_json(tags_data: Tags) -> str:
    """Converts a Tags object into a JSON string."""
    dict = asdict(tags_data)
    # Exclude 'other_tags' as it contains non-serializable mutagen objects.
    # The canonical source for these remains the MP3 file itself.
    del dict["other_tags"]
    # Remove any None values to keep the JSON clean
    dict = {k: v for k, v in dict.items() if v is not None}
    return json.dumps(dict, indent=2) + "\n"


def json_to_tags(data: str) -> Tags:
    """Converts JSON into a Tags object."""
    try:
        dict = json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON data: {e}") from e
    return Tags(**dict)


def get_text_frame(tags: ID3, key: str) -> Optional[str]:
    """Extracts text from a standard text frame."""
    frame: TextFrame | None = tags.get(key)
    return str(frame) if frame else None


def parse_id3_tags(mp3_path: Path) -> Optional[Tags]:
    """Parses ID3 tags from an MP3 into a structured Tags object."""
    try:
        id3 = ID3(mp3_path)
    except Exception as e:
        print(f"Failed to read ID3 tags from {mp3_path}: {e}")
        return None

    spotify_url, youtube_url = None, None
    comment: str | None = None

    # Handle WOAS for URLs
    woas_frame = id3.get("WOAS")
    if woas_frame and "open.spotify.com" in woas_frame.url:
        spotify_url = woas_frame.url
    elif woas_frame and "music.youtube.com" in woas_frame.url:
        youtube_url = woas_frame.url

    # Handle COMM for URLs and comments
    for frame in id3.getall("COMM"):
        text = frame.text[0] if frame.text else ""
        found_urls = URL_REGEX.findall(text)
        for url in found_urls:
            if "open.spotify.com" in url:
                spotify_url = url
            elif "music.youtube.com" in url:
                youtube_url = url

        # Remove URLs and clean up the remaining comment text
        comment_text = URL_REGEX.sub("", text).strip()
        if comment_text:
            if comment is None:
                comment = comment_text
            else:
                comment += f"\n{comment_text}"

    # Extract popularity from POPM frame if it exists
    popm = id3.get("POPM")
    popularity = int(popm.rating) if popm else None  # type: ignore

    # Gather all other tags that aren't managed elsewhere
    other_tags = {
        key: frame
        for key, frame in id3.items()
        if key[:4] not in MANAGED_EXTERNALLY and key[:4] not in MANAGED_INTERNALLY
    }

    return Tags(
        title=get_text_frame(id3, "TIT2"),
        artist=get_text_frame(id3, "TPE1"),
        album=get_text_frame(id3, "TALB"),
        album_artist=get_text_frame(id3, "TPE2"),
        track=get_text_frame(id3, "TRCK"),
        disc=get_text_frame(id3, "TPOS"),
        recording_date=get_text_frame(id3, "TDRC"),
        copyright=get_text_frame(id3, "TCOP"),
        genre=get_text_frame(id3, "TCON"),
        isrc=get_text_frame(id3, "TSRC"),
        encoder=get_text_frame(id3, "TENC"),
        encoder_settings=get_text_frame(id3, "TSSE"),
        popularity=popularity,
        comment=comment,
        spotify_url=spotify_url,
        youtube_url=youtube_url,
        other_tags=other_tags,
    )


def embed_tags(mp3_path: Path, tags_data: Tags):
    """Writes tags from a Tags object into an MP3 file."""
    try:
        id3 = ID3(mp3_path)
    except Exception:
        id3 = ID3()

    # Clear all existing tags managed by this module
    keys_to_delete = [k for k in id3.keys() if k[:4] in MANAGED_INTERNALLY]
    print(f"Clearing existing tags: {keys_to_delete}")
    for key in keys_to_delete:
        id3.delall(key)
    print(f"Remaining tags after clearing: {id3.keys()}")

    # Add tags from our structured data
    if tags_data.title:
        id3.add(TIT2(encoding=3, text=tags_data.title))
    if tags_data.artist:
        id3.add(TPE1(encoding=3, text=tags_data.artist))
    if tags_data.album:
        id3.add(TALB(encoding=3, text=tags_data.album))
    if tags_data.album_artist:
        id3.add(TPE2(encoding=3, text=tags_data.album_artist))
    if tags_data.track:
        id3.add(TRCK(encoding=3, text=tags_data.track))
    if tags_data.disc:
        id3.add(TPOS(encoding=3, text=tags_data.disc))
    if tags_data.recording_date:
        id3.add(TDRC(encoding=3, text=tags_data.recording_date))
    if tags_data.copyright:
        id3.add(TCOP(encoding=3, text=tags_data.copyright))
    if tags_data.genre:
        id3.add(TCON(encoding=3, text=tags_data.genre))
    if tags_data.isrc:
        id3.add(TSRC(encoding=3, text=tags_data.isrc))
    if tags_data.encoder:
        id3.add(TENC(encoding=3, text=tags_data.encoder))
    if tags_data.encoder_settings:
        id3.add(TSSE(encoding=3, text=tags_data.encoder_settings))
    if tags_data.popularity is not None:
        id3.add(POPM(email="None", rating=tags_data.popularity))

    # Set WOAS, preferring Spotify URL
    if tags_data.spotify_url:
        id3.add(WOAS(url=tags_data.spotify_url))
    elif tags_data.youtube_url:
        id3.add(WOAS(url=tags_data.youtube_url))

    # Set COMM, combining comment and URLs
    comm_text = tags_data.comment or ""
    if tags_data.spotify_url:
        comm_text += f"\n{tags_data.spotify_url}"
    if tags_data.youtube_url:
        comm_text += f"\n{tags_data.youtube_url}"
    if comm_text.strip():
        id3.add(COMM(encoding=3, lang="eng", desc="", text=comm_text.strip()))

    # Add back all other preserved tags
    for frame in tags_data.other_tags.values():
        id3.add(frame)
        print(f"Preserved tag: {frame}")

    try:
        id3.save(mp3_path)
    except Exception as e:
        raise RuntimeError(f"Failed to save ID3 tags to {mp3_path}: {e}") from e


def process_tags(mp3_path: Path):
    """
    Orchestrates tag processing for an MP3 file. It prioritizes a .json
    sidecar file for reading, then writes the final tags back to both the
    .json file and the MP3's ID3 tags for synchronization.
    """
    json_path = mp3_path.with_suffix(".json")
    tags_data: Optional[Tags] = None

    if json_path.exists():
        # Priority 1: .json file if it exists
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                json_content = f.read()
            tags_data = json_to_tags(json_content)
            # Make sure to load 'other_tags' from the mp3, as they aren't in the json
            id3_tags = parse_id3_tags(mp3_path)
            if tags_data and id3_tags:
                tags_data.other_tags = id3_tags.other_tags
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON data in {json_path}: {e}") from e
    else:
        # Priority 2: Parse directly from MP3 ID3 tags
        tags_data = parse_id3_tags(mp3_path)

    # In the future, cleaning/modification logic could go here.
    if tags_data:
        # Write to MP3 ID3 tags
        embed_tags(mp3_path, tags_data)

        # Write to .json file
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(tags_to_json(tags_data))
                print(f"Updated tags in {json_path}")
                print(f"Tags: {tags_to_json(tags_data)}")
        except Exception as e:
            raise RuntimeError(f"Failed to write tags to {json_path}: {e}") from e

        print(f"Processed and synced tags for {mp3_path.name}")
    else:
        print(f"Could not parse any tags for {mp3_path.name}, skipping")
