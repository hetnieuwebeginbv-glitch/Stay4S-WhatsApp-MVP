# Stay4OS ROM Build Plan -- Pixel 9a (tegu)
# Door: Droid (Architect of Record)
# Datum: 21 september 2026

## CRUCIALE ONTDEKKING

Google heeft alle Pixel device trees uit AOSP verwijderd vanaf Android 16.
Dit betekent dat vanilla AOSP NIET kan bouwen voor tegu zonder externe device tree.

Maar er zijn twee projecten die WEL tegu ondersteunen:
1. **LineageOS** -- officiële ondersteuning voor tegu (lineage-23.0, lineage-23.2)
2. **GrapheneOS** -- de Pixel 9a draait AL op GrapheneOS

## STRATEGIE KEUZE

### Optie A: LineageOS als base (aanbevolen voor flexibiliteit)
- Voordelen: officiële tegu device tree, grote community, makkelijk aan te passen
- Nadelen: minder security hardening dan GrapheneOS
- Device tree: github.com/LineageOS/android_device_google_tegu
- Kernel: github.com/LineageOS/android_kernel_google_gs-6.1_manifest
- Branch: lineage-23.2 (Android 16 based)
- Build: `breakfast tegu && brunch tegu`

### Optie B: GrapheneOS als base (aanbevolen voor security)
- Voordelen: beste security hardening, device draait er al op, eigen signing keys
- Nadelen: minder documentatie voor custom builds, strikter licensing
- Repo: github.com/GrapheneOS/platform_manifest
- Branch: 16 (Android 16)
- Device: tegu (al ondersteund)

### Optie C: Hybride (BESTE)
- Start met LineageOS device tree + kernel
- Neem GrapheneOS security patches (SELinux, hardened_malloc, etc)
- Voeg Stay4S customisaties toe
- Eigen signing keys

## AANBEVELING: Optie C (Hybride)

## BUILD REQUIREMENTS

| Requirement | Minimum | Aanbevolen | RunPod optie |
|------------|---------|------------|--------------|
| RAM | 64 GB | 128 GB | ACM Elite (96GB) of custom |
| Storage | 400 GB | 500 GB | Network volume 500GB |
| CPU | 8 cores | 16 cores | 16 vCPU |
| OS | Ubuntu 22.04 | Ubuntu 24.04 | RunPod Ubuntu template |
| Python | 3.10+ | 3.12 | Pre-installed |
| Java | OpenJDK 17+ | In source tree | Auto |
| ccache | 50 GB | 100 GB | Op network volume |

## BUILD ENVIRONMENT SETUP (RunPod)

### Stap 1: RunPod pod aanmaken
- Template: Ubuntu 22.04 met CUDA
- GPU: Niet strikt nodig voor AOSP build, maar CPU pods zijn goedkoper
- RAM: Minimum 64GB (liefst 96-128GB)
- Storage: 500GB network volume + pod disk
- Ports: 22 (SSH), 8080 (web)

### Stap 2: Build packages installeren
```bash
apt update && apt install -y bc bison build-essential ccache curl erofs-utils flex \
  g++-multilib gcc-multilib git git-lfs gnupg gperf imagemagick protobuf-compiler \
  python3-protobuf lib32readline-dev lib32z1-dev libdw-dev libelf-dev libgnutls28-dev \
  lz4 libsdl1.2-dev libssl-dev libxml2 libxml2-utils lzop pngcrush rsync schedtool \
  squashfs-tools xsltproc xxd zip zlib1g-dev python-is-python3 openjdk-17-jdk
```

### Stap 3: repo tool installeren
```bash
mkdir -p ~/bin
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
chmod a+x ~/bin/repo
export PATH=~/bin:$PATH
git config --global user.email "stay4s@gmail.com"
git config --global user.name "Stay4S"
git lfs install
```

### Stap 4: Source tree initialiseren
```bash
mkdir -p ~/android/stay4os
cd ~/android/stay4os

# Optie A: LineageOS base
repo init -u https://github.com/LineageOS/android.git -b lineage-23.2 --git-lfs --no-clone-bundle

# Optie B: GrapheneOS base
# repo init -u https://github.com/GrapheneOS/platform_manifest.git -b 16
```

### Stap 5: Source sync (dit duurt 1-3 uur)
```bash
repo sync -j4 -c --no-clone-bundle
```

### Stap 6: Device tree ophalen
```bash
source build/envsetup.sh
breakfast tegu
```

### Stap 7: Vendor blobs extraheren
```bash
# Vanuit device directory
cd device/google/tegu
./extract-files.sh  # Pixel 9a via adb verbonden
# OF: download van LineageOS blobs repo
```

### Stap 8: ccache configureren
```bash
export USE_CCACHE=1
export CCACHE_EXEC=/usr/bin/ccache
ccache -M 100G
ccache -o compression=true
```

### Stap 9: Build starten
```bash
croot
brunch tegu
# Build duurt 4-8 uur afhankelijk van CPU en RAM
```

