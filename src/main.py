import os
import time

from tailscale import tailscale_setup
from download import temp_download


def main():
    print("Hello from main.py!")

    tailscale_setup()

    print("Starting download...")
    temp_download()


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
