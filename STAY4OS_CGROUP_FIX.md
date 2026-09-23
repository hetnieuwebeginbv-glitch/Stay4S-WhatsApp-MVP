# STAY4OS v5 CGROUP-FIX (klaar — 23 sep)

## Wat er gefixt is
De kernel-cmdline in `vendor_boot.img` bevatte de GrapheneOS-flags:
```
cgroup_disable=memory   cgroup.memory=nokmem
```
Deze breken Android's init (memory-cgroups vereist voor app-UID-paden) → bootloop
(106× "Activation of cgroup controller +memory failed: Invalid argument").

## De fix (toegepast + geverifieerd)
```
D:\STAY4S-DATA\stay4os-rom\v5\vendor_boot_fixed.img   (64MB)
```
- `cgroup_disable=memory` verwijderd ✓
- `cgroup.memory=nokmem` verwijderd ✓
- `bootconfig` keyword intact ✓
- Rest van cmdline intact ✓
- sha256: a1f9de492174d64a... (orig: 22c4e8de7183e5ef...)

## Flash-route (met fix)
```bash
# 1. Boot images flashen (met de GEFIXTE vendor_boot)
fastboot flash boot boot.img
fastboot flash dtbo dtbo.img
fastboot flash vendor_kernel_boot vendor_kernel_boot.img
fastboot flash vendor_boot vendor_boot_fixed.img
fastboot reboot recovery

# 2. In recovery: Factory reset -> Format data
# 3. Apply update -> Apply from ADB
adb sideload D:\STAY4S-DATA\stay4os-rom\v5\stay4os_tegu-ota.zip
# 4. Reboot system
```

## Script
- `fix_vendor_boot_cgroup.py` — patcht vendor_boot.img (vervangt cgroup-flags door spaces, zelfde lengte)
- `inspect_bootimg.py` — vindt cmdline/bootconfig in boot-images
- `verify_fix.py` — verifieert dat de cgroup-flags weg zijn

## Let op
- De cmdline zit op offset 147-183 in vendor_boot.img (vlak na "experimental=Y")
- De `vendor_kernel_boot.img` had géén cgroup-flags (alleen console=)
- De boot.img had géén cgroup-flags (alleen bootconfig op 16156802)
- Alleen vendor_boot.img moest gefixt worden

*OpenCode — 23 sep 2026. Op basis van STAY4OS_BOOTLOOP_DIAGNOSE_v5.md.*