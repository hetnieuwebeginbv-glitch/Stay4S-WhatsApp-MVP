"""
Stay4Compa Agent v2.0 -- Het brein met conversation history.
Verbeteringen:
- Conversation history per gebruiker (geen context verlies)
- Tool calling met volledige context (niet alleen tool resultaat)
- Betere error handling + retry bij lege responses
- Model-specifieke stop tokens
"""
import os
import json
import logging
import requests
from typing import Optional, Dict, List, Any
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger("stay4s.compa.agent")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://192.168.2.21:11434")
OLLAMA_MODEL = os.environ.get("COMPA_MODEL", "qwen3:1.7b")
MAX_HISTORY = 10  # Max messages per conversation

from stay4compa_core import Memory, ToolRegistry, Conversations, TeamLog, Customers, Workflows, init

# Conversation history store (in-memory, per phone_hash)
_conv_history: Dict[str, List[dict]] = defaultdict(list)

SYSTEM_PROMPT = """Jij bent Stay4Compa, de AI-assistent van Stay4S. Je draait op een Raspberry Pi 5 met eigen AI. Soeverein, lokaal, geen Big Tech.

Je kunt tools gebruiken. Beschikbare tools:
{tools}

Regels:
- Als je een tool wilt gebruiken, zeg: TOOL: tool_naam PARAM: key=value
- Anders geef je een normaal antwoord
- Je spreekt Nederlands, vriendelijk en professioneel
- Bij twijfel vraag je door
- Je kent Stay4S producten: Stay4LM, Stay4Safe AI, Stay4S Cloud, WhatsApp AI
- Stay4S KvK: 86200860, openingstijden: ma-vr 9:00-17:00
- Houd antwoorden kort en duidelijk (max 3 zinnen tenzij om uitleg gevraagd)
"""

def get_tools_description() -> str:
    tools = ToolRegistry.list_tools()
    return "\n".join([f"- {t['name']}: {t['description']}" for t in tools])

def get_history(phone_hash: str) -> List[dict]:
    """Haal conversation history op voor een gebruiker."""
    return _conv_history[phone_hash][-MAX_HISTORY:]

def add_to_history(phone_hash: str, role: str, content: str):
    """Voeg message toe aan conversation history."""
    _conv_history[phone_hash].append({"role": role, "content": content})
    # Trim als te lang
    if len(_conv_history[phone_hash]) > MAX_HISTORY * 2:
        _conv_history[phone_hash] = _conv_history[phone_hash][-MAX_HISTORY:]

def call_ollama(messages: List[dict], max_tokens: int = 300, retry: bool = True) -> str:
    """Roep Ollama aan via /api/chat met think:false en conversation history."""
    # Model-specifieke stop tokens
    if "eigen" in OLLAMA_MODEL.lower():
        stop_tokens = ["<|eot|>", "<|user|>", "<|assistant|>"]
        extra = {}
    else:
        stop_tokens = ["<|im_end|>"]
        extra = {"think": False}
    try:
        body = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "top_p": 0.9,
                "top_k": 40,
                "temperature": 0.7,
                "stop": stop_tokens,
            },
        }
        body.update(extra)
        resp = requests.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("message", {}).get("content", "").strip()
            if not content and retry:
                logger.warning("Lege response, probeer met meer tokens")
                return call_ollama(messages, max_tokens=max_tokens + 100, retry=False)
            return content if content else "Ik kon geen antwoord genereren. Probeer het opnieuw."
        logger.error(f"Ollama HTTP {resp.status_code}")
        return "[FOUT: AI server fout]"
    except requests.exceptions.Timeout:
        logger.error("Ollama timeout (120s)")
        return "[FOUT: AI reageert te langzaam. Probeer het later opnieuw.]"
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return f"[FOUT: kan AI niet bereiken]"

def parse_tool_call(text: str) -> Optional[dict]:
    """Parse TOOL: name PARAM: key=value uit AI response."""
    if "TOOL:" not in text:
        return None
    try:
        tool_part = text.split("TOOL:")[1].split("\n")[0].strip()
        tool_name = tool_part.split("PARAM:")[0].strip().split()[0]
        params = {}
        if "PARAM:" in tool_part:
            param_part = tool_part.split("PARAM:")[1].strip()
            for pair in param_part.split():
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    params[k.strip()] = v.strip()
        return {"tool": tool_name, "params": params}
    except Exception:
        return None

