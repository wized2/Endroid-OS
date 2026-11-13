#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
ROOTFS="$BUILD/rootfs"
ISO="$BUILD/iso"
DEP="$ROOT/deps"
OUT="$ROOT/endroid-os.iso"

rm -rf "$ISO"
mkdir -p "$ISO/boot" "$ISO/EFI/BOOT"

echo "==> initramfs"
(
  cd "$ROOTFS"
  find . | cpio -H newc -o
) | gzip -n -1 > "$BUILD/boot/initrd.gz"
gzip -t "$BUILD/boot/initrd.gz"
ls -lh "$BUILD/boot/initrd.gz"
# verify /init present
zcat "$BUILD/boot/initrd.gz" | cpio -t | grep -E '^\./init$|^init$' | head

cp "$BUILD/boot/vmlinuz" "$ISO/vmlinuz"
cp "$BUILD/boot/initrd.gz" "$ISO/initrd.gz"
cp "$ROOT/boot/limine.cfg" "$ISO/limine.cfg"
cp "$ROOT/boot/limine.conf" "$ISO/limine.conf"

LIMINE_DIR="$DEP/limine"
make -C "$LIMINE_DIR" limine 2>/dev/null || true
cp "$LIMINE_DIR/limine-bios.sys" "$ISO/"
cp "$LIMINE_DIR/limine-bios-cd.bin" "$ISO/"
cp "$LIMINE_DIR/limine-uefi-cd.bin" "$ISO/"
cp "$LIMINE_DIR/BOOTX64.EFI" "$ISO/EFI/BOOT/BOOTX64.EFI"

xorriso -as mkisofs -R -r -J -joliet-long -l -V ENDROID_OS -o "$OUT" \
  -b limine-bios-cd.bin -no-emul-boot -boot-load-size 4 -boot-info-table \
  -eltorito-alt-boot -e limine-uefi-cd.bin -no-emul-boot \
  "$ISO"

if [ -x "$LIMINE_DIR/limine" ]; then
  "$LIMINE_DIR/limine" bios-install "$OUT" || true
fi
ls -lh "$OUT"
