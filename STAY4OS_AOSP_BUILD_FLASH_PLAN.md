# Stay4OS AOSP BUILD + FLASH MASTER PLAN
# Door: Droid -- 21 sep 2026, 04:30Z
# Status: LIVE -- repo sync draait op nieuwe pod (roxkzdxoy8jkwv)

## 1. HOE GAAT HET?

### Wat draait nu:
- Nieuwe AOSP build pod: roxkzdxoy8jkwv (RTX 4090, 300GB disk, 12 vCPU, 62GB RAM, $0.74/h)
- Oude pod (hsvk5co7mhze6b): gestopt, root disk was vol (100GB AOSP op 100GB disk)
- Repo sync: draait in background op /workspace/lineage (network volume, 1TB)
- Java 17, repo tool, ccache (50GB), ADB, fastboot: allemaal geinstalleerd
- Signing keys: 6 stuks op /workspace/stay4os-keys/ (blijven bewaard)
- 15 repo processen actief, ~1.4GB gedownload, groeiend

### Wat is klaar:
- stay4os-tegu GitHub repo met device tree, makefiles, lunch targets, flash guide
- LineageOS tegu device tree gevonden (LineageOS/android_device_google_tegu)
- Dependencies bekend: tegu + zumapro + tegu-kernels
- Build instructies gelezen van LineageOS wiki
- Brand spec, ROM feature spec, bootloader unlock guide: allemaal klaar

### Wat nog moet:
- Repo sync voltooien (~1-2u, 100GB+ source)
- Vendor blobs extraheren van Pixel 9a (MITCHELL vereist)
- stay4os-tegu overlay integreren in source tree
- Build starten: breakfast tegu -> brunch tegu (4-8u)
- Flashen op Pixel 9a (MITCHELL vereist)

## 2. HOE DOEN WE HET?

### Build pipeline (automatisch, Droid doet dit):

Stap 1: REPO SYNC (nu draaiend)
  cd /workspace/lineage
  repo sync -j8
  # Downloadt ~100GB LineageOS lineage-23.2 source + tegu device tree + zumapro + kernels
  # ETA: 1-2 uur

Stap 2: STAY4OS OVERLAY INTEGREREN
  # Clone onze stay4os-tegu repo
  cd /workspace/lineage
  git clone https://github.com/hetnieuwebeginbv-glitch/stay4os-tegu /tmp/stay4os-tegu
  # Kopieer device tree naar juiste locatie
  cp -a /tmp/stay4os-tegu/device/google/tegu-stay4os device/google/
  # Kopieer vendor overlay
  mkdir -p vendor/stay4os
  cp -a /tmp/stay4os-tegu/vendor/stay4os/stay4os-tegu.mk vendor/stay4os/
  # Maak stay4os.mk basis (voor inherit-product)
  cat > vendor/stay4os/stay4os.mk << 'EOF'
  # Stay4S common vendor config
  PRODUCT_PACKAGES += Stay4SAI
  EOF

Stap 3: VENDOR BLOBS EXTRAHEREN (MITCHELL vereist!)
  # Optie A: Mitchell verbindt Pixel 9a met laptop, draait op laptop:
  cd ~/android/lineage/device/google/tegu  # (of lokaal op laptop)
  ./extract-files.py
  # Dit trekt vendor blobs van de telefoon naar vendor/google/tegu/
  # Daarna uploaden naar pod via runpodctl send of rsync

  # Optie B: Blobs uit stock firmware zip halen
  # Zie: https://wiki.lineageos.org/extracting_blobs_from_zips.html

Stap 4: BUILD STARTEN
  cd /workspace/lineage
  source build/envsetup.sh
  breakfast tegu                          # Configureert voor tegu
  lunch stay4os_tegu-userdebug            # Onze Stay4S product
  export USE_CCACHE=1
  export CCACHE_EXEC=/usr/bin/ccache
  mka bacon -j12                          # Full build (4-8 uur)

Stap 5: BUILD OUTPUT OPHALEN
  cd $OUT
  # Belangrijkste bestanden:
  # - lineage-23.2-YYYYMMDD-UNOFFICIAL-tegu.zip (ROM installer)
  # - vendor_boot.img (recovery image)
  # - boot.img, dtbo.img, vendor_kernel_boot.img

Stap 6: SIGNING (optioneel, met onze keys)
  # Build kan worden gesigned met onze 6 signing keys
  # Zie: https://wiki.lineageos.org/signing_builds.html

## 3. WAT HEBBEN WE NODIG?

### Op de pod (allemaal geinstalleerd):
- [x] Java 17 (OpenJDK 17.0.15)
- [x] repo tool (v2.65)
- [x] ccache (50GB, compression aan)
- [x] ADB + fastboot
- [x] Alle build dependencies
- [x] 300GB container disk
- [x] Network volume (1TB) voor source persistence
- [x] 6 AOSP signing keys

### Van Mitchell vereist:
- [ ] VENDOR BLOBS: Pixel 9a via USB verbinden, extract-files.py draaien
  OF: stock firmware downloaden en blobs daaruit halen
- [ ] GO voor build start (kost ~$3-6 aan pod kosten, 4-8u)
- [ ] Pixel 9a voor flash procedure

