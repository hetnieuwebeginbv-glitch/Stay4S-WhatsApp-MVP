"""
Stay4Compa Core -- Zelfgehost AI agent platform op Pi 5.
Vervangt Base44 volledig. Soeverein, lokaal, geen afhankelijkheden.

Architectuur:
  agent_core.py  -> Hoofd agent loop (denk -> act -> observe -> herhaal)
  memory.py      -> SQLite geheugen (globaal + per-gebruiker)
  tools.py       -> Tool registry (scam detect, FAQ, health, send message)
  entities.py    -> SQLite database (klanten, gesprekken, logs, FAQ)
  channels.py    -> Multi-channel (WhatsApp, Telegram, Web)
  workflows.py   -> Cron-gebaseerde geautomatiseerde taken
  web_ui.py      -> Dashboard + management interface

Dit is het brein van Stay4S. Alles draait op Pi 5.
"""
import os
import json
import time
import sqlite3
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger("stay4s.compa")

DB_PATH = os.path.join(os.path.dirname(__file__), "stay4s.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        company TEXT,
        whatsapp TEXT,
        email TEXT,
        plan TEXT DEFAULT 'free',
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT (datetime('now')),
        phone_hash TEXT,
        channel TEXT,
        customer_name TEXT,
        message TEXT,
        ai_response TEXT,
        source TEXT,
        confidence REAL,
        quality_label TEXT,
        transferred INTEGER DEFAULT 0
    );
    
    CREATE TABLE IF NOT EXISTS scam_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT (datetime('now')),
        phone_hash TEXT,
        message TEXT,
        risk_score INTEGER,
        risk_level TEXT,
        categories TEXT
    );
    
    CREATE TABLE IF NOT EXISTS faq_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        source TEXT DEFAULT 'manual',
        created_at TEXT DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS memory_global (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        updated_at TEXT DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS memory_user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_hash TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT,
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(phone_hash, key)
    );
    
    CREATE TABLE IF NOT EXISTS team_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT (datetime('now')),
        agent TEXT,
        event TEXT,
        summary TEXT
    );
    
    CREATE TABLE IF NOT EXISTS workflow_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT (datetime('now')),
        workflow_name TEXT,
        status TEXT,
        result TEXT
    );
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized at " + DB_PATH)


# --- MEMORY ---

class Memory:
    """SQLite-based memory. Global + per-user. Replaceert Base44 memory."""
    
    @staticmethod
    def save_global(key: str, value: str):
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO memory_global (key, value, updated_at) VALUES (?, ?, datetime('now'))", (key, value))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_global(key: str) -> Optional[str]:
        conn = get_db()
        row = conn.execute("SELECT value FROM memory_global WHERE key = ?", (key,)).fetchone()
        conn.close()
        return row["value"] if row else None
    
    @staticmethod
    def save_user(phone_hash: str, key: str, value: str):
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO memory_user (phone_hash, key, value, updated_at) VALUES (?, ?, ?, datetime('now'))", (phone_hash, key, value))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_user(phone_hash: str, key: str) -> Optional[str]:
        conn = get_db()
        row = conn.execute("SELECT value FROM memory_user WHERE phone_hash = ? AND key = ?", (phone_hash, key)).fetchone()
        conn.close()
        return row["value"] if row else None
    
    @staticmethod
    def get_all_user(phone_hash: str) -> Dict[str, str]:
        conn = get_db()
        rows = conn.execute("SELECT key, value FROM memory_user WHERE phone_hash = ?", (phone_hash,)).fetchall()
        conn.close()
        return {row["key"]: row["value"] for row in rows}


# --- ENTITIES ---

