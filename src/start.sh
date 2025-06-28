#!/bin/sh
set -e

tailscaled \
  --tun=userspace-networking \
  --socks5-server=localhost:1055 --outbound-http-proxy-listen=localhost:1055 \
  >/dev/null 2>/dev/null &

export ALL_PROXY=socks5h://localhost:1055/
export HTTP_PROXY=http://localhost:1055/
export HTTPS_PROXY=http://localhost:1055/
export NO_PROXY=localhost,127.0.0.1,::1,.local,.test,.example,.invalid

export PYTHONUNBUFFERED=1
# Use Gunicorn to run the Flask app from the 'web.server' module.
# --workers 1: Important for threading.Lock to work
# --bind 0.0.0.0:3000: Listen on port 3000 on all available network interfaces
# web.server:app: Tells Gunicorn to look for an object named 'app' in the 'src/web/server.py' file.
exec gunicorn --workers 1 --threads 4 --bind 0.0.0.0:3000 --log-level "info" web.server:app
