# STAY4OS FLASH-PROCEDURE v2 — Definitieve volgorde (op basis van LineageOS-wiki)
## 22 sep 2026 — de juiste route (ADB sideload, niet fastbootd)

## KERNLESSEN VAN POGING 1
1. **NIET fastbootd gebruiken** — de officiële route is ADB sideload via recovery
2. **dtb.img was 0 bytes** — kernel-build boot.img (53MB, met dtb) direct gebruiken
3. **Flash-volgorde is cruciaal** — de wiki-stappen exact volgen

## DE DEFINITIEVE PROCEDURE (LineageOS-wiki, bewezen)

### Stap 1 — Boot images flashen (fastboot)
```bash
# flash in deze volgorde (zonder _a suffix — fastboot kiest de slot zelf)
fastboot flash boot boot.img
fastboot flash dtbo dtbo.img
fastboot flash vendor_kernel_boot vendor_kernel_boot.img
fastboot reboot bootloader
```

### Stap 2 — Recovery flashen (vendor_boot)
```bash
fastboot flash vendor_boot vendor_boot.img
# reboot naar recovery (volume-down + power, kies "Recovery Mode")
```

### Stap 3 — Factory reset (in recovery)
- Factory Reset → Format data / factory reset → bevestig

### Stap 4 — ADB sideload (in recovery)
- Apply Update → Apply from ADB
```bash
adb -d sideload stay4os_tegu-ota.zip
```
- (bij "reboot to recovery voor add-ons" → kies "No")
- Reboot system now

## VOOR STAY4OS (onze ROM)

De Stay4OS-build heeft **geen OTA zip** (webview-failure blokkeerde bacon).
We hebben wel alle .img files. Oplossing:

### Optie A — OTA zip maken (aanbevolen)
- De .img files in een flashbare zip zetten (update-binary die de images flasht)
- OF: een payload.bin genereren (LineageOS OTA-format)
- Dan: adb sideload werkt (bewezen route)

### Optie B — De browser-flash-tool (Mitchell's vondst)
- WebUSB: kan fastbootd/fastboot direct aansturen vanuit browser
- Goed voor het flashen van losse .img files
- Start: telefoon in fastboot → browser-tool → verbind

### Optie C — Officiële recovery + losse images
- Flash officiële LineageOS eerst (herstel)
- Daarna: probeer Stay4OS .img files via fastboot
- Maar: system/vendor/product zitten in super → fastbootd of sideload nodig

## DE DTB-FIX (kritiek)
- Kernel-build boot.img (53MB, met ingebouwde dtb) DIRECT gebruiken
- NIET de AOSP-built boot.img (64MB, lege dtb)
- Verify vóór flash:
```bash
python -c "
import struct
with open('boot.img','rb') as f: d=f.read()
print('grootte:', len(d))
if d[:8]==b'ANDROID!':
    ks=struct.unpack('<I', d[8:12])[0]
    print('kernel:', ks, 'bytes — dtb aanwezig?', ks>100000)
"
```

## CONCLUSIE
Poging 1 faalde op 2 punten:
1. Lege dtb (kernel kon hardware niet vinden)
2. Fastbootd-route i.p.v. ADB sideload

**Poging 2:** kernel boot.img + ADB sideload (via OTA zip of browser-tool).
De telefoon is hersteld naar officiële LineageOS (Droid bezig).

*OpenCode — 22 sep. Definitieve procedure voor Stay4OS-poging 2.*