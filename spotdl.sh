#!/bin/bash
# Author: Jeremy Woolley <jeremy@jeremywoolley.com>

set -eo pipefail
start_time=$(date '+%Y-%m-%d_%H:%M:%S')

# shellcheck source=/dev/null
source .env
# shellcheck source=/dev/null
source queries.sh

ls "${BASE_PATH}" || (log "BASE_PATH is not present. Exiting..."; exit 1)

mkdir -p log
log_file="./log/${start_time}.log"
spotdl_errors_file="./log/${start_time}_errors.log"

log() {
  echo "$1" | tee -a "$log_file"
}
time_difference() {
  local start="$1"
  local end="$2"
  local start_sec end_sec diff
  start_sec=$(date -j -f "%Y-%m-%d_%H:%M:%S" "$start" "+%s")
  end_sec=$(date -j -f "%Y-%m-%d_%H:%M:%S" "$end" "+%s")
  diff=$(( end_sec - start_sec ))
  if (( diff < 3600 )); then
    date -u -r "$diff" +"%M:%S"
  else
    date -u -r "$diff" +"%H:%M:%S"
  fi
}

log "Starting download process..."

# shellcheck disable=SC2154
queries_length=${#queries[@]}
log "Query count: ${queries_length}"
for ((i = 0; i < queries_length; i++)); do
  log "Query $((i + 1)): ${queries[i]}"
done

log "Starting SpotDL at ${start_time}"

# shellcheck disable=SC2154
# uv run spotify-downloader/spotdl/__main__.py \
  # --user-auth \
spotdl \
  --log-level DEBUG \
  --audio youtube-music --lyrics synced --lyrics musixmatch --lyrics genius --lyrics azlyrics \
  --use-cache-file --preload \
  --threads 8 --bitrate disable \
  --overwrite skip \
  --output "${BASE_PATH}/{album-artist}/{album}/{track-number} {title}.{output-ext}" \
  --id3-separator "; " --generate-lrc \
  --save-errors "${spotdl_errors_file}" \
  --client-id "${SPOTIFY_CLIENT_ID}" --client-secret "${SPOTIFY_CLIENT_SECRET}" \
  --genius-access-token "${GENIUS_ACCESS_TOKEN}" \
  download "${queries[@]}"
  # --print-errors \
  # --scan-for-songs \
  # --archive "./archive.txt" \

spotdl_end_time=$(date '+%Y-%m-%d_%H:%M:%S')
spotdl_errors=$(cat "$spotdl_errors_file")
rm "$spotdl_errors_file"

spotdl_time=$(time_difference "${start_time}" "${spotdl_end_time}")
log "Finished download process at ${spotdl_end_time}"
log "SpotDL took ${spotdl_time}"
log "Errors:"
log "$spotdl_errors"

log "Cleaning up lyrics files..."

./lyrics.py "${BASE_PATH}"

end_time=$(date '+%Y-%m-%d_%H:%M:%S')
log "Finished cleaning up lyrics files at ${end_time}"

total_time=$(time_difference "${start_time}" "${end_time}")
log "Total time: ${total_time}"
log "Done!"
