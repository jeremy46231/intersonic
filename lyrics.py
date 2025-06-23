#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "mutagen",
# ]
# ///

import re
from pathlib import Path
from typing import Optional, List, Tuple
from mutagen.id3 import ID3, USLT, SYLT, Encoding  # type: ignore
import argparse

parser = argparse.ArgumentParser('./lyrics.py', description="Clean and sync .lrc files with ID3 tags.")
parser.add_argument("target_dir", help="Directory containing mp3 files.")
parser.add_argument("--lrc", choices=["write", "leave", "delete"], default="write", help="What to do with .lrc files")
parser.add_argument("--embed", choices=["write", "leave", "delete"], default="write", help="What to do with embedded ID3 lyrics")
parser.add_argument("--remove-lyrics", action="store_true", help="Remove embedded lyrics if no .lrc file")
parser.add_argument("--keep-credits", action="store_true", help="Don't remove '作词 :' and '作曲 :' lines from the lyrics")
args = parser.parse_args()

# === Configuration Options ===
TARGET_DIR = args.target_dir
# Options: "write", "leave", "delete"
LRC_FILE = args.lrc  # operate on .lrc file
EMBED_LYRICS = args.embed  # operate on embedded lyrics
REMOVE_LYRICS_IF_NO_LRC = args.remove_lyrics  # remove embedded lyrics if no .lrc file
CLEAN_LRC_CREDITS = not args.keep_credits  # remove '作词 :' and '作曲 :' lines from .lrc

# print(f"Target directory: {TARGET_DIR}")
# print(f"LRC file action: {LRC_FILE}")
# print(f"Embedded lyrics action: {EMBED_LYRICS}")
# print(f"Remove lyrics if no .lrc: {REMOVE_LYRICS_IF_NO_LRC}")
# print(f"Keep '作词 :' and '作曲 :' lines: {CLEAN_LRC_CREDITS}")
# exit()

# Regex for LRC timestamps e.g. [01:23.45] or [01:23.456]
LRC_REGEX = re.compile(r"\[(\d{2}):(\d{2})\.(\d{2,3})\]")

# --- Intermediate lyrics type ---
LyricLine = Tuple[Optional[int], str]  # (ms, text)

# --- Helpers ---


def to_ms(min_str: str, sec_str: str, ms_str: str) -> int:
    # Ensure ms is 3 digits (pad with zeros if needed)
    ms_str = ms_str.ljust(3, "0")
    return int(min_str) * 60000 + int(sec_str) * 1000 + int(ms_str)


def parse_lyrics(text: str) -> List[LyricLine]:
    """Parse raw lyrics text into list of (timestamp in ms or None, text)."""
    lines: List[LyricLine] = []
    for line in text.splitlines():
        line = line.rstrip()
        if line.startswith("[") and "]" in line:
            # Attempt to extract timestamp from the beginning.
            try:
                time_part, rest = line.split("]", 1)
                m = LRC_REGEX.match(time_part + "]")
                if m:
                    ms = to_ms(m.group(1), m.group(2), m.group(3))
                    lines.append((ms, rest.lstrip()))
                    continue
            except Exception:
                pass
        # Unsynced or unformatted line.
        lines.append((None, line.strip()))
    return lines


def serialize_to_lrc(lyrics: List[LyricLine]) -> str:
    """Serialize lyrics into LRC formatted text using first timestamp if present."""
    result = []
    for ts, text in lyrics:
        if ts is not None:
            minutes = ts // 60000
            seconds = (ts % 60000) / 1000
            # Format: [mm:ss.xx]
            timestamp = f"[{minutes:02d}:{seconds:05.2f}]"
            result.append(f"{timestamp} {text}")
        else:
            result.append(text)
    return "\n".join(result)


def serialize_to_id3(lyrics: List[LyricLine]) -> str:
    """Serialize lyrics into plain text suitable for ID3 (timestamps removed)."""
    return "\n".join(text for _, text in lyrics)


def clean_lyrics_intermediate(lyrics: List[LyricLine]) -> List[LyricLine]:
    """Trim each lyric line and remove credit lines if enabled.
    Credit lines are those where text starts with '作词 :' or '作曲 :'.
    """
    cleaned: List[LyricLine] = []
    for ts, text in lyrics:
        txt = text.strip()
        if CLEAN_LRC_CREDITS and (txt.startswith("作词 :") or txt.startswith("作曲 :")):
            continue
        
        cleaned.append((ts, txt))
    return cleaned