class Customers:
    """Klantbeheer. Vervangt Base44 entities."""
    
    @staticmethod
    def add(name: str, company: str = "", whatsapp: str = "", email: str = "", plan: str = "free") -> int:
        conn = get_db()
        c = conn.execute("INSERT INTO customers (name, company, whatsapp, email, plan) VALUES (?, ?, ?, ?, ?)", (name, company, whatsapp, email, plan))
        conn.commit()
        cid = c.lastrowid
        conn.close()
        logger.info(f"New customer: {name} ({company}), plan={plan}")
        return cid
    
    @staticmethod
    def list_all() -> List[dict]:
        conn = get_db()
        rows = conn.execute("SELECT * FROM customers ORDER BY created_at DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    @staticmethod
    def update(cid: int, **kwargs):
        conn = get_db()
        for k, v in kwargs.items():
            conn.execute(f"UPDATE customers SET {k} = ? WHERE id = ?", (v, cid))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(cid: int):
        conn = get_db()
        conn.execute("DELETE FROM customers WHERE id = ?", (cid,))
        conn.commit()
        conn.close()


class Conversations:
    """Gespreksgeschiedenis. Persistent in SQLite."""
    
    @staticmethod
    def add(phone_hash: str, channel: str, name: str, message: str, response: str, source: str, confidence: float, transferred: bool = False):
        conn = get_db()
        conn.execute("INSERT INTO conversations (phone_hash, channel, customer_name, message, ai_response, source, confidence, transferred) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (phone_hash, channel, name, message, response, source, confidence, int(transferred)))
        conn.commit()
        conn.close()
    
    @staticmethod
    def list_recent(limit: int = 50) -> List[dict]:
        conn = get_db()
        rows = conn.execute("SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    @staticmethod
    def export_jsonl(filepath: str):
        """Export voor training data."""
        conn = get_db()
        rows = conn.execute("SELECT * FROM conversations ORDER BY timestamp ASC").fetchall()
        conn.close()
        with open(filepath, "w") as f:
            for r in rows:
                f.write(json.dumps(dict(r), ensure_ascii=False) + "\n")
        logger.info(f"Exported {len(rows)} conversations to {filepath}")


class TeamLog:
    """Team coordinatie log. Vervangt SHARED_STATE voor Stay4Compa."""
    
    @staticmethod
    def log(agent: str, event: str, summary: str):
        conn = get_db()
        conn.execute("INSERT INTO team_logs (agent, event, summary) VALUES (?, ?, ?)", (agent, event, summary))
        conn.commit()
        conn.close()
        logger.info(f"TeamLog: [{agent}] {event}: {summary[:80]}")


# --- TOOL REGISTRY ---

class ToolRegistry:
    """Tool registry. Stay4Compa kiest tools op basis van gebruikersverzoek."""
    
    tools = {}
    
    @classmethod
    def register(cls, name: str, description: str, func):
        cls.tools[name] = {"description": description, "func": func}
        logger.info(f"Tool registered: {name}")
    
    @classmethod
    def execute(cls, tool_name: str, **kwargs) -> dict:
        if tool_name not in cls.tools:
            return {"error": f"unknown tool: {tool_name}"}
        try:
            return cls.tools[tool_name]["func"](**kwargs)
        except Exception as e:
            return {"error": str(e)}
    
    @classmethod
    def list_tools(cls) -> List[dict]:
        return [{"name": k, "description": v["description"]} for k, v in cls.tools.items()]


# --- WORKFLOWS ---

class Workflows:
    """Cron-gebaseerde workflows. Vervangt Base44 automations."""
    
    workflows = {}
    
    @classmethod
    def register(cls, name: str, schedule: str, func):
        cls.workflows[name] = {"schedule": schedule, "func": func}
        logger.info(f"Workflow registered: {name} (schedule: {schedule})")
    
    @classmethod
    def run(cls, name: str) -> dict:
        if name not in cls.workflows:
            return {"error": f"unknown workflow: {name}"}
        try:
            result = cls.workflows[name]["func"]()
            conn = get_db()
            conn.execute("INSERT INTO workflow_runs (workflow_name, status, result) VALUES (?, 'ok', ?)", (name, json.dumps(result, ensure_ascii=False)))
            conn.commit()
            conn.close()
            return result
        except Exception as e:
            conn = get_db()
            conn.execute("INSERT INTO workflow_runs (workflow_name, status, result) VALUES (?, 'error', ?)", (name, str(e)))
            conn.commit()
            conn.close()
            return {"error": str(e)}


# --- INIT ---

def init():
    """Initialiseer Stay4Compa Core."""
    init_db()
    
    # Registreer tools
    try:
        from scam_detector import analyze_message
        ToolRegistry.register("scan_scam", "Analyseer bericht op phishing/scam", analyze_message)
    except ImportError:
        logger.warning("scam_detector not available")
    
    try:
        from rag_engine import RAGEngine
        rag = RAGEngine()
        ToolRegistry.register("search_faq", "Zoek in FAQ database", lambda query: {"context": rag.get_context(query)[0], "sources": rag.get_context(query)[1]})
        ToolRegistry.register("list_faq", "Lijst alle FAQ documenten", lambda: {"documents": rag.list_all(), "count": rag.count()})
        ToolRegistry.register("add_faq", "Voeg FAQ document toe", lambda title, content, source="manual": {"id": rag.add_document(title, content, source)})
    except ImportError:
        logger.warning("rag_engine not available")
    
    # Health check tool
    import requests
    def health_check():
        try:
            resp = requests.get("http://localhost:8081/health", timeout=5)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    ToolRegistry.register("health_check", "Check Pi 5 server health", health_check)
    
    # Customer tools
    ToolRegistry.register("add_customer", "Voeg nieuwe klant toe", lambda name, company="", whatsapp="", email="", plan="free": {"id": Customers.add(name, company, whatsapp, email, plan)})
    ToolRegistry.register("list_customers", "Lijst alle klanten", lambda: {"customers": Customers.list_all()})
    
    # Memory tools
    ToolRegistry.register("save_memory", "Sla geheugen op", lambda key, value, phone_hash=None: Memory.save_global(key, value) if not phone_hash else Memory.save_user(phone_hash, key, value))
    ToolRegistry.register("get_memory", "Haal geheugen op", lambda key, phone_hash=None: Memory.get_global(key) if not phone_hash else Memory.get_user(phone_hash, key))
    
    # Team log tool
    ToolRegistry.register("team_log", "Log team activiteit", lambda agent, event, summary: TeamLog.log(agent, event, summary))
    
    # Registreer workflows
    def daily_report():
        conv = Conversations.list_recent(10)
        return {"report": f"Dagelijks rapport: {len(conv)} gesprekken vandaag", "conversations": len(conv)}
    Workflows.register("daily_report", "0 9 * * *", daily_report)
    
    def conversation_mining():
        Conversations.export_jsonl(os.path.join(os.path.dirname(__file__), "conversations_export.jsonl"))
        return {"status": "exported"}
    Workflows.register("conversation_mining", "0 6 * * *", conversation_mining)
    
    def health_monitor():
        result = health_check()
        if "error" in result:
            TeamLog.log("STAY4COMPA", "ALERT", "Pi 5 health check FAILED: " + str(result["error"]))
        return result
    Workflows.register("health_monitor", "*/5 * * * *", health_monitor)
    
    logger.info("Stay4Compa Core initialized with " + str(len(ToolRegistry.tools)) + " tools and " + str(len(Workflows.workflows)) + " workflows")
    return True


if __name__ == "__main__":
    init()
    print("Stay4Compa Core -- initialized")
    print(f"Tools: {len(ToolRegistry.tools)}")
    print(f"Workflows: {len(Workflows.workflows)}")
    for t in ToolRegistry.list_tools():
        print(f"  Tool: {t['name']} -- {t['description']}")
    for w in Workflows.workflows:
        print(f"  Workflow: {w} (schedule: {Workflows.workflows[w]['schedule']})")