from spotdl import Spotdl
from spotdl.utils.formatter import create_file_name
from spotdl.types.options import DownloaderOptionalOptions
from spotdl.types.song import Song
from pathlib import Path
import os

client_id = os.environ.get("SPOTIFY_CLIENT_ID")
client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
genius_token = os.environ.get("GENIUS_ACCESS_TOKEN")

if not client_id or not client_secret:
    raise ValueError(
        "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set as environment variables"
    )
if not genius_token:
    print("GENIUS_ACCESS_TOKEN is not set")

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

spotdl_client: Spotdl | None = None


def get_spotdl():
    global spotdl_client
    if spotdl_client is not None:
        return spotdl_client

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    if not client_id:
        raise ValueError("SPOTIFY_CLIENT_ID environment variable is not set.")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_secret:
        raise ValueError("SPOTIFY_CLIENT_SECRET environment variable is not set.")

    spotdl = Spotdl(
        client_id=client_id,
        client_secret=client_secret,
        cache_path="/data/spotipy-cache/spotipy_cache",
        headless=True,
        downloader_settings=downloader_settings,
    )
    spotdl_client = spotdl
    return spotdl


def temp_download():
    spotdl = get_spotdl()
    queries = ["https://open.spotify.com/artist/4LkmOQU5KA6vZgvJHnpQDl"]

    print(f"Searching for {len(queries)} queries")
    songs = spotdl.search(queries)
    print(f"Found {len(songs)} songs to download.")

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
        if file_exists:
            print(f"File already exists: {path}")
        else:
            print(f"Downloading song: {song.display_name} to {path}")
            to_download.append(song)

    results = spotdl.download_songs(to_download)

    for song, path in results:
        print(f"Downloaded {song.display_name} to {path}")
