from pathlib import Path
from typing import Optional
from collections.abc import Callable
from spotdl import Spotdl
from spotdl.utils.formatter import create_file_name
from spotdl.types.options import DownloaderOptionalOptions
from spotdl.types.song import Song
import os
import asyncio

from metadata.main import process_file

client_id = os.environ.get("SPOTIFY_CLIENT_ID")
client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
genius_token = os.environ.get("GENIUS_ACCESS_TOKEN")

if not client_id or not client_secret:
    raise ValueError(
        "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set as environment variables"
    )
if not genius_token:
    print("Warning: GENIUS_ACCESS_TOKEN is not set")

downloader_settings: DownloaderOptionalOptions = {
    "audio_providers": ["youtube-music"],
    "lyrics_providers": ["synced", "musixmatch", "genius", "azlyrics"],
    "preload": True,
    "threads": 8,
    "bitrate": "disable",
    "overwrite": "skip",
    "output": "/music/{album-artist}/{album}/{track-number} {title}.{output-ext}",
    "id3_separator": "; ",
    "proxy": "http://100.100.100.100:8080",
}
if genius_token:
    downloader_settings["genius_token"] = genius_token


def get_spotdl():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    if not client_id:
        raise ValueError("SPOTIFY_CLIENT_ID environment variable is not set")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_secret:
        raise ValueError("SPOTIFY_CLIENT_SECRET environment variable is not set")

    spotdl = Spotdl(
        client_id=client_id,
        client_secret=client_secret,
        cache_path="/data/spotipy-cache/spotipy_cache",
        headless=True,
        downloader_settings=downloader_settings,
    )
    return spotdl


spotdl = get_spotdl()


def download_missing(
    queries: list[str], status_callback: Optional[Callable[[str], None]] = None
):
    # spotdl = get_spotdl()

    print(f"Searching for {len(queries)} queries")
    if status_callback:
        status_callback(
            f"Searching for {len(queries)} {'query' if len(queries) == 1 else 'queries'}..."
        )
    songs = spotdl.search(queries)
    print(f"Found {len(songs)} songs")

    to_download: list[Song] = []
    for song in songs:
        path = create_file_name(
            song=song,
            template=spotdl.downloader.settings["output"],
            file_extension=spotdl.downloader.settings["format"],
            restrict=spotdl.downloader.settings["restrict"],
            file_name_length=spotdl.downloader.settings["max_filename_length"],
        )
        file_exists = os.path.exists(path)
        if not file_exists:
            to_download.append(song)

    if not to_download:
        print("All songs already downloaded.")
        return []

    print(f"Downloading {len(to_download)} songs")
    if status_callback:
        status_callback(
            f"Downloading {len(to_download)} {'song' if len(to_download) == 1 else 'songs'}..."
        )

    total_songs = len(to_download)
    downloaded_songs = 0

    loop = asyncio.get_event_loop()
    semaphore = asyncio.Semaphore(spotdl.downloader.settings["threads"])

    async def download_song(song: Song) -> tuple[Song, Optional[Path]]:
        nonlocal downloaded_songs
        try:
            async with semaphore:
                song, path = await loop.run_in_executor(
                    None, spotdl.downloader.search_and_download, song
                )
            if path:
                process_file(path)

            downloaded_songs += 1
            percentage_str = f"{(downloaded_songs / total_songs) * 100:.2f}%"
            song_log_str = f"Downloaded {percentage_str} ({downloaded_songs}/{total_songs}) - '{song.display_name}'"
            print(song_log_str)
            if status_callback:
                status_callback(song_log_str)

            return song, path
        except Exception as e:
            print(f"Error downloading {song.display_name}: {e}")
            return song, None

    tasks = [download_song(song) for song in to_download]
    results = loop.run_until_complete(asyncio.gather(*tasks))

    successful_downloads = len([song for song, path in results if path is not None])
    failed_downloads = len([song for song, path in results if path is None])
    done_log_str = f"Successfully downloaded {successful_downloads} out of {total_songs} songs. Failed to download {failed_downloads} songs."
    print(done_log_str)
    if status_callback:
        status_callback(done_log_str)

    return results
