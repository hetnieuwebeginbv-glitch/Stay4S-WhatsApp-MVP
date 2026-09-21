# Stay4S GitHub Repo Inventarisatie -- 21 sep 2026
# Door: Droid -- Alle 45 repos uitgelezen en gecategoriseerd

## CATEGORIE 1: ACTIEF -- AOSP / Stay4OS ROM Build (direct nodig)

### stay4os-tegu -- BESTAAT AL! CRUCIAAL
- URL: github.com/hetnieuwebeginbv-glitch/stay4os-tegu
- Branch: main
- Inhoud: device/google/tegu-stay4os/ (AndroidProducts.mk + stay4os_tegu.mk)
- Inhoud: vendor/stay4os/stay4os-tegu.mk (Tensor G4 props, screen 1080x2424)
- Inhoud: docs/FLASH-TEGU.md (flash instructies), docs/OPENCODE-DROID-BOUWER.md
- Lunch target: `stay4os_tegu-userdebug`
- Build: `breakfast tegu` -> `lunch stay4os_tegu-userdebug` -> `mka bacon`
- STATUS: Bestaat al met werkende makefiles! Kan direct in AOSP build worden gebruikt.

### Stay4S-WhatsApp-MVP -- Droid's hoofdrepo
- URL: github.com/hetnieuwebeginbv-glitch/Stay4S-WhatsApp-MVP
- Branch: master, 20+ commits vandaag
- Inhoud: Alle Pi 5 scripts + Pixel 9a scripts + AOSP docs
- Belangrijk voor AOSP: stay4s-ai.sh, stay4s-chat-log.sh, STAY4OS_AOSP_BUILD_PLAN.md,
  STAY4OS_ROM_FEATURE_SPEC.md, STAY4OS_BRAND_SPEC.md, PIXEL_9A_BOOTLOADER_UNLOCK.md,
  stay4os_build.sh, extract_tegu_blobs.sh, pixel9a-dump/ (14 files)
- STATUS: ACTIEF, door Droid beheerd

### stay4os-docs -- Governance Hub
- URL: github.com/hetnieuwebeginbv-glitch/stay4os-docs
- Branch: main
- Inhoud: SHARED_STATE.json, STATE_SNAPSHOT.md, DECISIONS_LOG.md, WERKLOG.md,
  AOSP_MEESTERCOORDINATOR_PROMPT.md, alle architectuur docs
- STATUS: ACTIEF, Source of Truth voor hele project

## CATEGORIE 2: ACTIEF -- AI Training (OpenCode)

### Stay4LM-train -- Training Pipeline
- URL: github.com/hetnieuwebeginbv-glitch/Stay4LM-train
- Branch: master
- Scripts: chatlog_to_sft.py (converteert chat-log .txt naar SFT JSONL!),
  preflight.sh, newrun.sh, backup.sh, gcs_offload.sh, run_training.sh, install.sh
- Templates: training configs
- STATUS: ACTIEF, OpenCode gebruikt dit voor LoRA + Cyc7 + datagen

### stay4s-ai-board -- Coordinatiebord
- URL: github.com/hetnieuwebeginbv-glitch/stay4s-ai-board
- Inhoud: BOARD.md, LOG.md, AGENTS.md, ISSUES.md (31), DECISIONS.md, SUPERPROMPT_MASTERSTATUS.md
- 10 teamleden: Mitch, Stay4Compa, Droid, OpenCode, Codex, ChatGPT, Grok browser, Grok PowerShell, RunpodOps, Claude
- STATUS: ACTIEF, kanaal 2 voor team communicatie

## CATEGORIE 3: REFERENTIE -- Nothing Phone (asteroids) device tree

### android_device_nothing_asteroids -- COMPLETE referentie device tree
- URL: github.com/hetnieuwebeginbv-glitch/android_device_nothing_asteroids
- Inhoud: BoardConfig.mk, device.mk, lineage_asteroids.mk, stay4s_asteroids.mk,
  stay4s_grok_common.mk, stay4s_grok_edition.mk, extract-files.py,
  proprietary-files.txt, proprietary-firmware.txt, sepolicy/, sensors/, audio/,
  configs/, rootdir/, vibrator/, euicc/, modules/, overlay-lineage/, rro_overlays/
