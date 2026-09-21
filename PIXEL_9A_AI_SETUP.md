# Stay4S Eigen AI - Pixel 9a Setup

## Hardware
- Device: Pixel 9a (tegu), GrapheneOS, Android 16
- SoC: Google Tensor G4 (zumapro), 8-core ARM
- RAM: 8GB (4GB voor Android, 4GB voor AI)
- Storage: 109GB (106GB vrij)

## Software Stack
- Termux v0.118.3 (F-Droid)
- llama.cpp v0.4.1-dev (built from source, Clang 21.1.8)
- ARM features: NEON, ARM_FMA, FP16_VA, MATMUL_INT8, SVE, DOTPROD

## Models
| Model | File | Size | Role | Quality |
|-------|------|------|------|---------|
| Qwen3-4B-Instruct-2507 | qwen3-4b-q4_k_m.gguf | 2.50GB | PRIMARY | Uitstekend (8 tok/s) |
| Qwen3-1.7B | qwen3-1.7b-q8_0.gguf | 1.83GB | Backup | Goed |
| eigen-cyc6-sft-q4 | cyc6-sft-q4.gguf | 1.00GB | FALLBACK | Onvoldoende (needs more training) |

## Usage
```bash
# Start server (loads Qwen3-4B, ~5s)
sh /sdcard/Download/stay4s-ai.sh start

# Chat interactively
sh /sdcard/Download/stay4s-ai.sh chat

# Check status
sh /sdcard/Download/stay4s-ai.sh status

# Stop server
sh /sdcard/Download/stay4s-ai.sh stop

# List available models
sh /sdcard/Download/stay4s-ai.sh switch
```

## API
Server draait op http://127.0.0.1:8888 met OpenAI-compatible API:

```bash
curl http://127.0.0.1:8888/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hallo"}],"max_tokens":100}'
```

## Performance
- Prompt processing: 21 tok/s
- Token generation: 7-8 tok/s
- Model load: ~5 seconden
- RAM usage: ~3GB (model + context + compute)

## Test Results (20 sep 2026)
- Q1 "Hallo, wat kan jij doen?": Uitgebreid antwoord in vloeiend Nederlands
- Q2 "Openingstijden?" (met system prompt): Correcte openingstijden gegeven
- Q3 "Wat is Stay4S?": Creatief antwoord (model kent Stay4S niet, geen training data)
- Q4 "Hoofdstad Nederland?": "Amsterdam" -- correct!

## Build Instructions
```bash
# In Termux:
pkg update && pkg install -y git cmake clang python wget
git clone --depth 1 https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j4
# Build time: ~9.5 minuten op Tensor G4
```