### Van OpenCode (niet storend):
- [ ] Niets - OpenCode is bezig met LoRA + Cyc7 + datagen
- [ ] OpenCode hoeft NIETS te doen voor AOSP build
- [ ] Alleen rapporteren via SHARED_STATE

## 4. WAT ALS HIJ GEFLASHT IS?

### Na succesvolle flash:

1. EERSTE BOOT
   - Stay4OS boot op Pixel 9a
   - Setup wizard (of skip)
   - GrapheneOS-achtige privacy features actief

2. STAY4S AI ACTIVEREN
   - llama-server draait als init service (stay4s_ai.rc)
   - Qwen3-4B model geladen uit /system/app/Stay4SAI/
   - AI accessible via local API op 127.0.0.1:8888
   -聊天 interface via Stay4S app (Grok app omgebouwd)

3. FUNCTIONALITEIT TESTEN
   - WiFi, Bluetooth, GPS, camera, sensors
   - AI chat (Qwen3-4B @ 8 tok/s)
   - VPN (WireGuard via GL-MT3000)
   - Battery life met AI actief

4. STAY4S ECOSYSTEM KOPPELEN
   - Tailscale verbinding met Pi 5
   - WhatsApp AI webhook (via Pi 5)
   - Stay4Safe scam detector
   - Stay4Compa agent
   - E2EE vault

### Wat werkt na flash:
- Eigen OS op eigen telefoon
- Eigen AI (Qwen3-4B) lokaal op device
- Privacy-first (geen Google apps, geen tracking)
- Stay4S branding (kleuren, logo, boot animatie)
- VPN via WireGuard
- Verbonden met Stay4S ecosystem via Tailscale

### Wat nog niet werkt (toekomst):
- Eigen LoRA model (OpenCode traint nu, ~5u rest)
- AOSP custom launcher (spec klaar, nog bouwen)
- Custom settings UI (spec klaar, nog bouwen)
- Meshtastic LoRa (hardware vereist)

## 5. WIE DOET WAT TIJDENS FLASH?

### Droid (autonoom, voor flash):
- Repo sync voltooien
- Stay4OS overlay integreren
- Build starten en monitoren
- Build output verifiëren
- Flash guide documenteren
- ZIP + images uploaden naar network volume

### Mitchell (vereist voor flash):
- Vendor blobs extraheren van Pixel 9a (USB verbinding)
- Bootloader unlock (als nog niet gedaan)
- Flash procedure uitvoeren op laptop:
    adb reboot bootloader
    fastboot flashing unlock
    fastboot flash boot boot.img
    fastboot flash dtbo dtbo.img
    fastboot flash vendor_kernel_boot vendor_kernel_boot.img
    fastboot reboot bootloader
    fastboot flash vendor_boot vendor_boot.img
    # recovery: format data
    adb sideload stay4os-tegu.zip
- Eerste boot verifiëren
- Functionele test uitvoeren

### OpenCode (niet storen):
- Blijft trainen: LoRA Qwen3-4B (~5u rest), Cyc7 (13%), datagen (15.415 records)
- Levert LoRA GGUF als klaar -> Droid test op Pixel 9a
- Rapporteert via SHARED_STATE

## 6. DOE IK ALLES OF SAMEN MET OPENCODE?

### Droid doet alleen:
- AOSP build (volledig autonoom)
- Build monitoring
- Pixel 9a AI setup en testing
- Pi 5 services
- GitHub commits
- SHARED_STATE logging

### OpenCode doet alleen:
- AI training (LoRA, Cyc7, datagen)
- Training scripts
- Model conversie (GGUF)
- Eval scripts

### Samen (via SHARED_STATE):
- Status rapportages
- Beslissingen (via Mitchell)
- Eval resultaten delen
- Model testing (OpenCode levert, Droid test op Pixel)

### Mitchell doet:
- GO/NGO beslissingen
- Vendor blobs extractie
- Flash procedure
- Budget bewaking
- Prompts doorsturen naar andere AIs

## 7. KOSTEN

### AOSP Build pod (roxkzdxoy8jkwv):
- RTX 4090: $0.74/h
- Build tijd: ~4-8 uur
- Totale build kost: $3-$6
- Sync tijd: ~1-2 uur = $0.74-$1.48
- Totaal: ~$4-$8

### OpenCode pods (6 stuks):
- 5x $0.72/h + 1x $0.74/h = $4.34/h
- OpenCode blijft ongestoord draaien

### Totaal RunPod nu:
- 7 pods: $5.08/h (was $5.19/h met A100, nu $0.74/h met RTX 4090)
- Besparing: $0.85/h door van A100 naar RTX 4090 te gaan

## 8. TIJDLIJN

| Tijd | Taak | Wie |
|------|------|-----|
| Nu | Repo sync draait (1.4GB/100GB+) | Droid |
| +1-2u | Sync compleet | Droid |
| +15min | Stay4OS overlay integreren | Droid |
| WACHTEN | Vendor blobs extractie | Mitchell |
| +4-8u | Build starten (mka bacon) | Droid |
| +30min | Build output verifiëren | Droid |
| WACHTEN | Flash procedure | Mitchell |
| +30min | Eerste boot + test | Mitchell + Droid |

### Totale tijd tot Stay4OS op Pixel 9a:
- Zonder vendor blobs wachttijd: ~6-10 uur
- Met Mitchell's actieve deelname: ~8-12 uur