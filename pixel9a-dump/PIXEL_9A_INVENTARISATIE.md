# Pixel 9a -- Volledige Inventarisatie (20 sep 2026)

## Device Identiteit
| Eigenschap | Waarde |
|-----------|--------|
| Model | Pixel 9a |
| Codename | tegu |
| Brand | google |
| Device | tegu |
| Serial | 57261JEBF18463 |
| SoC | Google Tensor G4 (zumapro) |
| CPU | arm64-v8a (8-core) |
| RAM | 7.5 GB (7497324 kB) |
| Storage | 109 GB totalaal, 3.5 GB gebruikt, 106 GB vrij |
| Display | 1080x2424, density 420 (override 460) |
| Batterij | Li-ion, 78%, 36.0C |
| SIM | Lebara (vodafone NL) |
| WiFi MAC | ee:1b:da:ce:1c:71 |
| WiFi IP | 192.168.8.196 (GL-MT3000 netwerk!) |

## OS & Build
| Eigenschap | Waarde |
|-----------|--------|
| OS | Android 16 (GrapheneOS) |
| Build ID | 2025121201 |
| Build fingerprint | google/tegu/tegu:16/BP4A.251205.006/2025121201:user/release-keys |
| Security patch | 2025-12-05 |
| Build type | user |
| Build tags | release-keys |
| Build user | android-user |
| Kernel | Linux 6.1.158-android14-11-g52976443f3ca aarch64 |
| Bootloader | tegu-16.4-14097580 |
| Radio/baseband | g5300t-250909-251024-B-14326967 |

## Beveiliging
| Eigenschap | Waarde |
|-----------|--------|
| Bootloader | LOCKED (ro.boot.flash.locked = 1) |
| Verified boot | YELLOW (custom key) |
| VBMeta device state | locked |
| VBMeta AVB version | 1.3 |
| VBMeta digest | abac0ad7c0d1336bc491dd12e9f8601f7c03b1987109c44f9bc08b9e65ebce85 |
| VBMeta public key digest | 0508de44ee00bfb49ece32c418af1896391abde0f05b64f41bc9a2dfb589445b |
| SELinux | Enforcing |
| Perf harden | 1 (enabled) |
| Keystore | trusty |
| Attestation brand | google |
| Attestation device | tegu |

## Partities (A/B slot _a actief)
Verified boot hashes (sha256):
- system: 2208f49870d41cfbde17c61877beef65cbab668ac183a90698382ff9ee22f514
- system_ext: 29ed411805c63b9c46672dbafad8d0017e20e3ada98ef4e6a644ddda6b0de3b7
- product: f40f44e4725dc01ec985fff62a0d4c6f96fc842725e56e089be4d836eaf5ace3
- vendor: e09e8a344c251bacda8943b0b6f07bf71b44e850353cbdbd664c4547bf05719a
- vendor_dlkm: bb46169af340701efcd4fc92d0541b069670f5b6bcc9c89765884285135e34a7
- system_dlkm: e699f1cfccdc9e55dda5602c75980535531927257e1e06789bac7e64bcddbb62

OTA partities: abl, bl1, bl2, bl31, boot, dtbo, gcf, gsa, gsa_bl1, init_boot, ldfw, modem, pbl, product, pvmfw, system, system_dlkm, system_ext, tzsw, vbmeta, vendor, vendor_boot, vendor_dlkm, vendor_kernel_boot

## Geinstalleerde GrapheneOS Apps (versies)
| App | Versie |
|-----|--------|
| app.grapheneos.info | 6 |
| app.grapheneos.apps (App Store) | 33 |
| app.grapheneos.camera | 90 |
| app.grapheneos.pdfviewer | 31 |
| app.grapheneos.logviewer | 16 |
| app.grapheneos.setupwizard | 16 |
| app.grapheneos.gmscompat (Sandboxed Play) | 1 |
| app.grapheneos.gmscompat.config | 167 |
| app.grapheneos.gmscompat.lib | 102 |
| app.grapheneos.networklocation | 16 |
| app.grapheneos.carrierconfig2 | 16 |
| app.grapheneos.backup.contacts | 16-5.7 |
| app.grapheneos.AppCompatConfig | 4 |
| app.attestation.auditor | 90 |

## Totale App Inventaris
- Systeem apps: 72
- Third-party apps: 0 (schoon, geen Google Play apps)
- Totaal packages: 218

## Storage
- Geen documenten, foto's, downloads of gebruikersbestanden
- .nomedia files: 5
- .database_uuid files: 3
- Conclusie: verse GrapheneOS installatie, geen gebruikersdata

## Network
- Verbonden met WiFi 192.168.8.196/24 (GL-MT3000 netwerk!)
- Dit betekent dat de GL-MT3000 al actief is en de Pixel 9a erop is verbonden

## Dump Bestanden
Locatie: D:\STAY4S-DATA\pixel9a-dump\
- all_props.txt (32.8KB) -- alle system properties
- package_permissions.txt (330.1KB) -- alle package permissions
- permissions_list.txt (67.6KB) -- alle beschikbare permissions
- fstab.txt (20.2KB) -- filesystem tabel
- mounts.txt (20KB) -- alle mounts
- features.txt (6.2KB) -- hardware features
- disk_usage.txt (4.3KB) -- disk gebruik
- libraries.txt (1.6KB) -- shared libraries
- cmdline.txt (1.1KB) -- kernel command line
- cpuinfo.txt (0.9KB) -- CPU info
- cameras.txt (0.8KB) -- camera info
- Overige: input_devices, sensors, drm_info, build.prop files

## Belangrijk voor AOSP ROM Build
- Device tree codename: tegu
- SoC platform: zumapro (Tensor G4)
- A/B partitioning (slot _a actief)
- Treble enabled
- AVB 1.3 (Android Verified Boot)
- 24 OTA partities inclusief pvmfw (Protected VM firmware)
- Kernel: 6.1.158 (android14-11 branch)
- Bootloader: tegu-16.4-14097580
- Security patch level: 2025-12-05