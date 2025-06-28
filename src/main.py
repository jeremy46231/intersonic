import pathlib

from tailscale import tailscale_setup
from download import download_missing
from metadata.main import process_directory


def main():
    print("Hello from main.py")

    tailscale_setup()

    print("Starting download...")
    queries = ["https://open.spotify.com/track/2LCGFBu1ej6zt4r1VGPjny"]
    download_missing(queries)

    process_directory(pathlib.Path("/music"))


if __name__ == "__main__":
    main()
