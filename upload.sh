#!/bin/bash

set -eo pipefail
# shellcheck source=/dev/null
source .env

if [ -z "$BASE_PATH" ]; then
  echo "BASE_PATH is not defined. Exiting..."
  exit 1
fi

cd "${BASE_PATH}" || exit
# -a: archive mode (preserves permissions, timestamps, etc.)
# -v: verbose, so you can see the progress
# --update: skip files that are newer on the receiver
# --progress: show progress during transfer
# rsync -av --update --progress ./* "mc:/opt/navidrome/music"

# # move only .mp3 files to the usb stick, and only if it's mounted
# if mount | grep -q "/Volumes/PAPER TOWEL"; then
#   echo "PAPER TOWEL is mounted. Copying..."

#   find . -type f -name '*.mp3' | while IFS= read -r file; do
#     relpath="${file#./}"
#     echo "Processing: $relpath"
#     dest="/Volumes/PAPER TOWEL/$relpath"
#     mkdir -p "$(dirname "$dest")"
#     # Only copy if destination doesn't exist or source is newer
#     if [ ! -f "$dest" ] || [ "$file" -nt "$dest" ]; then
#       cp -p "$file" "$dest"
#       echo "Copied: $file to $dest"
#     else
#       echo "Skipped (destination up to date): $file"
#     fi
#   done
# fi