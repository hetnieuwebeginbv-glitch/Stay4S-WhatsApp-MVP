# STAY4S MEESTERCOORDINATOR -- AOSP TRANSITIE PROJECT AUDIT
# Voor: OpenCode, ChatGPT, Grok, Stay4Compa, Droid, en alle meewerkende AIs
# Datum: 21 september 2026
# Door: Mitchell (Owner) + Droid (Architect of Record)

## WAAROM DEZE PROMPT

We gaan Stay4S uitbreiden naar een eigen AOSP ROM op de Google Pixel 9a (codename: tegu). 
Voordat we dat doen, moet iedereen zich melden met een volledig verslag van:
1. Wat we hebben
2. Wat we nog niet hebben
3. Welke documenten bestaan en waar ze staan
4. Wat de regels zijn
5. Nieuwe regels die we moeten vaststellen

Iedereen moet zich melden in de stay4s-docs. Ook Droid.

---

## DEEL A -- WAT WE HEBBEN (Volledige Inventarisatie)

Beantwoord elke vraag met zoveel mogelijk detail:

### A1. Hardware
- Welke hardware is fysiek aanwezig en operationeel?
  - Pixel 9a (tegu, GrapheneOS, Android 16, Tensor G4, 8GB RAM, 109GB storage)
  - Raspberry Pi 5 (8GB RAM, 29GB disk, 6 systemd services)
  - GL-MT3000 router (actief, Pixel 9a verbonden op 192.168.8.196)
  - Welke GPUs? (alleen RunPod cloud, geen lokale GPU besteld)
- Wat ontbreekt er voor AOSP?

### A2. Software & Infrastructure
- Pi 5: 6 systemd services (webhook:8081, compa:8082, vault:8083, ollama, cloudflared, caddy)
- Pixel 9a: Termux + llama.cpp v0.4.1-dev + Qwen3-4B + eigen-cyc6
- RunPod: 41 pods, 3 RUNNING, 11 serverless endpoints
- GitHub: Stay4S-WhatsApp-MVP (15+ commits), stay4s-ai-board, stay4os-docs
- Ollama: qwen3:1.7b (Pi 5 primary), eigen-cyc6 (fallback), qwen3:4b (Pixel 9a primary)

### A3. AI Modellen
- Spoor A (Qwen3-8B fine-tune): SFT1=0.4743 (kampioen), SFT6=0.4148, SFT-data schaling loopt
- Spoor B (eigen 1.67B from scratch): Cyc6 KLAAR (ppl 5.93), Cyc6-SFT q4 getest op Pi 5 + Pixel 9a (kwaliteit onvoldoende)
- Qwen3-4B-Instruct-2507: WERKT op Pixel 9a (8 tok/s, perfect Nederlands)
- Qwen3-1.7B: WERKT op Pi 5 (fallback)
- Welke modellen missen we voor AOSP?

### A4. Producten & Features
- WhatsApp AI klantenservice: LIVE (Meta verified, webhook actief, business number in review)
- Stay4Safe AI: LIVE (scam detector, landing page)
- Stay4Compa: LIVE (self-hosted agent, 10 tools, 3 workflows)
- E2EE Vault: LIVE (AES-256-GCM, JWT)
- Computer-use agent v3.0: BREAKTHROUGH (4-step task completion)
- Chat logger: Conversation saving + training review system
- Flash endpoint: Code klaar, niet getest
- Welke producten missen we voor AOSP?

---

## DEEL B -- WAT WE NOG NIET HEBBEN

Beantwoord:

### B1. AOSP ROM Build
- Hebben we een AOSP source tree? (Nee)
- Hebben we device tree voor tegu? (Alleen dump data, geen echte tree)
- Hebben we vendor blobs? (Nee)
- Hebben we een build environment? (Nee, wel RunPod pods beschikbaar)
- Hebben we Stay4S customisatie specs? (Nee, moeten worden ontworpen)

### B2. Ontbrekende Infrastructure
- Cloudflare named tunnel (wacht op Mitchell account)
- GL-MT3000 WireGuard (wacht op admin password)
- Telegram bot token (wacht op @BotFather)
- Mollie betaling (voor Stay4Safe abonnementen)
- GCS service account JSON (voor rclone zonder signed URLs)

### B3. Ontbrekende AI
- Eigen model kwaliteit onvoldoende (50K+ SFT data nodig)
- Geen Stay4S-specifieke fine-tune op Qwen3-4B
- Geen eigen eval benchmark
- Geen LoRA adapter voor Stay4S persoonlijkheid

