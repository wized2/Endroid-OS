#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
ROOTFS="$BUILD/rootfs"
ISO="$BUILD/iso"
OUT="$ROOT/endroid-os.iso"

rm -rf "$ISO"
mkdir -p "$ISO/boot/grub"

echo "==> ensure /init"
# Re-copy init from overlay in case
cp -f "$ROOT/overlay/init" "$ROOTFS/init"
chmod 755 "$ROOTFS/init"
# Also provide /sbin/init fallback
mkdir -p "$ROOTFS/sbin"
cp -f "$ROOTFS/init" "$ROOTFS/sbin/init"
chmod 755 "$ROOTFS/sbin/init"
ls -la "$ROOTFS/init"
head -1 "$ROOTFS/init"
test -x "$ROOTFS/bin/busybox" || test -x "$ROOTFS/usr/bin/busybox" || ls -la "$ROOTFS/bin" | head

echo "==> pack initrd as root in docker (preserve + executable)"
docker run --rm --privileged \
  -v "$ROOTFS:/rootfs:ro" \
  -v "$BUILD/boot:/outboot" \
  alpine:3.20 \
  sh -c '
    set -e
    apk add --no-cache cpio gzip >/dev/null
    # copy to writable then pack
    rm -rf /tmp/r
    mkdir /tmp/r
    cp -a /rootfs/. /tmp/r/
    chmod 755 /tmp/r/init /tmp/r/sbin/init
    # busybox shebang needs /bin/busybox
    if [ ! -e /tmp/r/bin/busybox ]; then
      if [ -e /tmp/r/usr/bin/busybox ]; then
        mkdir -p /tmp/r/bin
        ln -sf ../usr/bin/busybox /tmp/r/bin/busybox
      fi
    fi
    ln -sf busybox /tmp/r/bin/sh 2>/dev/null || true
    ( cd /tmp/r && find . | cpio -H newc -o ) | gzip -n -1 > /outboot/initrd.gz
    gzip -t /outboot/initrd.gz
    echo "initrd entries:"
    zcat /outboot/initrd.gz | cpio -t | grep -E "init|busybox" | head -n 20
    ls -lh /outboot/initrd.gz
    chown 1001:1001 /outboot/initrd.gz 2>/dev/null || chown 1000:1000 /outboot/initrd.gz 2>/dev/null || true
  '

ls -lh "$BUILD/boot/initrd.gz" "$BUILD/boot/vmlinuz"

cp "$BUILD/boot/vmlinuz" "$ISO/boot/vmlinuz"
cp "$BUILD/boot/initrd.gz" "$ISO/boot/initrd.gz"

cat > "$ISO/boot/grub/grub.cfg" << 'GRUB'
set timeout=2
set default=0
serial --unit=0 --speed=115200
terminal_input serial console
terminal_output serial console
menuentry "Endroid OS" {
    linux /boot/vmlinuz console=tty0 console=ttyS0,115200 rdinit=/init
    initrd /boot/initrd.gz
}
GRUB

grub-mkrescue -o "$OUT" "$ISO"
ls -lh "$OUT"
cp "$BUILD/boot/vmlinuz" "$ROOT/vmlinuz"
cp "$BUILD/boot/initrd.gz" "$ROOT/initrd.gz"
