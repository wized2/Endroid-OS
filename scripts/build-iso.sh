#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
ROOTFS="$BUILD/rootfs"
ISO="$BUILD/iso"
OUT="$ROOT/endroid-os.iso"

rm -rf "$ISO"
mkdir -p "$ISO/boot/grub"

echo "==> initrd"
(
  cd "$ROOTFS"
  find . | cpio -H newc -o
) | gzip -n -1 > "$BUILD/boot/initrd.gz"
gzip -t "$BUILD/boot/initrd.gz"
ls -lh "$BUILD/boot/initrd.gz" "$BUILD/boot/vmlinuz"
zcat "$BUILD/boot/initrd.gz" | cpio -t | grep -E '^\./init$' | head

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

echo "==> grub-mkrescue"
if ! command -v grub-mkrescue >/dev/null 2>&1; then
  echo "grub-mkrescue missing" >&2
  exit 1
fi
grub-mkrescue -o "$OUT" "$ISO"
ls -lh "$OUT"

# Also extract kernel/initrd for direct QEMU testing
cp "$BUILD/boot/vmlinuz" "$ROOT/vmlinuz"
cp "$BUILD/boot/initrd.gz" "$ROOT/initrd.gz"