---

## DEEL C -- DOCUMENTEN EN WAAR ZE STAAN

### C1. Centrale Documenten (stay4os-docs/00_CENTRAAL/)
Lijst ALLE documenten die je kent met:
- Bestandsnaam
- Volledig pad
- Korte beschrijving (1 regel)
- Laatst bijgewerkt (datum)
- Status (actueel/verouderd/archief)

### C2. GitHub Repositories
- Stay4S-WhatsApp-MVP: github.com/hetnieuwebeginbv-glitch/Stay4S-WhatsApp-MVP
  - 15+ commits, 28+ files
  - Laatste commit: 99d4e60 (chat logger v2)
- stay4s-ai-board: github.com/hetnieuwebeginbv-glitch/stay4s-ai-board
- stay4os-docs: github.com/hetnieuwebeginbv-glitch/stay4os-docs

### C3. Pi 5 Bestanden
- /home/Miesdevries/stay4s-whatsapp/ (alle Python scripts, databases, .env)
- /var/www/stay4s/ (Caddy web root)
- /etc/caddy/Caddyfile
- 6 systemd services
- 4 cron jobs

### C4. Pixel 9a Bestanden
- ~/models/ (qwen3-4b-q4_k_m.gguf 2.5GB, qwen3-1.7b-q8_0.gguf 1.83GB, cyc6-sft-q4.gguf 1.0GB)
- ~/llama.cpp/build/bin/ (llama-server, llama-cli, etc.)
- /sdcard/Download/stay4s-ai.sh (auto-start script)
- /sdcard/Download/stay4s-chat-log.sh (conversation logger)
- /sdcard/Download/stay4s-conversations/ (opgeslagen gesprekken)
- /data/local/tmp/cyc6-sft-q4.gguf (OpenCode copy)

### C5. Laptop Bestanden
- D:\STAY4S-DATA\ (cyc6-sft-q4.gguf, pixel9a-dump/, termux scripts)
- C:\Users\Gebruiker\stay4os-docs\ (centrale docs repo)
- C:\Users\Gebruiker\Stay4S-WhatsApp-MVP\ (GitHub repo local)

---

## DEEL D -- REGELS (HUIDIGE EN NIEUWE)

### D1. Huidige Bindende Directives
| ID | Regel | Status |
|----|-------|--------|
| O-001 | Volle toestemmingen, maximale autonomie | ACTIEF |
| O-003 | Droid = bouwmeester / Android leader | ACTIEF |
| O-006 | Codex retired. Fleet = Grok + Droid (+ OpenCode) | ACTIEF |
| O-008 | Bestanden nooit wissen, alleen verplaatsen | ACTIEF |
| O-009 | Altijd 2 opslagpunten buiten GitHub | ACTIEF |
| O-014 | Droid = Architect of Record | ACTIEF |
| O-150 | Spoor B stopt nooit (eigen model training) | ACTIEF |
| O-173 | Optie C = only Dutch records | ACTIEF |
| O-204 | Meta bedrijfsverificatie GOEDGEKEURD | ACTIEF |
| -- | Geen pod-stops zonder Mitchell GO | ACTIEF |
| -- | Geen twee agents aan dezelfde taak | ACTIEF |
| -- | Config is leidend, niet het script (DR-003) | ACTIEF |
| -- | Geen GitHub tokens in omgevingsvariabelen | ACTIEF |
| -- | Voeg nooit credentials toe aan commits | ACTIEF |

### D2. NIEUW VOORGESTELDE REGELS (te bevestigen)
| ID | Regel | Voorstel door |
|----|-------|--------------|
| O-210 | AOSP ROM = top prioriteit na SFT-data schaling | Mitchell |
| O-211 | Eigen AI op Pixel 9a = Qwen3-4B primary, eigen-cyc6 fallback | Mitchell |
| O-212 | Chat logger data = eerste bron voor SFT training data | Mitchell |
| O-213 | Elke AI moet zich melden in stay4os-docs/00_CENTRAAL/agents/ | Mitchell |
| O-214 | AOSP build draait op RunPod (geen lokale build server) | Droid |
| O-215 | Device tree voor tegu = gebaseerd op AOSP upstream + GrapheneOS patches | Droid |
| O-216 | Stay4S ROM = privacy-first, geen Google telemetry, eigen AI ingebakken | Mitchell |

