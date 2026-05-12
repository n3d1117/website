#!/usr/bin/env bash
set -euo pipefail

# Install the user-local tools needed for direct Cloudflare Pages deploys.

NODE_VERSION="${NODE_VERSION:-22.21.1}"
HUGO_VERSION="${HUGO_VERSION:-0.161.1}"
LOCAL_DIR="${HOME}/.local"
NODE_DIR="${LOCAL_DIR}/node"
BIN_DIR="${LOCAL_DIR}/bin"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$BIN_DIR"

arch="$(uname -m)"
case "$arch" in
  aarch64 | arm64)
    node_arch="arm64"
    hugo_arch="arm64"
    ;;
  x86_64 | amd64)
    node_arch="x64"
    hugo_arch="amd64"
    ;;
  *)
    echo "Unsupported architecture: $arch"
    exit 1
    ;;
esac

node_archive="node-v${NODE_VERSION}-linux-${node_arch}.tar.xz"
curl --fail --location --silent --show-error \
  "https://nodejs.org/dist/v${NODE_VERSION}/${node_archive}" \
  --output "${TMP_DIR}/${node_archive}"
rm -rf "$NODE_DIR"
mkdir -p "$NODE_DIR"
tar -xJf "${TMP_DIR}/${node_archive}" --strip-components=1 -C "$NODE_DIR"

hugo_archive="hugo_extended_${HUGO_VERSION}_linux-${hugo_arch}.tar.gz"
curl --fail --location --silent --show-error \
  "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/${hugo_archive}" \
  --output "${TMP_DIR}/${hugo_archive}"
tar -xzf "${TMP_DIR}/${hugo_archive}" -C "$TMP_DIR" hugo
install -m 0755 "${TMP_DIR}/hugo" "${BIN_DIR}/hugo"

export PATH="${NODE_DIR}/bin:${BIN_DIR}:$PATH"
npm install --global wrangler@4.90.0

node --version
npm --version
hugo version
wrangler --version
