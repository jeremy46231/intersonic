import re
from pathlib import Path
from typing import Optional, List
from mutagen.id3 import ID3
from mutagen.id3._frames import USLT, SYLT
from mutagen.id3._specs import Encoding

from utils import LyricLine, to_ms

LRC_REGEX = re.compile(r"\[(\d{2}):(\d{2})\.(\d{2,3})\]")


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
    return "\n".join(result) + "\n"


def serialize_to_plain(lyrics: List[LyricLine]) -> str:
    """Serialize lyrics into plain text suitable for ID3 (timestamps removed)."""
    return "\n".join(text for _, text in lyrics)


def clean_lyrics(lyrics: List[LyricLine]) -> List[LyricLine]:
    """Trim each lyric and remove credits.
    Credit lines are those at the top which contain " : ".
    """
    cleaned: List[LyricLine] = []
    skipping_credits = True

    for ts, text in lyrics:
        txt = text.strip()

        if skipping_credits and " : " in txt:
            # This is a credit line
            continue
        # We have reached non-credit lines, stop skipping
        skipping_credits = False

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
    unsynced_text = serialize_to_plain(lyrics)
    tags.delall("USLT")
    tags.delall("SYLT")
    tags.add(USLT(encoding=Encoding.UTF8, text=unsynced_text))
    if has_synced:
        # For SYLT, embed only those with a defined timestamp.
        sync_data = [(text, ts) for ts, text in lyrics if ts is not None]
        if sync_data:
            tags.add(SYLT(encoding=Encoding.UTF8, text=sync_data, format=2, type=1))
    try:
        tags.save(mp3_path)
    except Exception as e:
        raise RuntimeError(f"Failed to save lyrics to {mp3_path}: {e}") from e


def remove_embedded_lyrics(mp3_path: Path):
    try:
        tags = ID3(mp3_path)
        tags.delall("USLT")
        tags.delall("SYLT")
        tags.save(mp3_path)
    except Exception as e:
        print(f"Error: Failed to remove lyrics from {mp3_path}: {e}")


def process_lyrics(mp3_path: Path):
    lrc_path = mp3_path.with_suffix(".lrc")

    raw_lyrics: Optional[List[LyricLine]] = None

    if lrc_path.exists():
        # Priority: .lrc file if it exists
        try:
            raw_text = lrc_path.read_text(encoding="utf-8")
            raw_lyrics = parse_lyrics(raw_text)
        except Exception as e:
            print(f"Error: Failed to read lyrics from {lrc_path}: {e}")
    else:
        # Fallback: parse lyrics from ID3
        raw_lyrics = parse_id3_lyrics(mp3_path)

    if raw_lyrics:
        # Apply cleaning
        cleaned_lyrics = clean_lyrics(raw_lyrics)

        # Write to .lrc file and embed in MP3
        try:
            lrc_path.write_text(serialize_to_lrc(cleaned_lyrics), encoding="utf-8")
            embed_lyrics_to_mp3(mp3_path, cleaned_lyrics)
        except Exception as e:
            print(f"Error: Failed to process lyrics for {mp3_path}: {e}")
    else:
        print(f"No lyrics found for {mp3_path.name}, skipping")
