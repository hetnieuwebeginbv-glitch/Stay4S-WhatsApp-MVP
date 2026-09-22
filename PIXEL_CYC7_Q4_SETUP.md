# Stay4S Eigen AI op de Pixel 9a — q4-model installatie (HYBRIDE)

## Architectuur (Mitchell's keuze, 22 sep)
- **Lokaal (Pixel)**: cyc7-sft-q4 (1.02GB) — chat, scam-detectie, persoonlijke assistent (privacy)
- **Serverless (RunPod)**: zware taken (code, complexe redenering)
- **Pi 5 (thuis)**: stay4s-lora (4.3GB) — thuis-server, WhatsApp

## Model
- GGUF: `cyc7-sft-q4.gguf` (1.02GB, Q4_K_M)
- GCS: `stayd/staylm2/eigen1b/cyc7-sft-q4-20260922/cyc7-sft-q4.gguf`
- Eval: 32% overall (algemeen 50, code 74, taal 39, pixel 33)
- Stop-tokens: `<|eot|>`, `<|user|>`, `<|assistant|>`

## Installatie (op de Pixel, via Termux — Droid's setup)
```bash
# 1. Download q4 naar telefoon (signed URL of via adb push)
#    /sdcard/Download/cyc7-sft-q4.gguf

# 2. Model in Termux-home
mkdir -p ~/models
cp /sdcard/Download/cyc7-sft-q4.gguf ~/models/

# 3. llama.cpp staat al op de Pixel (Droid's build)
cd ~/llama.cpp/build/bin

# 4. Test (met stop-tokens!)
./llama-cli -m ~/models/cyc7-sft-q4.gguf \
  --temp 0.7 --ctx-size 2048 \
  --stop "<|eot|>" --stop "<|user|>" --stop "<|assistant|>" \
  -p "<|user|>\nWat is Stay4S?<|eot|>\n<|assistant|>\n"
```

## OF via Ollama (als die op Pixel draait)
```bash
cat > Modelfile.cyc7 << 'EOF'
FROM ./cyc7-sft-q4.gguf
PARAMETER temperature 0.7
PARAMETER num_ctx 2048
PARAMETER stop "<|eot|>"
PARAMETER stop "<|user|>"
PARAMETER stop "<|assistant|>"
TEMPLATE """<|user|>
{{ .Prompt }}<|eot|>
<|assistant|>
"""
EOF
ollama create eigen-cyc7 -f Modelfile.cyc7
```

## Testvragen (na installatie)
1. Wat is Stay4S? (domein)
2. Wat is de hoofdstad van Nederland? (algemeen)
3. Schrijf een Python functie die twee getallen optelt. (code)
4. Hoe is het weer? (taal/uitleg)
5. Is dit een scam: 'U heeft een pakket gewonnen, klik hier'? (safety)

## Rollen (hybride)
| Taak | Model | Waar |
|---|---|---|
| Chat + persoonlijk | cyc7-sft-q4 | Pixel (lokaal) |
| Code + redenering | LoRA/serverless | RunPod |
| WhatsApp | stay4s-lora | Pi 5 |
| Backup | qwen3:1.7b | Pi 5 |

## Notitie
- cyc7-sft-q4 is 16× beter dan cyc6 (2%→32%)
- Rekenen blijft zwak (pretraining-issue) — cyc8-3B lost dit op
- Voor Stay4OS-ROM: dit model komt IN de ROM (on-device AI)