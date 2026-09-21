# Stay4OS ROM v1.0 -- Feature Specification
# Pixel 9a (tegu) -- Based on LineageOS 23.2 (Android 16)

## Core Principles
1. **Privacy First** -- Geen Google telemetry, geen ongewenste data collection
2. **Eigen AI** -- Qwen3-4B ingebakken, werkt volledig offline
3. **Stay4S Ecosystem** -- Alle Stay4S services geintegreerd
4. **Security** -- GrapheneOS-level hardening behouden
5. **Open Source** -- Alles bouwbaar from source

## System Features

### 1. Stay4S AI (System App)
- **Model:** Qwen3-4B-Instruct-2507 Q4_K_M (2.5GB)
- **Engine:** llama.cpp llama-server (ARM64 native)
- **API:** OpenAI-compatible op 127.0.0.1:8888
- **Auto-start:** Bij boot via init service (stay4s_ai.rc)
- **RAM:** ~3GB (model + context + compute)
- **Snelheid:** 6-8 tok/s op Tensor G4
- **Taal:** Nederlands (system prompt)
- **Fallback:** eigen-cyc6-sft-q4 (1.0GB) bij primary falen
- **Chat interface:** Simpele Terminal UI in Termux
- **Logging:** Alle conversaties opgeslagen voor training data

### 2. Stay4S Launcher
- Eigen launcher (geen Google Launcher)
- Directe toegang tot: AI, WhatsApp service, Vault, Settings
- Cyan accent kleuren (#00D9FF)
- Dark mode default
- Minimalistische iconen
- Geen app drawer (alleen geinstalleerde apps op homescreen)

### 3. Stay4S Safe (System App)
- Scam detector AI
- Real-time SMS/WhatsApp bericht analyse
- 10 scam indicator categories
- Weighted scoring 0-100
- Waarschuwing bij HOOG risico
- Werkt offline (geen cloud)

### 4. Stay4S Compa (System App)
- Self-hosted AI agent
- 10 tools (weather, calc, translate, scam check, etc.)
- 3 workflows (klantenservice, scam check, daily report)
- Memory system per user
- Ollama backend (qwen3:1.7b of Qwen3-4B)

### 5. Stay4S Vault (System App)
- E2EE document opslag
- AES-256-GCM encryptie
- JWT authenticatie
- Secure delete (DoD 5220.22-M)
- Audit log
- Invite tokens voor sharing

### 6. WireGuard VPN (System App)
- Ingebouwd in settings
- Auto-connect bij boot
- Config import via QR code
- Kill switch
- Eigen Stay4S VPN profiel

### 7. Privacy Hardening
- Geen Google Play Services (of sandboxed zoals GrapheneOS)
- Geen Google telemetry/analytics
- Geen Google location sharing
- Eigen DNS (Pi-hole/AdGuard compatible)
- SELinux enforcing (behouden)
- Verified boot met Stay4S signing keys
- App permissions stricter (GrapheneOS style)
- Network permissions toggle per app
- Sensors toggle per app

### 8. Stay4S Branding
- **Boot animation:** Cyan "Stay4OS" tekst fade-in + pulse effect
- **Boot sound:** Soft electronic chime (3 ascending notes)
- **Wallpapers:** 3 wallpapers (Ocean Deep, Starfield, Circuit)
- **Icons:** Rounded squares, cyan accent
- **Font:** Roboto system + Inter Bold voor branding
- **Settings:** "Powered by Stay4S AI" header, Stay4S in About
- **Lock screen:** Minimal cyan clock, AI quick access (swipe left)

### 9. Removed Google Apps
- Chrome -> Fenix (Firefox) of eigen browser
- Gmail -> Eigen mail client
- YouTube -> NewPipe of eigen
- Google Maps -> Organic Maps
- Google Calendar -> Eigen calendar
- Google Assistant -> Stay4S AI
- Google Play Store -> GrapheneOS App Store (F-Droid based)
- Google Photos -> Eigen gallery
- Google Drive -> Stay4S Vault

### 10. Pre-installed Apps
- Termux (voor AI chat access)
- Signal (messaging)
- Organic Maps (offline maps)
- NewPipe (video)
- Fennec (Firefox browser)
- K-9 Mail (email)
- Simple Gallery (photos)
- Stay4S AI Chat (eigen)
- Stay4S Safe (scam detector)
- Stay4S Vault (E2EE opslag)
- WireGuard (VPN)

### 11. System Properties
```
ro.stay4s.version=1.0
ro.stay4s.ai.model=qwen3-4b-instruct-2507
ro.stay4s.ai.quant=q4_k_m
ro.stay4s.ai.tokens_per_sec=8
persist.stay4s.ai.enabled=true
persist.stay4s.ai.port=8888
persist.stay4s.privacy.mode=strict
persist.stay4s.wireguard.enabled=true
```

### 12. Partition Layout
- A/B partitions (behouden van Pixel 9a)
- system: ~4GB (AOSP + Stay4S apps)
- vendor: ~2GB (Tensor G4 blobs)
- product: ~1GB (Stay4S branding)
- system_ext: ~500MB
- Eigen vbmeta signing

## Build Variants
1. **stay4os_tegu** -- Full Stay4OS (alle features)
2. **stay4os_tegu_minimal** -- Alleen AI + privacy hardening (geen Stay4S apps)
3. **stay4os_tengu_dev** -- Developer build (adb root, debuggable)

## Testing Checklist
- [ ] Boot op Pixel 9a
- [ ] Stay4S AI start automatisch
- [ ] Chat werkt in Nederlands
- [ ] Scam detector werkt
- [ ] Vault encryptie werkt
- [ ] WireGuard connect
- [ ] SELinux enforcing
- [ ] Verified boot yellow (eigen keys)
- [ ] Geen Google crashes
- [ ] Batterijduur acceptabel (>12h standby)
- [ ] RAM usage < 6GB (laat 2GB voor apps)