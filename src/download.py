from spotdl import Spotdl
import os

client_id = os.environ.get("SPOTIFY_CLIENT_ID")
client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
genius_token = os.environ.get("GENIUS_ACCESS_TOKEN")

if not client_id or not client_secret:
    raise ValueError(
        "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set as environment variables"
    )
if not genius_token:
    print("GENIUS_ACCESS_TOKEN is not set; lyrics from Genius may not work.")
    
downloader_settings = {
    "audio_providers": ["youtube-music"],
    "lyrics_providers": ["synced", "musixmatch", "genius", "azlyrics"],
    "preload": True,
    "threads": 8,
    "bitrate": "disable",
    "overwrite": "skip",
    "output": "/music/{album-artist}/{album}/{track-number} {title}.{output-ext}",
    "id3_separator": "; ",
    "generate_lrc": True,
    "genius_token": genius_token,
}


spotdl = Spotdl(
    client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
    client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    cache_path="/data/spotipy-cache",
    headless=True,
)

def temp_download():
    queries = [
        "https://open.spotify.com/artist/4LkmOQU5KA6vZgvJHnpQDl"
    ]

    songs = spotdl.search(queries)
    results = spotdl.download_songs(songs)