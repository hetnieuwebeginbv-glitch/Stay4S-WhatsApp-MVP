# STAY4OS FLASH-FIX — Diagnose + oplossing (22 sep)
## Waarom de flash mislukte en hoe we het oplossen

## DIAGNOSE

### Symptoom
- Stay4OS geflasht (boot_b, system_b, vendor_b, product_b, system_ext_b)
- Telefoon op Google-logo → terugval naar bootloader ("boot slot b")
- Kernel kon niet opstarten

### Oorzaak
**dtb.img (device tree blob) was 0 bytes in de AOSP-build output.**
Zonder device tree weet de kernel niet welke hardware aanwezig is
(display, opslag, etc.) → kernel hangt bij initialisatie.

De kernel ZELF was goed (Bazel-build succesvol, boot.img 53MB met
ingebouwde dtb). Maar de AOSP-build systeem maakte zijn eigen boot.img
(64MB) met een LEEGE dtb.

### Bewijs
- Kernel-build boot.img: 53.477.376 bytes (51MB) — bevat dtb ✓
- AOSP boot.img: 67.108.864 bytes (64MB) — dtb leeg ✗
- dtb.img in AOSP output: 0 bytes ✗

## OPLOSSING (voor de volgende build)

### Optie A — Kernel boot.img direct gebruiken (aanbevolen)
Gebruik de kernel-build's boot.img (53MB, met dtb) in plaats van de
AOSP-built boot.img (64MB, lege dtb).

```bash
# In de AOSP build, vervang de gegenereerde boot.img:
cp <kernel-build-output>/boot.img out/target/product/tegu/boot.img
# of zet TARGET_PREBUILT_KERNEL + TARGET_PREBUILT_DTB naar de kernel-build
```

### Optie B — DTB correct meenemen
Zorg dat de kernel-build's dtb.img (1.5MB) op de juiste plek komt:
```bash
# De dtb moet in de boot.img of vendor_boot.img zitten
# Check: unpack de AOSP boot.img en verifieer dtb aanwezig
```

### Optie C — Verify vóór flash
Test de boot.img vóór flashen (on-device):
```bash
# Check of boot.img een dtb bevat
python -c "
with open('boot.img','rb') as f: d=f.read()
print('grootte:', len(d))
# Android boot image: kernel_size na header
import struct
if d[:8]==b'ANDROID!':
    ks=struct.unpack('<I', d[8:12])[0]
    print('kernel:', ks, 'bytes')
"
```

## HERSTEL-STATUS
- [x] Officiële boot images terug naar slot A
- [x] Officiële LineageOS sideload (herinstallatie bezig)
- [ ] Telefoon weer op LineageOS
- [ ] Daarna: Stay4OS-fix + nieuwe poging

## EXTRA — Super-partitie
- wipe-super faalde (super_empty.img niet parseerbaar)
- Gevolg: super-metadata mogelijk inconsistent
- Fix: gebruik de OFFICIELE super_empty.img (niet onze 5KB versie)
- Of: flashen via ADB sideload (bewezen route, werkt)

## CONCLUSIE
De Stay4OS-build is 90% goed (kernel + systeem gebouwd). De fix is:
**de kernel-build's boot.img met ingebouwde dtb gebruiken** + super-
partitie correct wipen. Daarna flasht het.

*OpenCode — 22 sep. Diagnose voor Droid's volgende poging.*