import io
from pathlib import Path
from typing import Optional

from mutagen.id3 import ID3
from mutagen.id3._frames import APIC
from PIL import Image


def extract_embedded_art(mp3_path: Path) -> Optional[bytes]:
    """
    Extracts album art from an MP3 file's ID3 tags.
    Returns the first 'APIC' (Attached Picture) frame's data as bytes.
    """
    try:
        tags = ID3(mp3_path)
        # 'APIC:' is the key for Attached Picture frames
        apic_frames = tags.getall("APIC")
        print(f"Found {len(apic_frames)} embedded art frames in {mp3_path}")
        print(f"APIC frames: {apic_frames}")
        if apic_frames:
            # Just return the data of the first picture found
            return apic_frames[0].data
    except Exception as e:
        print(f"Warning: Could not extract embedded art from {mp3_path}: {e}")
        pass
    return None


def convert_to_jpeg(image_data: bytes) -> Optional[bytes]:
    """
    Converts image data from any format into JPEG format using Pillow.
    If the data is already JPEG, it's returned as-is.
    """
    try:
        with io.BytesIO(image_data) as in_buffer:
            img = Image.open(in_buffer)

            # If it's already a JPEG, don't re-encode
            if img.format == "JPEG":
                return image_data

            # Remove transparency if the image has it
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            with io.BytesIO() as out_buffer:
                img.save(out_buffer, format="JPEG", quality=95)
                return out_buffer.getvalue()
    except Exception as e:
        print(f"Warning: Could not process or convert image to JPG: {e}")
        return None


def embed_art_to_mp3(mp3_path: Path, image_data: bytes):
    """Embeds the given JPG image data into the MP3 file's ID3 tags."""
    try:
        tags = ID3(mp3_path)
    except Exception:
        tags = ID3()  # Create new ID3 tag

    # Remove any existing art to prevent duplicates
    tags.delall("APIC")
    tags.add(
        APIC(
            encoding=3,  # 3 is for utf-8
            mime="image/jpeg",
            type=3,  # 3 is for the cover (front) image
            desc="Cover",
            data=image_data,
        )
    )
    tags.save(mp3_path)
    print(f"Embedded album art into {mp3_path}")


def process_album_art(mp3_path: Path):
    """
    Processes album art for the given MP3 file.
    It prioritizes an external .jpg file, falls back to embedded art,
    and ensures both the file and the MP3 tag are synchronized.
    If no art is found, it cleans up any existing art.
    """
    jpg_path = mp3_path.with_suffix(".jpg")

    raw_image_data: Optional[bytes] = None

    if jpg_path.exists():
        # Priority 1: .jpg file if it exists
        raw_image_data = jpg_path.read_bytes()
    else:
        # Priority 2: Fallback to embedded art
        raw_image_data = extract_embedded_art(mp3_path)

    if raw_image_data:
        # We have image data, now process and sync it
        final_jpg_data = convert_to_jpeg(raw_image_data)

        if final_jpg_data:
            # Write to .jpg file and embed in MP3
            jpg_path.write_bytes(final_jpg_data)
            embed_art_to_mp3(mp3_path, final_jpg_data)
        else:
            print(f"Could not get image data for {mp3_path.name}, skipping")
    else:
        print(f"Could not find any album art for {mp3_path.name}, skipping")