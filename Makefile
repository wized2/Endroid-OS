.PHONY: all iso smoke clean
all: iso
iso:
	./scripts/fetch-deps.sh
	./scripts/build-rootfs.sh
	./scripts/build-iso.sh
smoke: endroid-os.iso
	./scripts/qemu-smoke.sh endroid-os.iso screenshots
clean:
	rm -rf build endroid-os.iso screenshots deps
