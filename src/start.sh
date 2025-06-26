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

python3 -u main.py
