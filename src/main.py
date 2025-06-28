import os
import time
import pathlib

from tailscale import tailscale_setup
from download import temp_download
from metadata.main import process_file, process_directory

def main():
    print("Hello from main.py!")

    tailscale_setup()

    # print("Starting download...")
    # temp_download()
    
    # Process every MP3 file in the /music directory
    process_directory(pathlib.Path("/music"))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("An error occurred:")
        print(e)
    finally:
        print("Done. Sleeping...")
        while True:
            time.sleep(3600)