### D3. AOSP Specifieke Regels (voorgesteld)
1. AOSP source op RunPod network volume (niet lokaal, te groot ~30GB+)
2. Device tree in eigen GitHub repo: Stay4S-AOSP-tegu
3. Vendor blobs geextraheerd van Pixel 9a (met toestemming O-008)
4. Build op RunPod pod met minimaal 32GB RAM
5. Stay4S customisaties in device/product makefiles, niet in framework
6. Eigen AI (llama.cpp + Qwen3-4B) als prebuilt app in system image
7. GrapheneOS security patches behouden (verified boot, SELinux enforcing)
8. Eigen signing keys voor ROM (niet Google's)

---

## DEEL E -- IEDEREEN MOET ZICH MELDEN

### Wie moet melden:
1. **OpenCode** -- SFT-data status, eigen model plan, AOSP mogelijkheden
2. **Droid** -- Volledige infra status, AOSP build plan, Pixel 9a status
3. **ChatGPT** -- Eventuele bijdragen, AOSP kennis
4. **Grok** -- Eventuele bijdragen, AOSP kennis
5. **Stay4Compa** -- Agent platform status, integratie met AOSP

### Wat moet je melden:
1. Je huidige status (bezig/wacht/klaar)
2. Wat je hebt gedaan (laatste 24u)
3. Wat je gaat doen (volgende 24u)
4. Welke documenten je hebt bijgedragen
5. Welke blockers je ervaart
6. Wat je kunt bijdragen aan AOSP

### Waar moet je je melden:
Schrijf je verslag naar:
`stay4os-docs/00_CENTRAAL/agents/INBOX_[JOUW_NAAM].md`

Format:
```
## [Jouw AI] -- Melding 21 sep 2026

### Status: [BEZIG/WACHT/KLAAR]
### Laatste 24u: [wat je hebt gedaan]
### Volgende 24u: [wat je gaat doen]
### Documenten: [lijst van docs die je hebt bijgedragen]
### Blockers: [wat je tegenhoudt]
### AOSP bijdrage: [wat je kunt bijdragen aan de AOSP ROM]
```

---

## DEEL F -- AOSP ROM PLAN (Voorbereidend)

### Doel
Een eigen Android ROM (Stay4OS) gebaseerd op AOSP voor de Pixel 9a (tegu) met:
- Eigen AI ingebakken (Qwen3-4B + llama.cpp als system app)
- Privacy-first (geen Google telemetry, GrapheneOS-level security)
- Stay4S branding en services
- WireGuard VPN ingebouwd
- Eigen app store (GrapheneOS app store als basis)
- WhatsApp AI klantenservice als system service

### Fases
1. **Fase 1: Voorbereiding** (nu)
   - AOSP source tree opzetten op RunPod
   - Device tree voor tegu maken
   - Vendor blobs extraheren van Pixel 9a
   - Build environment op RunPod opzetten
   
2. **Fase 2: Basiss Build**
   - Vanilla AOSP build voor tegu
   - Boot testen op Pixel 9a
   - Verified boot met eigen keys
   
3. **Fase 3: Stay4S Customisaties**
   - Eigen launcher
   - Eigen AI app (llama.cpp + Qwen3-4B)
   - Stay4S branding
   - Privacy hardening
   - WireGuard ingebouwd
   
4. **Fase 4: Test & Deploy**
   - Flash naar Pixel 9a
   - Alle features testen
   - Eerste Stay4OS ROM release

### Benodigdheden
- RunPod pod met 64GB+ RAM voor AOSP build (~6-8 uur build time)
- 50GB+ storage (network volume) voor AOSP source + build output
- Pixel 9a bootloader unlock (voorbereiding, nog niet uitvoeren)
- Eigen signing keys (avbtool + make_key)
- Device tree data (al gedeeltelijk verzameld in pixel9a-dump/)

---

## ACTIE: Wat nu te doen

1. **Iedereen:** Meld je in stay4os-docs met je volledige verslag
2. **OpenCode:** Geef status van SFT-data schaling + kun je AOSP source syncen op RunPod?
3. **Droid:** Start autonoom met AOSP voorbereiding (device tree, build plan)
4. **Mitchell:** Bevestig nieuwe regels O-210 t/m O-216

Deze prompt is bindend. Iedereen moet reageren binnen 24 uur.