"""
Stay4S WhatsApp AI Klantenservice - Webhook Server.
FastAPI server op Pi 5. Ontvangt WhatsApp berichten, haalt RAG context op,
genereert antwoord via StayLM2, stuurt terug.
"""
import os
import time
import json
import hashlib
import hmac
import logging
from datetime import datetime
from typing import List, Dict, Optional

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from rag_engine import RAGEngine
from staylm_client import generate_response
from scam_detector import analyze_message

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger("stay4s.whatsapp")

app = FastAPI(title="Stay4S WhatsApp AI", version="0.2.0")
rag = RAGEngine()
conversations: List[Dict] = []

# Meta tokens
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "stay4s_verify_2026")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
META_PHONE_NUMBER_ID = os.environ.get("META_PHONE_NUMBER_ID", "")
META_APP_SECRET = os.environ.get("META_APP_SECRET", "")


def hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()[:12]


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "stay4s-whatsapp-ai",
        "version": "0.2.0",
        "rag_documents": rag.count(),
        "rag_status": "ok" if rag.count() > 0 else "empty",
        "total_conversations": len(conversations),
    }


@app.get("/chat")
async def chat_page():
    chat_path = os.path.join(os.path.dirname(__file__), "chat.html")
    if os.path.exists(chat_path):
        return FileResponse(chat_path, media_type="text/html")
    return {"error": "chat.html not found"}


@app.get("/")
async def dashboard():
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path, media_type="text/html")
    return {"error": "dashboard.html not found"}


@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    # Webhook signature verification (HMAC-SHA256)
    if META_APP_SECRET:
        signature = request.headers.get("X-Hub-Signature-256", "")
        body = await request.body()
        if signature:
            expected = "sha256=" + hmac.new(
                META_APP_SECRET.encode(), body, hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected):
                logger.warning("Webhook signature verification FAILED")
                return JSONResponse(status_code=403, content={"error": "invalid signature"})

    try:
        data = json.loads(body)
    except Exception:
        body_str = body.decode("utf-8", errors="replace")
        try:
            data = json.loads(body_str)
        except Exception:
            return {"status": "error", "reason": "invalid json"}

    # Check if this is a Meta WhatsApp webhook (has "entry" key)
    if "entry" in data:
        parsed = _parse_meta_webhook(data)
        if not parsed:
            return {"status": "ignored", "reason": "no message in Meta webhook"}
        data = parsed
        is_meta = True
    else:
        is_meta = False

    phone = data.get("from", data.get("From", "unknown"))
    message = data.get("body", data.get("Body", ""))
    msg_id = data.get("message_id", data.get("MessageId", f"msg_{int(time.time())}"))
    name = data.get("profile_name", data.get("ProfileName", "Klant"))

    if not message:
        return {"status": "ignored", "reason": "empty message"}

    logger.info(f"Webhook: {name} ({phone}): {message[:80]}")

    # 1. RAG context ophalen
    context, sources = rag.get_context(message)

    # 2. Bepaal of doorverwijzing nodig is
    # FIX: "iemand" verwijderd (gaf false positives bij "is er iemand?")
    transfer_keywords = ["medewerker", "mens", "telefoon", "bellen", "spreken"]
    needs_transfer = any(kw in message.lower() for kw in transfer_keywords)

    # 3. Genereer antwoord
    if needs_transfer:
        reply_text = "Ik schakel u door naar een medewerker. Een moment geduld alstublieft."
        source = "transfer"
        confidence = 1.0
    else:
        system_prompt = (
            "Je bent een vriendelijke Nederlandse AI-klantenservice medewerker. "
            "Beantwoord de vraag kort en duidelijk in het Nederlands (max 200 woorden). "
            "Gebruik de onderstaande bedrijfsinformatie als bron. "
            "Als de informatie er niet staat, zeg dan eerlijk dat je het niet weet "
            "en bied aan om door te verwijzen naar een medewerker."
        )
        if context:
            full_prompt = system_prompt + "\n\nBedrijfsinformatie:\n" + context + "\n\nKlant: " + message
        else:
            # FIX: RAG-empty check -- geen context = expliciet "weet niet" instructie
            full_prompt = (
                system_prompt
                + "\n\nIMPORTANT: Er is geen bedrijfsinformatie beschikbaar voor deze vraag. "
                + "Je MOET eerlijk zeggen: 'Dat staat niet in mijn informatie, zal ik u doorverbinden met een medewerker?' "
                + "Beantwoord de vraag NIET met algemene kennis. Geef alleen aan dat je het niet weet."
                + "\n\nKlant: " + message
            )

        result = await generate_response(full_prompt, max_tokens=300, temperature=0.5)
        reply_text = result["text"]
        source = result["source"]
        confidence = result["confidence"]

        if confidence < 0.5:
            reply_text += "\n\nAls u deze vraag liever aan een medewerker stelt, laat het me weten."

    # 4. Sla gesprek op
    conv = {
        "id": msg_id,
        "timestamp": datetime.now().isoformat(),
        "phone": hash_phone(phone),
        "name": name,
        "customer_message": message,
        "ai_response": reply_text,
        "source": source,
        "confidence": confidence,
        "rag_sources": sources,
        "transferred": needs_transfer,
    }
    conversations.append(conv)
    if len(conversations) > 1000:
        conversations[:] = conversations[-500:]

    logger.info(f"Reply ({source}, conf={confidence:.2f}): {reply_text[:80]}")

    # Send reply back to WhatsApp if this came from Meta
    if is_meta and phone and phone != "unknown":
        await _send_whatsapp_reply(phone, reply_text)

    return {
        "status": "ok",
        "reply": reply_text,
        "source": source,
        "confidence": confidence,
        "rag_sources": sources,
        "conversation_id": msg_id,
    }


