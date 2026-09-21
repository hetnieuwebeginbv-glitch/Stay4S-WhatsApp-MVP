# Stay4S Eigen AI → WhatsApp koppeling

## Doel
De eigen Stay4S-AI (LoRA-Qwen3-4B nu, cyc7-sft straks) laten antwoorden
in WhatsApp via Stay4Compa op de Pi 5.

## Status van de code (al klaar in Stay4S-WhatsApp-MVP)
- `stay4compa_agent.py` leest `COMPA_MODEL` env-var
- Heeft AL eigen-model stop-tokens: `if "eigen" in OLLAMA_MODEL.lower(): stop_tokens = ["<|eot|>", ...]`
- `model_wissel.py` test een model met 5 vragen en wisselt primary

## Stap 1 — LoRA in Ollama op Pi 5 (brein NU, werkt)
```bash
# op Pi 5, model binnenhalen via signed URL of rclone
cd /home/Miesdevries/stay4s-whatsapp/models
wget "<GCS-signed-URL qwen3-4b-lora-q8-v2.gguf>"
# Modelfile
cat > Modelfile.lora << 'EOF'
FROM ./qwen3-4b-lora-q8-v2.gguf
PARAMETER temperature 0.7
PARAMETER num_ctx 2048
EOF
ollama create stay4s-lora -f Modelfile.lora
# test
ollama run stay4s-lora "Wat is Stay4S?"
```

## Stap 2 — Stay4Compa schakelen naar de LoRA
```bash
# in stay4compa_agent.py: COMPA_MODEL default -> "stay4s-lora"
sudo systemctl restart stay4compa
```

## Stap 3 — test via model_wissel
```bash
python3 model_wissel.py --model stay4s-lora
```

## Stap 4 — als cyc7-sft klaar is (eigen 1.67B)
- GGUF-q8 → Ollama als `eigen-cyc7`
- COMPA_MODEL -> "eigen-cyc7" (eigen-model stop-tokens worden automatisch gebruikt)
- Test: eval > 50% en 5 model_wissel-vragen → dan primary

## Veiligheid / fallback
- qwen3:1.7b blijft fallback tot het eigen model de eval haalt
- chat-log vangt gesprekken → training-data (continue-loop)

## Verantwoordelijkheden
- OpenCode: GGUF leveren + eval + instructies
- Droid: installeren op Pi 5 + schakelen + testen