### Stap 10: Output
```bash
cd $OUT
# Belangrijkste files:
# - vendor_boot.img (recovery)
# - lineage-23.2-YYYYMMDD-UNOFFICIAL-tegu.zip (installer)
# - boot.img, system.img, vendor.img, etc.
```

## STAY4S CUSTOMISATIES

### Te toevoegen aan device tree:
1. **Stay4S AI App** (prebuilt system app)
   - llama.cpp binary (ARM64, gecompileerd voor Tensor G4)
   - Qwen3-4B-Instruct-2507 Q4_K_M model (2.5GB, in /system/app/Stay4SAI/)
   - Chat interface (simplified Termux-based)
   - Auto-start bij boot

2. **Stay4S Launcher**
   - Eigen launcher met Stay4S branding
   - Directe toegang tot AI, WhatsApp service, Vault
   - Geen Google app drawer

3. **Privacy Hardening** (van GrapheneOS overnemen)
   - Geen Google telemetry
   - Geen Google Play Services (of sandboxed zoals GrapheneOS)
   - Eigen DNS (Pi-hole / AdGuard)
   - WireGuard VPN ingebouwd
   - SELinux enforcing (behouden)
   - Verified boot met eigen keys

4. **Stay4S Apps** (prebuilt)
   - Stay4Safe AI (scam detector)
   - Stay4Compa agent
   - E2EE Vault client
   - WhatsApp AI klantenservice

5. **Branding**
   - Boot animation (Stay4S logo)
   - Wallpaper pack
   - Eigen icon set
   - Settings branding

### Implementatie in makefiles:
```makefile
# device/google/tegu/stay4s.mk
PRODUCT_PACKAGES += \
    Stay4SAI \
    Stay4SLauncher \
    Stay4SSafe \
    Stay4SCompa \
    Stay4SVault \
    WireGuard

PRODUCT_COPY_FILES += \
    vendor/stay4s/app/Stay4SAI/llama-server:system/app/Stay4SAI/lib/arm64/llama-server \
    vendor/stay4s/models/qwen3-4b-q4_k_m.gguf:system/app/Stay4SAI/models/qwen3-4b-q4_k_m.gguf

PRODUCT_SYSTEM_PROPERTIES += \
    ro.stay4s.version=1.0 \
    ro.stay4s.ai.model=qwen3-4b \
    persist.stay4s.ai.enabled=true
```

## EIGEN SIGNING KEYS

```bash
# Genereer signing keys
. build/envsetup.sh
brunch tegu  # first build with test keys

# Daarna eigen keys maken:
mkdir -p ~/.android-certs
for cert in releasekey platform shared media networkstack sdk_sandbox; do
    make_key ~/.android-certs/$cert '/CN=Stay4S/'
done

# Build met eigen keys:
export SIGNING_KEY_DIR=~/.android-certs
brunch tegu
```

## FLASH PROCEDURE

```bash
# Bootloader unlock (vernietigt alle data!)
adb reboot bootloader
fastboot flashing unlock
# Bevestig op device

# Flash ROM
fastboot flash boot boot.img
fastboot flash system system.img
fastboot flash vendor vendor.img
fastboot flash vendor_boot vendor_boot.img
fastboot flash product product.img
fastboot flash system_ext system_ext.img
fastboot flash vbmeta vbmeta.img --disable-verity --disable-verification

# Reboot
fastboot reboot
```

## TIJDLIJN

| Fase | Duur | Wat |
|------|------|-----|
| 1. RunPod setup | 30 min | Pod aanmaken, packages installeren |
| 2. Source sync | 1-3 uur | repo sync (30-50GB download) |
| 3. Device tree | 30 min | breakfast tegu, extract blobs |
| 4. Eerste build | 4-8 uur | brunch tegu (vanilla) |
| 5. Test flash | 30 min | Flash naar Pixel 9a, testen |
| 6. Stay4S mods | 2-4 uur | Custom makefiles, apps, branding |
| 7. Stay4S build | 4-8 uur | Opnieuw bouwen met customisaties |
| 8. Final test | 1 uur | Flash Stay4OS, alle features testen |

Totaal: ~12-24 uur (verspreid over meerdere dagen)

## VOLGENDE STAPPEN (autonoom)

1. RunPod pod aanmaken met 64GB+ RAM (via runpod-mcp)
2. Build packages installeren
3. repo init + sync starten
4. Device tree voor tegu ophalen
5. Vendor blobs extraheren van Pixel 9a (via adb)
6. Eerste vanilla build testen
7. Stay4S customisaties toevoegen
8. Stay4OS ROM bouwen

## RISICO'S

- Google device trees uit AOSP verwijderd -- opgelost via LineageOS
- Vendor blobs nodig -- extraheer van Pixel 9a via adb
- Build kan falen -- eerste build is altijd vanilla test
- Bootloader unlock vernietigt data -- backup eerst!
- Eigen keys vereist voor verified boot -- generate na eerste build