- BUILD_NOTES.md, FLASH_CHECKLIST.md, STAY4S_BUILD_REVIEW.md, STAY4S_ROADMAP.md
- STATUS: REFERENTIE voor tegu device tree (zelfde structuur nodig)

### android_vendor_nothing_asteroids -- Vendor blobs (PRIVATE)
- URL: github.com/hetnieuwebeginbv-glitch/android_vendor_nothing_asteroids
- STATUS: Referentie voor vendor blob structuur

### device_nothing_asteroids -- Alternative device tree
- URL: github.com/hetnieuwebeginbv-glitch/device_nothing_asteroids
- STATUS: Referentie

### GrokPhone-OS -- Meta repo met build scripts
- URL: github.com/hetnieuwebeginbv-glitch/GrokPhone-OS
- Scripts: build-stay4os.ps1 (PowerShell build), setup-build-env.sh (Ubuntu setup)
- .repo/ directory met local manifests
- STATUS: Referentie voor build scripts (ons stay4os_build.sh is beter)

## CATEGORIE 4: REFERENTIE -- Android Apps voor AOSP

### android_packages_apps_Grok -- Grok Agent App
- URL: github.com/hetnieuwebeginbv-glitch/android_packages_apps_Grok
- Inhoud: Android.bp, AndroidManifest.xml, aidl/, res/, src/com/
- Privileged AI agent voor Stay4OS
- STATUS: Kan worden aangepast voor tegu (vervang Grok door Stay4S AI)

### android_packages_apps_AetherCore -- AI Orchestrator
- URL: github.com/hetnieuwebeginbv-glitch/android_packages_apps_AetherCore
- Inhoud: Android.bp, AndroidManifest.xml, aidl/, src/com/
- On-device AI orchestrator
- STATUS: Kan worden gebruikt als basis voor Stay4S AI system app

## CATEGORIE 5: ACTIEF -- Agent Platform

### Stay4S-Factory -- Agent Factory
- URL: github.com/hetnieuwebeginbv-glitch/Stay4S-Factory
- Inhoud: agents/, gateway/, hoofdagent/, docker-compose.yml, sql/, docs/
- WhatsApp Cloud API v23 + LangGraph hoofdagent + factory + GitHub PR-reviewer
- STATUS: ACTIEF (maar Pi 5 versie is meer actueel)

### Stay4S-hoofdagent -- AI Hoofdkwartier
- URL: github.com/hetnieuwebeginbv-glitch/Stay4S-hoofdagent
- Inhoud: WhatsApp berichtcentrum + hoofdagent (LangGraph) + agent factory + InfoVault
- STATUS: Referentie voor Pi 5 Stay4Compa

### Stay4Compa-Mini -- Soevereine AI Assistent
- URL: github.com/hetnieuwebeginbv-glitch/Stay4Compa-Mini
- Inhoud: app/, mini/, data/, evals/, tests/, SPEC.md, INVENTORY.md, CODING_LOG.md
- STATUS: ACTIEF referentie

### Stay4S-Agent -- Minimal AI assistant
- URL: github.com/hetnieuwebeginbv-glitch/Stay4S-Agent
- Inhoud: openai-agents SDK based
- STATUS: Referentie

### Stay4S-Intelligence -- Prompt Suite
- URL: github.com/hetnieuwebeginbv-glitch/Stay4S-Intelligence
- Inhoud: Prompt schemas, templates
- STATUS: Referentie voor AI prompts

## CATEGORIE 6: ACTIEF -- Nexus Platform

### Stay4S-Nexus -- Enterprise Intelligence Platform
- URL: github.com/hetnieuwebeginbv-glitch/Stay4S-Nexus
- Inhoud: Rust (Cargo.toml), nexus/, nexus_core/, server/, connectors/, plugins/,
  contracts/, centers/, cps/, clients/, shared/, architecture/, adr/, docs/, tests/
- 33 commits, echte axum HTTP server
- STATUS: ACTIEF (maar niet direct nodig voor AOSP)

## CATEGORIE 7: ARCHIEF / SUPERSEDED

### Stay4S-app -- SUPERSEDED
- Beschrijving: "SUPERSEDED 9 sep 2026: GrapheneOS-basis vervangen door AOSP-besluit"
- STATUS: ARCHIEF, niet bouwen

