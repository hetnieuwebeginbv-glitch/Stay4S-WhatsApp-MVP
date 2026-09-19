"""
Stay4Compa Agent -- Het brein.
Gebruikt Ollama /api/chat (think:false) + ToolRegistry (handen).
"""
import os
import json
import logging
import requests
from typing import Optional, Dict, List, Any

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger("stay4s.compa.agent")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://192.168.2.21:11434")
OLLAMA_MODEL = os.environ.get("COMPA_MODEL", "qwen3:1.7b")

from stay4compa_core import Memory, ToolRegistry, Conversations, TeamLog, Customers, Workflows, init

SYSTEM_PROMPT = """Jij bent Stay4Compa, de AI-assistent van Stay4S. Je draait op een Raspberry Pi 5 met eigen AI. Soeverein, lokaal, geen Big Tech.

Je kunt tools gebruiken. Beschikbare tools:
{tools}

Regels:
- Als je een tool wilt gebruiken, zeg: TOOL: tool_naam PARAM: key=value
- Anders geef je een normaal antwoord
- Je spreekt Nederlands, vriendelijk en professioneel
- Bij twijfel vraag je door
- Je kent Stay4S producten: Stay4LM, Stay4Safe AI, Stay4S Cloud, WhatsApp AI
"""


def get_tools_description() -> str:
    tools = ToolRegistry.list_tools()
    return "\n".join([f"- {t['name']}: {t['description']}" for t in tools])


def call_ollama(prompt: str, system: str = "", max_tokens: int = 500) -> str:
    """Roep Ollama aan via /api/chat met think:false."""
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "think": False,
                "options": {"num_predict": max_tokens, "top_p": 0.9, "top_k": 40}
            },
            timeout=120
        )
        data = resp.json()
        return data.get("message", {}).get("content", "").strip()
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return f"[FOUT: kan AI niet bereiken: {e}]"


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
    """Hoofd functie: verwerk een inkomend bericht."""
    init()
    user_memory = Memory.get_all_user(phone_hash)
    memory_context = ""
    if user_memory:
        memory_context = "\nGebruiker info: " + json.dumps(user_memory, ensure_ascii=False)
    tools_desc = get_tools_description()
    system = SYSTEM_PROMPT.format(tools=tools_desc)
    if memory_context:
        system += memory_context
    logger.info(f"Agent: processing message from {name} ({channel})")
    ai_response = call_ollama(message, system)
    tool_call = parse_tool_call(ai_response)
    if tool_call:
        logger.info(f"Agent wants tool: {tool_call['tool']}")
        result = ToolRegistry.execute(tool_call["tool"], **tool_call["params"])
        followup = f"Tool resultaat voor {tool_call['tool']}: {json.dumps(result, ensure_ascii=False)}\nGeef een duidelijk antwoord aan de gebruiker op basis van dit resultaat."
        ai_response = call_ollama(followup, system)
    if "ik heet" in message.lower() or "mijn naam is" in message.lower():
        try:
            name_part = message.lower().split("heet")[-1].split("naam is")[-1].strip().strip(".!?")
            Memory.save_user(phone_hash, "naam", name_part)
        except Exception:
            pass
    Conversations.add(phone_hash, channel, name, message, ai_response, "stay4compa", 0.8)
    TeamLog.log("STAY4COMPA", "MESSAGE", f"{name} ({channel}): {message[:60]} -> {ai_response[:60]}")
    return {
        "response": ai_response,
        "channel": channel,
        "tools_used": [tool_call["tool"]] if tool_call else [],
        "memory": user_memory
    }


# --- Web API ---

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

compa_app = FastAPI(title="Stay4Compa Agent", version="1.0.0")


@compa_app.get("/")
async def compa_dashboard():
    return {
        "service": "stay4compa",
        "version": "1.0.0",
        "tools": ToolRegistry.list_tools(),
        "workflows": list(Workflows.workflows.keys()),
        "customers": len(Customers.list_all()),
        "conversations": len(Conversations.list_recent(10000)),
    }


@compa_app.post("/chat")
async def compa_chat(request: Request):
    data = await request.json()
    message = data.get("message", "")
    phone = data.get("phone", "web")
    name = data.get("name", "Gebruiker")
    if not message:
        return {"error": "no message"}
    result = process_message(message, phone_hash=hash(str(phone)), channel="web", name=name)
    return result


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
        logger.info(f"Starting Stay4Compa Agent on port {port}")
        uvicorn.run(compa_app, host="0.0.0.0", port=port)
    elif len(sys.argv) > 1 and sys.argv[1] == "--chat":
        print("Stay4Compa Agent -- CLI mode (type 'quit' to exit)")
        print("=" * 50)
        while True:
            msg = input("\nJij: ")
            if msg.lower() in ("quit", "exit", "stop"):
                break
            result = process_message(msg, phone_hash="cli", channel="cli", name="Mitchell")
            print(f"\nStay4Compa: {result['response']}")
            if result.get("tools_used"):
                print(f"  [Tools gebruikt: {', '.join(result['tools_used'])}]")
    else:
        print("Stay4Compa Agent")
        print("Gebruik: --serve (web server op 8082) of --chat (CLI mode)")
        print(f"Tools: {len(ToolRegistry.tools)}")
        print(f"Workflows: {len(Workflows.workflows)}")