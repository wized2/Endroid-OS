#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
DEP="$ROOT/deps"
BUILD="$ROOT/build"
ROOTFS="$BUILD/rootfs"
rm -rf "$ROOTFS"
mkdir -p "$ROOTFS" "$BUILD/boot"

echo "==> unpack minirootfs"
tar -xzf "$DEP/alpine-minirootfs.tar.gz" -C "$ROOTFS"
echo "nameserver 1.1.1.1" > "$ROOTFS/etc/resolv.conf"

echo "==> packages (GTK4, linux-virt, no browser)"
docker run --rm --privileged --network host \
  -v "$ROOTFS:/rootfs" \
  -v "$ROOT/overlay:/overlay:ro" \
  -v "$BUILD/boot:/outboot" \
  alpine:3.20 \
  sh -c '
    set -e
    echo "nameserver 1.1.1.1" > /rootfs/etc/resolv.conf
    # ensure community repo
    echo "https://dl-cdn.alpinelinux.org/alpine/v3.20/main" > /rootfs/etc/apk/repositories
    echo "https://dl-cdn.alpinelinux.org/alpine/v3.20/community" >> /rootfs/etc/apk/repositories

    mount --bind /proc /rootfs/proc
    mount --bind /sys /rootfs/sys
    mount --bind /dev /rootfs/dev
    mkdir -p /rootfs/dev/pts
    mount -t devpts devpts /rootfs/dev/pts || true

    chroot /rootfs /bin/sh -c "
      set -e
      apk update
      apk add --no-cache \
        linux-virt \
        busybox-extras \
        xorg-server xf86-video-modesetting xf86-input-libinput \
        mesa-dri-gallium mesa-egl \
        openbox xinit xauth \
        gtk4.0 py3-gobject3 py3-cairo python3 \
        font-noto ttf-dejavu \
        util-linux e2fsprogs iproute2
    "

    cp -a /overlay/. /rootfs/
    chmod +x /rootfs/init /rootfs/usr/local/bin/* /rootfs/usr/share/endroid/shell.py
    echo endroid > /rootfs/etc/hostname

    mkdir -p /rootfs/etc/X11
    cat > /rootfs/etc/X11/xorg.conf << "XORG"
Section "ServerFlags"
  Option "DontZap" "false"
EndSection
XORG

    # kernel image
    if [ -f /rootfs/boot/vmlinuz-virt ]; then
      cp -f /rootfs/boot/vmlinuz-virt /outboot/vmlinuz
    else
      f=$(find /rootfs/boot -maxdepth 1 -type f -name "vmlinuz*" | head -n1)
      cp -f "$f" /outboot/vmlinuz
    fi

    # Drop heavy/unused bits to shrink initrd
    rm -rf /rootfs/boot/initramfs* /rootfs/var/cache/apk/* \
           /rootfs/usr/share/man /rootfs/usr/share/doc \
           /rootfs/usr/share/gtk-doc \
           /rootfs/usr/lib/python3.*/turtledemo \
           /rootfs/usr/lib/python3.*/test \
           /rootfs/usr/lib/python3.*/ensurepip \
           /rootfs/usr/share/locale \
           /rootfs/usr/share/X11/locale \
           /rootfs/var/lib/apk 2>/dev/null || true
    rm -rf /rootfs/lib/firmware 2>/dev/null || true

    umount /rootfs/dev/pts 2>/dev/null || true
    umount /rootfs/dev 2>/dev/null || true
    umount /rootfs/proc 2>/dev/null || true
    umount /rootfs/sys 2>/dev/null || true

    chown -R 1001:1001 /rootfs /outboot 2>/dev/null || chown -R 1000:1000 /rootfs /outboot 2>/dev/null || true
    chmod -R a+rX /rootfs /outboot || true
  '

test -f "$BUILD/boot/vmlinuz"
echo "==> rootfs $(du -sh "$ROOTFS" | awk "{print \$1}")"