### Stay4S-Pixel -- SUPERSEDED
- Beschrijving: "SUPERSEDED 9 sep 2026: GrapheneOS-basis vervangen door AOSP-besluit"
- STATUS: ARCHIEF, referentie-only

### Stay4S-LocationGuard -- GEPAUZEERD
- Beschrijving: "GPS Kill Switch, kandidaat-module voor toekomstige AOSP-ROM"
- STATUS: Referentie, kan later in Stay4OS worden geintegreerd

### Stay4S-System-Verslag -- Referentie
- Beschrijving: "Volledig systeemverslag + 18 Grok-superprompts"
- STATUS: Archief van prompts

## CATEGORIE 8: MIRRORS (backup only, niet canonical)

- mirror-carlyle-felix-android_kernel_nothing_sm7635
- mirror-carlyle-felix-android_kernel_nothing_sm7635-modules
- mirror-carlyle-felix-android_kernel_nothing_sm7635-devicetrees
- mirror-NullDebris-proprietary_vendor_nothing_asteroids
- mirror-NullDebris-packages_apps_ParanoidGlyph
- mirror-NullDebris-packages_apps_GlyphAdapter
- mirror-NullDebris-hardware_dolby
- STATUS: Read-only backups, niet gebruiken als bron

## CATEGORIE 9: OVERIGE (niet direct relevant)

| Repo | Status |
|------|--------|
| hetnieuwebeginbv-glitch | Profile repo |
| Stay4S-All | Ultra-metarepo (submodules) |
| nothing-phone-3a-recovery | Recovery toolkit |
| Connect4opem | Fork OpenConnector |
| Stay4S-SAIP | Onbekend |
| android_kernel_nothing_sm7635 | Kernel mirror |
| GrokPhone_Integrated | Integration superproject |
| Stay4Grok | Privacy-first AI smartphone concept |
| stay4s-grokrom | Own grokphone |
| repit-recovery | Replit recovery |
| Drive-Recovery | Replit drive recovery |
| Stay4S-Grok | Stay4S-Grok |
| Stay4S | Phone |
| stay4safe-ai | Stay4Safe AI (.github only) |
| stay4s-grok-edition | Grok Edition concept |
| M-Ai-Phone | Ai Manus Phone |
| stay4s-grokphone-flexbank | ARCHIEF-KANDIDAAT |
| echo-infinite-reality | AI game (niet Stay4S) |
| Multiagent | Circlelair (niet Stay4S) |
| ai-guard | Ai guard (niet Stay4S) |
| TermuxCyberArmy | ARCHIEF-KANDIDAAT |

---

## WAT HEBBEN WE NODIG VOOR AOSP BUILD?

### Direct bruikbaar (bestaat al):
1. **stay4os-tegu** repo -- device tree met makefiles, lunch targets, flash guide
2. **Stay4LM-train/scripts/chatlog_to_sft.py** -- chat-log naar SFT data converter
3. **android_device_nothing_asteroids** -- referentie voor device tree structuur
4. **GrokPhone-OS/scripts/setup-build-env.sh** -- referentie voor build env setup
5. **android_packages_apps_Grok** -- basis voor Stay4S AI system app
6. **android_packages_apps_AetherCore** -- basis voor AI orchestrator
7. **Stay4S-WhatsApp-MVP** -- alle Pixel 9a scripts + AOSP docs + device dump

### Nog te maken:
1. **Vendor blobs voor tegu** -- extract van Pixel 9a (extract_tegu_blobs.sh klaar)
2. **Stay4S AI APK** -- Grok app ombouwen naar Stay4S AI met llama.cpp
3. **Boot animation** -- Stay4S branded (spec klaar in STAY4OS_BRAND_SPEC.md)
4. **Overlay themes** -- Stay4S kleuren, iconen, wallpapers
5. **sepolicy voor stay4s_ai** -- SELinux rules voor llama-server service

### Te koppelen aan AOSP build:
1. stay4os-tegu device tree -> ~/android/stay4os/device/google/tegu-stay4os/
2. vendor/stay4os/stay4os-tegu.mk -> ~/android/stay4os/vendor/stay4os/
3. llama.cpp binary + model -> vendor/stay4os/app/Stay4SAI/
4. Signing keys -> /workspace/stay4os-keys/ (al gegenereerd)
5. stay4os_build.sh -> automated build (al klaar op pod)