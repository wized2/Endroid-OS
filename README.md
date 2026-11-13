# Endroid OS

Lightweight Linux that boots into a **GTK4** desktop UI styled with **Material You 3**.

- x86_64 · BIOS + UEFI (Limine)
- Alpine userspace · BusyBox init
- **No browser** — native GTK4 shell
- Apps: Calculator, Notepad, Timer, System

```bash
make all          # build ISO
make smoke        # QEMU smoke + screenshots
qemu-system-x86_64 -m 1024 -cdrom endroid-os.iso -boot d
```
