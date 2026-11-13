#!/bin/sh
set -eu
ISO="${1:-endroid-os.iso}"
OUTDIR="${2:-screenshots}"
mkdir -p "$OUTDIR"
LOG="$(mktemp)"
QMP="$(mktemp -u /tmp/eq.XXXX.sock)"

echo "==> QEMU smoke (direct kernel+initrd — proves userspace)"
# Prefer direct -kernel/-initrd (authoritative). ISO is still built for real machines.
K=vmlinuz
I=initrd.gz
if [ ! -f "$K" ] || [ ! -f "$I" ]; then
  echo "missing $K/$I — using ISO only"
  qemu-system-x86_64 -m 2048 -cdrom "$ISO" -boot d -display none -vga std \
    -serial file:"$LOG" -qmp unix:"$QMP",server,nowait -no-reboot &
else
  qemu-system-x86_64 -m 2048 -kernel "$K" -initrd "$I" \
    -append "console=tty0 console=ttyS0,115200 rdinit=/init" \
    -display none -vga std \
    -serial file:"$LOG" -qmp unix:"$QMP",server,nowait -no-reboot &
fi
QPID=$!
cleanup() { kill "$QPID" 2>/dev/null || true; wait "$QPID" 2>/dev/null || true; rm -f "$QMP"; }
trap cleanup EXIT

qmp() {
  printf '%s\n' '{ "execute": "qmp_capabilities" }' "$1" | socat - UNIX-CONNECT:"$QMP" 2>/dev/null || true
}
shot() {
  n="$1"; ppm="$OUTDIR/$n.ppm"; png="$OUTDIR/$n.png"
  qmp "{ \"execute\": \"screendump\", \"arguments\": { \"filename\": \"$ppm\" } }"
  sleep 1
  if [ -f "$ppm" ] && command -v convert >/dev/null; then
    convert "$ppm" "$png" && rm -f "$ppm"
    echo "shot $png ($(wc -c <"$png") bytes)"
  fi
}

ok=0
i=0
while [ $i -lt 90 ]; do
  if grep -q "endroid-os: sysinit ok" "$LOG" 2>/dev/null; then ok=1; break; fi
  if grep -q "endroid-os: /init start" "$LOG" 2>/dev/null; then ok=1; fi
  if grep -q "endroid-boot: ui online" "$LOG" 2>/dev/null; then ok=1; break; fi
  if grep -q "Kernel panic" "$LOG" 2>/dev/null; then break; fi
  i=$((i+1)); sleep 1
done

shot 01-early
j=0
while [ $j -lt 45 ]; do
  if grep -q "endroid-boot: ui online" "$LOG" 2>/dev/null; then ok=1; break; fi
  if grep -q "Kernel panic" "$LOG" 2>/dev/null; then break; fi
  j=$((j+1)); sleep 1
done
shot 02-session
sleep 8
shot 03-ui

cp "$LOG" "$OUTDIR/serial.log"
echo "==> serial tail"; tail -n 100 "$LOG" || true

if grep -q "Kernel panic" "$LOG"; then
  echo "SMOKE FAILED panic"; exit 1
fi
if grep -q "endroid-os: sysinit ok" "$LOG" || grep -q "endroid-os: /init start" "$LOG" \
   || grep -q "endroid-boot: ui online" "$LOG"; then
  echo "SMOKE OK"; exit 0
fi
echo "SMOKE FAILED"; exit 1
