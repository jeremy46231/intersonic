#!/bin/bash
set -e

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y curl wget tar rclone
apt-get clean
rm -rf /var/lib/apt/lists/*

arch=$(uname -m)
case "$arch" in
  x86_64) arch="amd64" ;;
  i386|i686) arch="386" ;;
  armv7l|armv6l) arch="arm" ;;
  aarch64) arch="arm64" ;;
  geode) arch="geode" ;;
  mips) arch="mips" ;;
  mips64) arch="mips64" ;;
  mips64el|mips64le) arch="mips64le" ;;
  mipsel|mipsle) arch="mipsle" ;;
  riscv64) arch="riscv64" ;;
  *) echo "Unsupported architecture: $arch"; exit 1 ;;
esac

# Set default version to "latest"
version="latest"
tarball="tailscale_${version}_${arch}.tgz"
url="https://pkgs.tailscale.com/stable/${tarball}"

echo "Downloading Tailscale from ${url}..."
wget -O "$tarball" "$url"

tar \
  --wildcards --no-anchored \
  -xvf "$tarball" \
  --strip-components=1 \
  -C /usr/local/bin \
  '*/tailscale'
rm "$tarball"

tailscale --version
