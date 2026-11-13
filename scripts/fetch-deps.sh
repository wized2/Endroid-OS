#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
DEP="$ROOT/deps"
mkdir -p "$DEP"
ALPINE_VER="3.20.3"
ARCH="x86_64"

if [ ! -f "$DEP/limine/limine-bios.sys" ]; then
  echo "==> Limine v8.x-binary"
  rm -rf "$DEP/limine"
  git clone --depth 1 --branch v8.x-binary \
    https://github.com/limine-bootloader/limine.git "$DEP/limine"
  make -C "$DEP/limine" limine || true
fi

if [ ! -f "$DEP/alpine-minirootfs.tar.gz" ]; then
  echo "==> Alpine minirootfs"
  major="${ALPINE_VER%.*}"
  wget -qO "$DEP/alpine-minirootfs.tar.gz" \
    "https://dl-cdn.alpinelinux.org/alpine/v${major}/releases/${ARCH}/alpine-minirootfs-${ALPINE_VER}-${ARCH}.tar.gz"
fi
echo "deps ready"
