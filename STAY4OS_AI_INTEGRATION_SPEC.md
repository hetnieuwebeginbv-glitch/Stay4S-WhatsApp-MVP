# STAY4OS AI-INTEGRATIE-SPEC
## Hoe het eigen AI-brein in Stay4OS komt (volgende ROM-build)
### 22 sep 2026 — OpenCode

---

## DOEL

Stay4OS krijgt een **systeem-AI-assistent** die overal in de OS werkt:
- Init-script start AI bij boot
- Systeem-chat-interface (geen losse Termux-app)
- Notificatie-hooks (AI leest/adviseert)
- Tools (computer-use, agent-factory) via systeemrechten

Dit is VOOR de volgende ROM-build. Deze Stay4OS-build (v4) heeft alleen
de kernel + basis; de AI-integratie komt erin.

---

## ARCHITECTUUR

```
┌─────────────────────────────────────────────┐
│ STAY4OS (Android 16 / LineageOS 23.2)      │
│                                             │
│  /system/priv-app/Stay4AI/                  │
│  ├── Stay4AIService.java   (AIDL-service)   │
│  ├── InferenceEngine.java  (llama.cpp)      │
│  ├── ChatActivity.java     (chat-UI)        │
│  └── PrivacyGuard.java     (safety)         │
│                                             │
│  /data/stay4s/models/cyc7-sft-q4.gguf       │  ← het eigen model
│  /data/stay4s/models/stay4s-lora.gguf       │  ← productie (later)
│                                             │
│  init.stay4ai.rc  (start AI bij boot)       │
└─────────────────────────────────────────────┘
```

---

## COMPONENTEN

### 1. Stay4AIService (AIDL)
- Systeem-service die AI aanbiedt aan elke app
- AIDL: `IAStay4AIService.aidl`
  - `chat(prompt, max_tokens)` → response
  - `summarize(text)` → samenvatting
  - `detectScam(text)` → safety
  - `runAgent(task)` → agent-factory
- Geprivileged (platform-cert), andere Stay4OS-apps kunnen hem aanroepen

### 2. InferenceEngine (llama.cpp binding)
- Laadt GGUF bij boot (of lazy bij eerste gebruik)
- Model-keuze: cyc7-sft-q4 (lokaal) OF stay4s-lora (via Pi 5/serverless)
- NNAPI-gebruik voor hardwareversnelling (Tensor G4)
- Fallback: CPU

### 3. ChatActivity (systeem-UI)
- Chat-interface overal beschikbaar (quick-settings tile, gesture)
- Toont AI-responsen in systeemstijl
- Gesprek-log → training-data (chat-log format, met toestemming)

### 4. PrivacyGuard
- AI leest ALLEEN wat expliciet is toegestaan
- Notificaties: AI kan samenvatten maar niet extern sturen
- Lokaal = standaard (niks verlaat de telefoon tenzij gevraagd)

### 5. init.stay4ai.rc
```rc
service stay4ai /system/bin/stay4ai_server
    class main
    user system
    group system
    seclabel u:r:stay4ai:s0
    disabled
    on property:sys.boot_completed=1
        start stay4ai
```

---

## MODEL-KEUZE (eerlijk)

| Model | Eval | Grootte | Rol in Stay4OS |
|---|---|---|---|
| cyc7-sft-q4 | 32% | 1GB | EXPERIMENTEEL — demo, bewijs-van-concept |
| stay4s-lora | 57% | 4.3GB | PRODUCTIE (via Pi 5 / serverless, te groot voor lokaal) |
| cyc8-3B (toekomst) | ? | ~2GB q4 | ECHTE productie — rekenen + code |

**cyc7-sft-q4 is NIET productie-klaar (32%).** Stay4OS krijgt het als
experimenteel bewijs dat on-device AI werkt. cyc8-3B wordt het echte brein.

---

## IMPLEMENTATIE-VOLGORDE

### Fase A (nu, voorbereiden)
- [x] cyc7-sft-q4 in GCS (klaar)
- [x] Installatie-instructie PIXEL_CYC7_Q4_SETUP.md
- [ ] Stay4AIService.java skelet schrijven (AIDL)
- [ ] init.stay4ai.rc schrijven
- [ ] Android.bp voor Stay4AI-app

### Fase B (na deze flash, als Stay4OS draait)
- [ ] Test cyc7-sft-q4 via Termux eerst (Droid)
- [ ] Port naar systeem-app (als demo werkt)
- [ ] WebView fixen (de v4-build heeft placeholder webview)

### Fase C (cyc8-3B klaar)
- [ ] cyc8-3B-q4 vervangt cyc7-sft-q4 als on-device brein
- [ ] Productie-modus aan

---

## BELANGRIJK (werkregel Mitchell)
- Communiceren via GitHub + dashboard vóór acties
- Droid = ROM/flash; OpenCode = AI-modellen
- Geen pods parallel op hetzelfde doel

*OpenCode — 22 sep. Spec voor de volgende Stay4OS-iteratie.*