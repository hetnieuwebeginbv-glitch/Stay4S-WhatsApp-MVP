# Stay4S WhatsApp AI MVP

Privacy-first WhatsApp AI klantenservice voor Nederlands MKB.
Draait op eigen infrastructuur (Raspberry Pi 5 + Ollama + RunPod).

## Wat het doet

- Ontvangt WhatsApp-berichten via Meta Business API
- Zoekt antwoorden in bedrijfs-FAQ via SQLite FTS5 RAG
- Genereert antwoorden met Ollama (lokaal) of RunPod (fallback)
- Stuurt antwoord terug via WhatsApp API
- Web dashboard voor monitoring
- Chat interface voor testen

## Architectuur

`
WhatsApp gebruiker
    |
    v
Meta Webhook -> Cloudflare Tunnel -> Pi 5:8081
    |
    v
FastAPI webhook_server.py
    |
    +-> rag_engine.py (SQLite FTS5 FAQ search)
    +-> staylm_client.py (Ollama primary, RunPod fallback)
    |
    v
Antwoord terug via Meta WhatsApp API
`

## Bestanden

| Bestand | Functie |
|---------|---------|
| webhook_server.py | FastAPI server, Meta webhook, message routing |
| rag_engine.py | SQLite FTS5 RAG engine met stop-word removal |
| staylm_client.py | LLM client: Ollama (primair) + RunPod (fallback) |
| faq_seed.py | Seed 10 test FAQ documenten |
| dashboard.html | Web dashboard met statistieken |
| chat.html | WhatsApp-achtige chat test interface |
| privacy.html | AVG/GDPR privacy policy |
| terms.html | Gebruiksvoorwaarden |
| data-deletion.html | Instructies voor gegevensverwijdering |
| requirements.txt | Python dependencies |

## Setup

### 1. Installeer dependencies
`ash
pip3 install fastapi uvicorn requests
`

### 2. Maak .env aan
`ash
RUNPOD_API_KEY=jouw_key
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:1.7b
STAYLM2_ENDPOINT=jouw_endpoint_id
WHATSAPP_VERIFY_TOKEN=jouw_verify_token
META_ACCESS_TOKEN=jouw_token
META_PHONE_NUMBER_ID=jouw_phone_id
META_APP_SECRET=jouw_secret
`

### 3. Pull Ollama model
`ash
ollama pull qwen3:1.7b
`

### 4. Seed FAQ database
`ash
python3 faq_seed.py
`

### 5. Start server
`ash
set -a; source .env; set +a
export PORT=8081
nohup python3 webhook_server.py > server.log 2>&1 &
`

### 6. Setup Meta webhook
- Callback URL: https://jouw-tunnel/webhook
- Verify Token: jouw_verify_token
- Subscribe to: messages

## API Endpoints

| Endpoint | Methode | Functie |
|----------|---------|---------|
| /health | GET | Health check |
| /webhook | GET | Meta webhook verify |
| /webhook | POST | Meta inkomende berichten |
| /chat | GET | Chat test interface |
| /conversations | GET | Gespreksgeschiedenis |
| /documents | GET | Lijst FAQ documenten |
| /documents | POST | Voeg FAQ document toe |
| /documents | DELETE | Verwijder FAQ document |
| /privacy | GET | Privacy policy |
| /terms | GET | Gebruiksvoorwaarden |
| /data-deletion | GET | Verwijderinstructies |
| /data-deletion-callback | POST | Meta data deletion callback |

## Tech Stack

- Python 3.13 + FastAPI + Uvicorn
- SQLite + FTS5 (RAG)
- Ollama (qwen3:1.7b, edge inference)
- RunPod Serverless (StayLM2 fallback)
- Cloudflare Tunnel (publieke URL)
- Meta WhatsApp Business API

## Veiligheid

- .env bevat secrets -> chmod 600 -> .gitignore
- Webhook signature verificatie (HMAC-SHA256) -- TODO
- Geen secrets in logs
- Geen klantdata in commits

## Licentie

Proprietary - Stay4S (Mitchell Turk)

## Team

- Mitchell Turk (Owner)
- Droid (Builder)
- Stay4Compa (Coordinator)
- OpenCode (Engineer)