def parse_id3_lyrics(mp3_path: Path) -> Optional[List[LyricLine]]:
    """Parse lyrics from ID3 tags into the intermediate format.
    Prioritize SYLT (synced) then USLT (unsynced).
    """
    try:
        tags = ID3(mp3_path)
        # SYLT: synced lyrics, might be list of (text, ms) pairs.
        sylt_tags = tags.getall("SYLT")
        if sylt_tags:
            lines: List[LyricLine] = []
            for tag in sylt_tags:
                if isinstance(tag.text, list):
                    lines.extend([(ms, text.strip()) for text, ms in tag.text])
                else:
                    lines.append((None, tag.text.strip()))
            if lines:
                return lines
        # USLT: unsynced lyrics (plain text)
        uslt_tags = tags.getall("USLT")
        if uslt_tags:
            text = "\n".join(tag.text for tag in uslt_tags if tag.text)
            return parse_lyrics(text)
    except Exception:
        pass
    return None


def embed_lyrics_to_mp3(mp3_path: Path, lyrics: List[LyricLine]):
    try:
        tags = ID3(mp3_path)
    except Exception:
        tags = ID3()  # Create new ID3 tag

    # Determine if any synced entries exist.
    has_synced = any(ts is not None for ts, _ in lyrics)
    unsynced_text = serialize_to_id3(lyrics)
    tags.delall("USLT")
    tags.delall("SYLT")
    tags.add(USLT(encoding=Encoding.UTF8, text=unsynced_text))
    if has_synced:
        # For SYLT, embed only those with a defined timestamp.
        sync_data = [(text, ts) for ts, text in lyrics if ts is not None]
        if sync_data:
            tags.add(SYLT(encoding=Encoding.UTF8, text=sync_data, format=2, type=1))
    tags.save(mp3_path)
    print(f"Embedded lyrics into {mp3_path}")


def remove_embedded_lyrics(mp3_path: Path):
    try:
        tags = ID3(mp3_path)
        tags.delall("USLT")
        tags.delall("SYLT")
        tags.save(mp3_path)
        print(f"Removed embedded lyrics from {mp3_path}")
    except Exception as e:
        print(f"Error removing lyrics from {mp3_path}: {e}")


# --- Main ---


def main():
    base = Path(TARGET_DIR)
    if not base.exists():
        print(f"Target directory {TARGET_DIR} does not exist.")
        raise SystemExit(1)
    # Get all mp3 files.
    mp3_files = list(base.rglob("*.mp3"))
    total_files = len(mp3_files)
    print(f"Found {total_files} mp3 file(s) in {TARGET_DIR}")

    for idx, mp3_file in enumerate(mp3_files):
        print(f"Processing file {idx+1}/{total_files}: {mp3_file.name}")
        lrc_path = mp3_file.with_suffix(".lrc")
        raw_lyrics: Optional[List[LyricLine]] = None

        # Priority: .lrc file if exists.
        if lrc_path.exists():
            raw_text = lrc_path.read_text(encoding="utf-8")
            raw_lyrics = parse_lyrics(raw_text)
        else:
            # Fallback: parse lyrics from ID3
            raw_lyrics = parse_id3_lyrics(mp3_file)

        if raw_lyrics:
            # Apply cleaning.
            intermediate = clean_lyrics_intermediate(raw_lyrics)

            # Handle .lrc file based on option.
            if LRC_FILE == "write":
                lrc_path.write_text(serialize_to_lrc(intermediate), encoding="utf-8")
            elif LRC_FILE == "delete":
                if lrc_path.exists():
                    lrc_path.unlink()
                    print(f"Deleted {lrc_path}")
            # "leave" means do nothing to .lrc file.

            # Handle ID3 embedding.
            if EMBED_LYRICS == "write":
                embed_lyrics_to_mp3(mp3_file, intermediate)
            elif EMBED_LYRICS == "delete":
                remove_embedded_lyrics(mp3_file)
            # "leave" means do nothing.
        else:
            if REMOVE_LYRICS_IF_NO_LRC:
                remove_embedded_lyrics(mp3_file)


if __name__ == "__main__":
    main()