@app.get("/conversations")
async def get_conversations(limit: int = 50):
    return {"total": len(conversations), "conversations": conversations[-limit:]}


@app.get("/documents")
async def list_documents():
    return {"documents": rag.list_all(), "count": rag.count()}


@app.post("/documents")
async def add_document(data: dict):
    title = data.get("title", "")
    content = data.get("content", "")
    source = data.get("source", "manual")
    if not title or not content:
        return {"error": "title and content required"}
    doc_id = rag.add_document(title, content, source)
    return {"id": doc_id, "status": "added"}


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    if rag.delete_document(doc_id):
        return {"status": "deleted"}
    return {"error": "not found"}


# --- WhatsApp Business API Integration ---

@app.get("/webhook")
async def webhook_verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode", "")
    token = params.get("hub.verify_token", "")
    challenge = params.get("hub.challenge", "")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified")
        return PlainTextResponse(content=challenge)
    logger.warning(f"Webhook verify failed: mode={mode} token={token[:10]}...")
    return JSONResponse(status_code=403, content={"error": "verification failed"})


async def _send_whatsapp_reply(to_phone: str, text: str):
    if not META_ACCESS_TOKEN or not META_PHONE_NUMBER_ID:
        logger.warning("Meta tokens not configured, skipping WhatsApp reply")
        return
    url = f"https://graph.facebook.com/v18.0/{META_PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}", "Content-Type": "application/json"}
    body = {"messaging_product": "whatsapp", "to": to_phone, "type": "text", "text": {"body": text}}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code == 200:
                logger.info(f"WhatsApp reply sent to {to_phone}")
            else:
                logger.error(f"WhatsApp reply failed: HTTP {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"WhatsApp reply error: {e}")


def _parse_meta_webhook(data: dict):
    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        contacts = value.get("contacts", [])
        if not messages:
            return None
        msg = messages[0]
        phone = msg.get(" "    , "")
        text = msg.get("text", {}).get("body", "")
        msg_id = msg.get("id", f"msg_{int(time.time())}")
        name = contacts[0].get("profile", {}).get("name", "Klant") if contacts else "Klant"
        return {"from": phone, "body": text, "message_id": msg_id, "profile_name": name}
    except Exception:
        return None


@app.get("/privacy")
async def privacy_page():
    path = os.path.join(os.path.dirname(__file__), "privacy.html")
    if os.path.exists(path):
        return FileResponse(path, media_type="text/html")
    return {"error": "privacy.html not found"}


@app.get("/terms")
async def terms_page():
    path = os.path.join(os.path.dirname(__file__), "terms.html")
    if os.path.exists(path):
        return FileResponse(path, media_type="text/html")
    return {"error": "terms.html not found"}


@app.get("/data-deletion")
async def data_deletion_page():
    path = os.path.join(os.path.dirname(__file__), "data-deletion.html")
    if os.path.exists(path):
        return FileResponse(path, media_type="text/html")
    return {"error": "data-deletion.html not found"}


@app.post("/data-deletion-callback")
async def data_deletion_callback(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = dict(await request.form())
    signed_request = data.get("signed_request", "")
    logger.info(f"Data deletion callback received: {signed_request[:30]}...")
    deletion_code = f"stay4s-deletion-{int(time.time())}"
    url = f"https://blast-wifi-isolated-retention.trycloudflare.com/data-deletion"
    return JSONResponse(content={
        "url": url,
        "deletion_code": deletion_code,
        "confirmation_code": deletion_code
    })


# --- Chat Widget API (voor stay4s.com embed) ---

@app.post("/widget")
async def chat_widget_api(request: Request):
    # API endpoint voor stay4s.com chat widget
    try:
        data = await request.json()
    except Exception:
        return {"error": "invalid json"}
    message = data.get("message", "")
    if not message:
        return {"error": "no message"}
    context, sources = rag.get_context(message)
    transfer_keywords = ["medewerker", "mens", "telefoon", "bellen", "spreken"]
    needs_transfer = any(kw in message.lower() for kw in transfer_keywords)
    if needs_transfer:
        return {"reply": "Ik schakel u door naar een medewerker. Een moment geduld alstublieft.", "source": "transfer"}
    system_prompt = (
        "Je bent Stay4S AI, een vriendelijke Nederlandse AI-assistent. "
        "Beantwoord kort en duidelijk in het Nederlands (max 150 woorden). "
        "Gebruik de bedrijfsinformatie als bron. "
        "Als je het niet weet, zeg het eerlijk."
    )
    if context:
        full_prompt = system_prompt + "\n\nBedrijfsinformatie:\n" + context + "\n\nKlant: " + message
    else:
        full_prompt = system_prompt + "\n\nIMPORTANT: Geen bedrijfsinformatie beschikbaar. Zeg eerlijk dat je het niet weet.\n\nKlant: " + message
    result = await generate_response(full_prompt, max_tokens=200, temperature=0.5)
    conv = {
        "id": f"widget_{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "phone": "widget",
        "name": "Website bezoeker",
        "customer_message": message,
        "ai_response": result["text"],
        "source": result["source"],
        "confidence": result["confidence"],
        "rag_sources": sources,
        "transferred": needs_transfer,
    }
    conversations.append(conv)
    return {"reply": result["text"], "source": result["source"], "confidence": result["confidence"]}




# --- Stay4Safe AI -- Phishing & Scam Detector ---

@app.post("/scan")
async def scan_message(request: Request):
    # Analyseer bericht op phishing/scam indicators
    try:
        data = await request.json()
    except Exception:
        return {"error": "invalid json"}
    message = data.get("message", "")
    if not message:
        return {"error": "no message"}
    result = analyze_message(message)
    logger.info(f"Stay4Safe scan: score={result['risk_score']} level={result['risk_level']}")
    return result


@app.get("/stay4safe")
async def stay4safe_page():
    path = os.path.join(os.path.dirname(__file__), "stay4safe.html")
    if os.path.exists(path):
        return FileResponse(path, media_type="text/html")
    return {"error": "stay4safe.html not found"}


@app.post("/safe")
async def whatsapp_safe_webhook(request: Request):
    # WhatsApp webhook for Stay4Safe -- analyseer doorgestuurd bericht
    try:
        data = await request.json()
    except Exception:
        data = dict(await request.form())
    
    if "entry" in data:
        parsed = _parse_meta_webhook(data)
        if not parsed:
            return {"status": "ignored"}
        data = parsed
        is_meta = True
    else:
        is_meta = False
    
    phone = data.get("from", data.get("From", "unknown"))
    message = data.get("body", data.get("Body", ""))
    name = data.get("profile_name", data.get("ProfileName", "Gebruiker"))
    
    if not message:
        return {"status": "ignored", "reason": "empty message"}
    
    logger.info(f"Stay4Safe: {name} ({phone}): {message[:80]}")
    
    # Analyseer op scam
    result = analyze_message(message)
    
    # Bouw WhatsApp-vriendelijk antwoord
    reply = result["report"]
    
    # Sla op in conversations
    conv = {
        "id": f"safe_{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "phone": hash_phone(phone),
        "name": name,
        "customer_message": message,
        "ai_response": reply,
        "source": "stay4safe",
        "confidence": result["risk_score"] / 100.0,
        "rag_sources": [],
        "transferred": False,
    }
    conversations.append(conv)
    
    # Stuur terug via WhatsApp
    if is_meta and phone and phone != "unknown":
        await _send_whatsapp_reply(phone, reply)
    
    return {"status": "ok", "risk_score": result["risk_score"], "risk_level": result["risk_level"], "reply": reply}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    logger.info(f"Starting Stay4S WhatsApp AI on {host}:{port}")
    uvicorn.run(app, host=host, port=port)