# WAT WE SAMEN KUNNEN — Overzicht + OpenCode's plan
## 24 sep 2026 — UPDATE v2 (RunPod + Droid geïnformeerd)

---

## WAAR WE NU STAAN (alles werkend, 24 sep)
| Component | Status | Bewijs |
|---|---|---|
| **Eigen model (cyc7-sft)** | ✅ op Pi 5 | eigen-cyc7sft:1 in Ollama (32%) |
| **LoRA-Qwen3-4B** | ✅ productie-brein | stay4s-lora 57%, WhatsApp + agent-server |
| **coder-agent LoRA** | ✅ NIEUW BESTE MODEL | **61%** (reken 90%, algemeen 70%) |
| **reken-agent LoRA** | ✅ | **58%** (algemeen 90%, rekenen 70%) |
| **summarizer-agent** | 🔄 traint | 7.418 records, ~1.5u |
| **cyc8-4.4B** | 🔄 traint (groot model) | loss 1.85 (11.36 baseline), 18K/115K steps |
| **Stay4OS v6-build** | 🔄 Droid bouwt | repo-sync + build (incl. cgroup-fix) |
| **Dashboard** | ✅ LIVE op Pi 5 | http://192.168.2.21:8084/planning.html |
| **Agent-leerplan** | ✅ zelfgroeidend | AGENT_LEERPLAN.md + dashboard-tab |

---

## 📢 MELDING AAN RUNPOD + DROID (samenwerkingsupdate)

**Aan Droid:** je v6-build (met cgroup-fix) is de sleutel voor de flash. Zodra klaar:
- OTA-zip op volume → ADB sideload (bewezen route, flash-procedure v2)
- Alle v5-bestanden + vendor_boot_fixed staan klaar in D:\STAY4S-DATA\stay4os-rom\v5\
- Na flash: Stay4OS draait op de Pixel → dan eigen-model-integratie (AetherCore)

**Aan RunPod:** onze trainingspods draaien autonoom (3 pods = $3.05/u):
- A100: cyc8-4.4B (4 dagen, $153 totaal) — groot eigen model
- 4500: agent-LoRA-suite (coder 61%, reken 58%, summarizer→researcher→domein)
- OD-Integration-Plan: aangeboden, voorlopig geparkeerd (eigen dashboard + GitHub werkt al)

---

## AGENT-LEERSUITE (het zelfgroeidende plan)
| Rol | Records | Status | Score | Sterk |
|---|---|---|---|---|
| coder | 2.770 | ✅ KLAAR | **61%** | reken 90%, algemeen 70% |
| reken | 3.711 | ✅ KLAAR | **58%** | algemeen 90%, rekenen 70% |
| summarizer | 7.418 | 🔄 TRAINT | — | — |
| researcher | 7.418 | ⏳ GEPLAND | — | — |
| domein | 0 | ⚠️ WACHT-DATA | — | — |

**Zelfgroei:** agent_leerplan.py genereert na elke training nieuwe leertaken uit eval-zwaktes.
Auto-pipeline: training → eval → GCS → leerplan-update → volgende agent.

---

## OPENCODE'S PLAN (bijgewerkt)

### P1 — Eigen model naar de telefoon (Stay4OS-brein)
- ✅ cyc7-sft op Pi 5 (eigen-cyc7sft:1)
- ⏳ na v6-flash: op Pixel via AetherCore

### P2 — Eigen model sterker (rekenen fixen)
- ✅ Reken-paren in cyc8-pretraining (1000)
- ✅ reken-agent LoRA (58%, rekenen 70%)
- 🔄 cyc8-4.4B lost het fundamenteel op

### P3 — Stay4OS-ROM met kernel (met Droid)
- 🔄 v6-build draait (cgroup-fix inbegrepen)
- ✅ pre-flash checks klaar

### P4 — Assistent-modus compleet
- ✅ Agent-suite (coder/reken/summarizer/researcher)
- ✅ Dashboard live + agent-leerplan
- ⏳ RAG volledig integreren (Qdrant later)

---

## VOLGENDE STAPPEN (autonoom)
1. 🔄 Summarizer klaar (~1.5u) → eval + GCS → leerplan-update
2. ⏳ Researcher start automatisch na summarizer (pipeline)
3. ⏳ Droid's v6-build klaar → FLASH (Mitchell + Droid)
4. ⏳ cyc8-4.4B eval bij checkpoint-mijlpalen

*OpenCode — 24 sep. Samenwerkingsupdate gecommuniceerd via GitHub + dashboard.*