def process_message(message: str, phone_hash: str = "web", channel: str = "web", name: str = "Gebruiker") -> dict:
    """Hoofd functie: verwerk een inkomend bericht met conversation history."""
    init()
    
    # Laad gebruiker memory
    user_memory = Memory.get_all_user(phone_hash)
    memory_context = ""
    if user_memory:
        memory_context = "\nGebruiker info: " + json.dumps(user_memory, ensure_ascii=False)
    
    # Bouw system prompt
    tools_desc = get_tools_description()
    system = SYSTEM_PROMPT.format(tools=tools_desc)
    if memory_context:
        system += memory_context
    
    # Bouw messages met conversation history
    messages = [{"role": "system", "content": system}]
    history = get_history(phone_hash)
    messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    # Sla user message op in history
    add_to_history(phone_hash, "user", message)
    
    logger.info(f"Agent: processing message from {name} ({channel}), history={len(history)} msgs")
    
    # Roep AI aan
    ai_response = call_ollama(messages)
    
    # Check voor tool call
    tool_call = parse_tool_call(ai_response)
    tools_used = []
    
    if tool_call:
        logger.info(f"Agent wants tool: {tool_call['tool']}")
        # Sla AI's tool request op in history
        add_to_history(phone_hash, "assistant", ai_response)
        
        # Voer tool uit
        try:
            result = ToolRegistry.execute(tool_call["tool"], **tool_call["params"])
        except Exception as e:
            result = {"error": str(e)}
        
        tools_used.append(tool_call["tool"])
        
        # Bouw followup met VOLLEDIGE conversation context
        followup_msg = f"Tool resultaat voor {tool_call['tool']}: {json.dumps(result, ensure_ascii=False)}\n\nGeef een duidelijk, kort antwoord aan de gebruiker op basis van dit resultaat."
        
        # Voeg tool resultaat toe aan messages (niet aan history, dat is een intern ding)
        messages.append({"role": "assistant", "content": ai_response})
        messages.append({"role": "user", "content": followup_msg})
        
        ai_response = call_ollama(messages)
    
    # Sla AI response op in history
    add_to_history(phone_hash, "assistant", ai_response)
    
    # Naam extractie
    if "ik heet" in message.lower() or "mijn naam is" in message.lower():
        try:
            msg_lower = message.lower()
            if "ik heet" in msg_lower:
                after = msg_lower.split("ik heet")[-1].strip()
            else:
                after = msg_lower.split("mijn naam is")[-1].strip()
            # Take just the first word (the name), capitalize
            name_part = after.split()[0].strip(".,!?;:")
            if name_part and len(name_part) < 30:
                name_part = name_part.capitalize()
                Memory.save_user(phone_hash, "naam", name_part)
        except Exception:
            pass
    
    # Sla conversation op in DB
    Conversations.add(phone_hash, channel, name, message, ai_response, "stay4compa", 0.8)
    TeamLog.log("STAY4COMPA", "MESSAGE", f"{name} ({channel}): {message[:60]} -> {ai_response[:60]}")
    
    return {
        "response": ai_response,
        "channel": channel,
        "tools_used": tools_used,
        "memory": user_memory,
        "history_length": len(history),
    }

# --- Web API ---

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

compa_app = FastAPI(title="Stay4Compa Agent", version="2.0.0")

@compa_app.get("/")
async def compa_dashboard():
    return {
        "service": "stay4compa",
        "version": "2.0.0",
        "tools": ToolRegistry.list_tools(),
        "workflows": list(Workflows.workflows.keys()),
        "customers": len(Customers.list_all()),
        "conversations": len(Conversations.list_recent(10000)),
        "active_conversations": len(_conv_history),
    }

@compa_app.post("/chat")
async def compa_chat(request: Request):
    data = await request.json()
    message = data.get("message", "")
    phone = data.get("phone", "web")
    name = data.get("name", "Gebruiker")
    if not message:
        return {"error": "no message"}
    result = process_message(message, phone_hash=str(hash(str(phone))), channel="web", name=name)
    return result

@compa_app.post("/chat/clear")
async def clear_chat(data: dict):
    """Clear conversation history voor een phone_hash."""
    phone = data.get("phone", "web")
    phone_hash = str(hash(str(phone)))
    if phone_hash in _conv_history:
        del _conv_history[phone_hash]
    return {"status": "ok", "message": "Conversation history cleared"}

@compa_app.get("/customers")
async def list_customers():
    return {"customers": Customers.list_all()}

@compa_app.post("/customers")
async def add_customer(data: dict):
    return {"id": Customers.add(**data)}

@compa_app.get("/conversations")
async def list_conversations(limit: int = 50):
    return {"conversations": Conversations.list_recent(limit)}

@compa_app.get("/tools")
async def list_tools():
    return {"tools": ToolRegistry.list_tools()}

@compa_app.post("/tools/execute")
async def execute_tool(data: dict):
    tool_name = data.get("tool", "")
    params = data.get("params", {})
    return ToolRegistry.execute(tool_name, **params)

@compa_app.get("/workflows/run/{name}")
async def run_workflow(name: str):
    return Workflows.run(name)

@compa_app.get("/memory/{phone_hash}")
async def get_memory(phone_hash: str):
    return {"memory": Memory.get_all_user(phone_hash)}

@compa_app.get("/health")
async def health():
    return {"status": "ok", "model": OLLAMA_MODEL, "version": "2.0.0", "active_conversations": len(_conv_history)}

@compa_app.get("/dashboard")
async def dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "compa_dashboard.html")
    if os.path.exists(path):
        return FileResponse(path, media_type="text/html")
    return {"error": "dashboard not found"}

if __name__ == "__main__":
    import sys
    init()
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        import uvicorn
        port = int(os.environ.get("COMPA_PORT", "8082"))
        logger.info(f"Starting Stay4Compa Agent v2.0 on port {port}")
        uvicorn.run(compa_app, host="0.0.0.0", port=port)
    elif len(sys.argv) > 1 and sys.argv[1] == "--chat":
        print("Stay4Compa Agent v2.0 -- CLI mode (type 'quit' to exit)")
        print("=" * 50)
        while True:
            msg = input("\nJij: ")
            if msg.lower() in ("quit", "exit", "stop"):
                break
            result = process_message(msg, phone_hash="cli", channel="cli", name="Mitchell")
            print(f"\nStay4Compa: {result['response']}")
            if result.get("tools_used"):
                print(f"  [Tools: {', '.join(result['tools_used'])}]")
            print(f"  [History: {result.get('history_length', 0)} msgs]")
    else:
        print("Stay4Compa Agent v2.0")
        print("Gebruik: --serve (web server op 8082) of --chat (CLI mode)")
        print(f"Tools: {len(ToolRegistry.tools)}")
        print(f"Workflows: {len(Workflows.workflows)}")
