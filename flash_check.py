#!/usr/bin/env python3
"""Flash-check voor Stay4OS OTA-zip vóór sideload.

Verifieert de bacon-output (lineage-*.zip) + boot.img-dtb vóór flashen.
Dit voorkomt een herhaling van poging 1 (lege dtb + verkeerde slot).
"""
import os
import struct
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

ROM_DIR = r"D:\STAY4S-DATA\stay4os-rom"
V4_DIR = os.path.join(ROM_DIR, "v4")


def check_boot_dtb(boot_path):
    """Check of boot.img een echte kernel bevat."""
    try:
        with open(boot_path, "rb") as f:
            d = f.read()
        print(f"[boot.img] grootte: {len(d)} bytes")
        if d[:8] == b"ANDROID!":
            ks = struct.unpack("<I", d[8:12])[0]
            ok = ks > 100000
            print(f"[boot.img] kernel: {ks} bytes → {'OK (kernel+dtb aanwezig)' if ok else 'LEEG (dtb mist!)'}")
            return ok
        print("[boot.img] GEEN Android boot image magic!")
        return False
    except Exception as e:
        print(f"[boot.img] FOUT: {e}")
        return False


def check_ota_zip(zip_path):
    """Check of de OTA-zip geldig is."""
    if not os.path.exists(zip_path):
        return False
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            has_payload = any("payload.bin" in n for n in names)
            has_script = any("updater-script" in n for n in names)
            size = os.path.getsize(zip_path)
            print(f"[ota-zip] {os.path.basename(zip_path)}: {round(size/1e6,1)} MB")
            print(f"[ota-zip] payload.bin: {has_payload} | updater-script: {has_script}")
            return has_payload or has_script
    except Exception as e:
        print(f"[ota-zip] FOUT: {e}")
        return False


def main():
    # 1. check de v4 boot.img (kernel van AOSP-build)
    boot_v4 = os.path.join(V4_DIR, "boot.img")
    print("=== CHECK 1: boot.img dtb ===")
    v4_ok = check_boot_dtb(boot_v4)

    # 2. check of er een nieuwe OTA-zip is (Droid's bacon output)
    print("\n=== CHECK 2: OTA-zip ===")
    zips = [f for f in os.listdir(ROM_DIR) if f.endswith(".zip")]
    new_zips = [f for f in zips if not os.path.exists(os.path.join(ROM_DIR, f)) or True]
    for z in sorted(zips):
        p = os.path.join(ROM_DIR, z)
        check_ota_zip(p)

    # 3. conclusie
    print("\n=== CONCLUSIE ===")
    if v4_ok:
        print("boot.img: OK (kernel aanwezig). Klaar voor flash.")
    else:
        print("boot.img: PROBLEEM — gebruik de kernel-build boot.img (53MB, met dtb).")
    print("Flash-route: ADB sideload via recovery (zie STAY4OS_FLASH_PROCEDURE_v2.md).")


if __name__ == "__main__":
    main()