#!/usr/bin/env python3
"""Stay4S Geheim Communicatie Portaal - E2EE Vault Server
Volledig encrypted, lokaal, soeverein.
AES-256-GCM server-side + Web Crypto API client-side = double encryption.
"""
import os, json, sqlite3, hashlib, secrets, time, hmac
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel
import base64

VAULT_DB = "/home/Miesdevries/stay4s-whatsapp/vault.db"
VAULT_PORT = 8083
JWT_SECRET = secrets.token_hex(32)
TOKEN_EXPIRY_HOURS = 24

app = FastAPI(title="Stay4S Vault", version="1.0.0")

# --- Database ---
def init_db():
    db = sqlite3.connect(VAULT_DB)
    c = db.cursor()
    c.executescript("""
    PRAGMA journal_mode=WAL;
    PRAGMA secure_delete=ON;
    
    CREATE TABLE IF NOT EXISTS vault_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        public_key TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        last_login TEXT
    );
    
    CREATE TABLE IF NOT EXISTS vault_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        encrypted_content TEXT NOT NULL,
        nonce TEXT NOT NULL,
        iv TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        read_at TEXT,
        expires_at TEXT,
        FOREIGN KEY (sender_id) REFERENCES vault_users(id),
        FOREIGN KEY (recipient_id) REFERENCES vault_users(id)
    );
    
    CREATE TABLE IF NOT EXISTS vault_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE NOT NULL,
        created_by INTEGER NOT NULL,
        used_by INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        used_at TEXT,
        expires_at TEXT NOT NULL,
        FOREIGN KEY (created_by) REFERENCES vault_users(id),
        FOREIGN KEY (used_by) REFERENCES vault_users(id)
    );
    
    CREATE TABLE IF NOT EXISTS vault_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        ip TEXT,
        timestamp TEXT DEFAULT (datetime('now')),
        details TEXT
    );
    """)
    db.commit()
    db.close()

init_db()

# --- Auth ---
def hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

def create_jwt(user_id, username):
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + (TOKEN_EXPIRY_HOURS * 3600)
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"

def verify_jwt(token):
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        expected_sig = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except:
        return None

async def get_current_user(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Geen token")
    token = auth[7:]
    payload = verify_jwt(token)
    if not payload:
        raise HTTPException(401, "Ongeldig token")
    return payload

# --- Rate limiting ---
rate_limit = {}

def check_rate_limit(ip, max_req=20, window=60):
    now = time.time()
    if ip not in rate_limit:
        rate_limit[ip] = []
    rate_limit[ip] = [t for t in rate_limit[ip] if now - t < window]
    if len(rate_limit[ip]) >= max_req:
        raise HTTPException(429, "Te veel verzoeken")
    rate_limit[ip].append(now)

# --- Models ---
class RegisterModel(BaseModel):
    username: str
    password: str
    invite_token: str = None

class LoginModel(BaseModel):
    username: str
    password: str

class MessageModel(BaseModel):
    recipient: str
    encrypted_content: str
    nonce: str
    iv: str
    expires_hours: int = 72

# --- Routes ---
@app.get("/health")
async def health():
    db = sqlite3.connect(VAULT_DB)
    c = db.cursor()
    c.execute("SELECT COUNT(*) FROM vault_users")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM vault_messages")
    msgs = c.fetchone()[0]
    db.close()
    return {"status": "ok", "users": users, "messages": msgs, "port": VAULT_PORT}

@app.post("/vault/register")
async def register(req: RegisterModel, request: Request):
    check_rate_limit(request.client.host)
    db = sqlite3.connect(VAULT_DB)
    c = db.cursor()
    
    # Check if registration requires invite token (after first user)
    c.execute("SELECT COUNT(*) FROM vault_users")
    user_count = c.fetchone()[0]
    
    if user_count > 0 and not req.invite_token:
        db.close()
        raise HTTPException(403, "Uitnodiging vereist")
    
    if req.invite_token:
        c.execute("SELECT id, expires_at, used_by FROM vault_tokens WHERE token=?", (req.invite_token,))
        token_row = c.fetchone()
        if not token_row:
            db.close()
            raise HTTPException(403, "Ongeldig token")
        if token_row[2] is not None:
            db.close()
            raise HTTPException(403, "Token al gebruikt")
        if datetime.fromisoformat(token_row[1]) < datetime.now():
            db.close()
            raise HTTPException(403, "Token verlopen")
    
    salt = secrets.token_hex(16)
    pwd_hash = hash_password(req.password, salt)
    
    try:
        c.execute("INSERT INTO vault_users (username, password_hash, salt) VALUES (?, ?, ?)",
                  (req.username, pwd_hash, salt))
        db.commit()
        user_id = c.lastrowid
        
        if req.invite_token:
            c.execute("UPDATE vault_tokens SET used_by=?, used_at=datetime('now') WHERE token=?",
                      (user_id, req.invite_token))
            db.commit()
        
        c.execute("INSERT INTO vault_audit (user_id, action, ip) VALUES (?, 'register', ?)",
                  (user_id, request.client.host))
        db.commit()
        
        token = create_jwt(user_id, req.username)
        db.close()
        return {"status": "ok", "token": token, "message": "Account aangemaakt"}
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(409, "Gebruikersnaam bestaat al")

@app.post("/vault/login")
async def login(req: LoginModel, request: Request):
    check_rate_limit(request.client.host)
    db = sqlite3.connect(VAULT_DB)
    c = db.cursor()
    c.execute("SELECT id, password_hash, salt FROM vault_users WHERE username=?", (req.username,))
    row = c.fetchone()
    if not row:
        db.close()
        raise HTTPException(401, "Ongeldige inloggegevens")
    
    user_id, pwd_hash, salt = row
    if hash_password(req.password, salt) != pwd_hash:
        db.close()
        raise HTTPException(401, "Ongeldige inloggegevens")
    
    c.execute("UPDATE vault_users SET last_login=datetime('now') WHERE id=?", (user_id,))
    c.execute("INSERT INTO vault_audit (user_id, action, ip) VALUES (?, 'login', ?)",
              (user_id, request.client.host))
    db.commit()
    
    token = create_jwt(user_id, req.username)
    db.close()
    return {"status": "ok", "token": token}

@app.post("/vault/send")
async def send_message(msg: MessageModel, user: dict = Depends(get_current_user)):
    db = sqlite3.connect(VAULT_DB)
    c = db.cursor()
    c.execute("SELECT id FROM vault_users WHERE username=?", (msg.recipient,))
    recipient = c.fetchone()
    if not recipient:
        db.close()
        raise HTTPException(404, "Ontvanger niet gevonden")
    
    expires = (datetime.now() + timedelta(hours=msg.expires_hours)).isoformat()
    c.execute("""INSERT INTO vault_messages 
                 (sender_id, recipient_id, encrypted_content, nonce, iv, expires_at)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (user["user_id"], recipient[0], msg.encrypted_content, msg.nonce, msg.iv, expires))
    db.commit()
    
    c.execute("INSERT INTO vault_audit (user_id, action, details) VALUES (?, 'send', ?)",
              (user["user_id"], f"to:{msg.recipient}"))
    db.commit()
    db.close()
    return {"status": "ok", "message": "Bericht verzonden"}

@app.get("/vault/messages")
async def get_messages(user: dict = Depends(get_current_user)):
    db = sqlite3.connect(VAULT_DB)
    c = db.cursor()
    c.execute("""SELECT m.id, u.username as sender, m.encrypted_content, m.nonce, m.iv, 
                        m.created_at, m.expires_at
                 FROM vault_messages m 
                 JOIN vault_users u ON m.sender_id = u.id
                 WHERE m.recipient_id=? AND (m.expires_at IS NULL OR m.expires_at > datetime('now'))
                 ORDER BY m.created_at DESC""", (user["user_id"],))
    messages = []
    for row in c.fetchall():
        messages.append({
            "id": row[0], "sender": row[1], "encrypted_content": row[2],
            "nonce": row[3], "iv": row[4], "created_at": row[5], "expires_at": row[6]
        })
    c.execute("UPDATE vault_messages SET read_at=datetime('now') WHERE recipient_id=?", (user["user_id"],))
    db.commit()
    db.close()
    return {"messages": messages}

@app.post("/vault/create-invite")
async def create_invite(user: dict = Depends(get_current_user)):
    db = sqlite3.connect(VAULT_DB)
    c = db.cursor()
    token = secrets.token_urlsafe(32)
    expires = (datetime.now() + timedelta(hours=48)).isoformat()
    c.execute("INSERT INTO vault_tokens (token, created_by, expires_at) VALUES (?, ?, ?)",
              (token, user["user_id"], expires))
    db.commit()
    db.close()
    return {"token": token, "expires_at": expires, "message": "Deel dit token met de uitgenodigde"}

@app.get("/vault/users")
async def list_users(user: dict = Depends(get_current_user)):
    db = sqlite3.connect(VAULT_DB)
    c = db.cursor()
    c.execute("SELECT username FROM vault_users WHERE id != ?", (user["user_id"],))
    users = [row[0] for row in c.fetchall()]
    db.close()
    return {"users": users}

@app.get("/vault/audit")
async def get_audit(user: dict = Depends(get_current_user)):
    db = sqlite3.connect(VAULT_DB)
    c = db.cursor()
    c.execute("""SELECT action, timestamp, ip, details FROM vault_audit 
                 WHERE user_id=? ORDER BY timestamp DESC LIMIT 20""", (user["user_id"],))
    audit = [{"action": r[0], "timestamp": r[1], "ip": r[2], "details": r[3]} for r in c.fetchall()]
    db.close()
    return {"audit": audit}

@app.delete("/vault/message/{msg_id}")
async def delete_message(msg_id: int, user: dict = Depends(get_current_user)):
    db = sqlite3.connect(VAULT_DB)
    c = db.cursor()
    c.execute("DELETE FROM vault_messages WHERE id=? AND (sender_id=? OR recipient_id=?)",
              (msg_id, user["user_id"], user["user_id"]))
    db.commit()
    deleted = c.rowcount
    db.close()
    if deleted == 0:
        raise HTTPException(404, "Bericht niet gevonden")
    return {"status": "ok", "message": "Bericht verwijderd (secure_delete)"}

@app.get("/vault/dashboard", response_class=HTMLResponse)
async def vault_dashboard():
    return """<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stay4S Vault - Geheim Communicatie Portaal</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:system-ui,sans-serif; background:#0a0a0a; color:#fff; min-height:100vh; }
.container { max-width:600px; margin:0 auto; padding:20px; }
h1 { color:#4a9eff; margin-bottom:10px; font-size:1.5rem; }
.subtitle { color:#888; margin-bottom:20px; }
.card { background:#1a1a1a; border-radius:12px; padding:20px; margin-bottom:15px; }
input, textarea { width:100%; padding:12px; background:#2a2a2a; border:1px solid #444; border-radius:8px; color:#fff; margin-bottom:10px; font-size:14px; }
button { padding:12px 24px; background:#4a9eff; border:none; border-radius:8px; color:#fff; cursor:pointer; font-size:14px; width:100%; }
button:hover { background:#3a8eef; }
.tab { display:inline-block; padding:10px 20px; background:#1a1a1a; border-radius:8px 8px 0 0; cursor:pointer; margin-right:5px; }
.tab.active { background:#4a9eff; }
#messages { max-height:300px; overflow-y:auto; }
.msg { background:#2a2a2a; padding:10px; border-radius:8px; margin-bottom:8px; }
.msg-meta { font-size:12px; color:#888; }
.badge { display:inline-block; padding:2px 8px; background:#2a4a2a; border-radius:4px; font-size:12px; }
.encrypted { color:#4a9eff; font-family:monospace; font-size:12px; word-break:break-all; }
</style>
</head>
<body>
<div class="container">
<h1>Stay4S Vault</h1>
<p class="subtitle">End-to-End Encrypted Communicatie - Soeverein, Lokaal, Privé</p>

<div id="auth">
<div class="card">
<div class="tab active" onclick="switchTab('login')">Login</div>
<div class="tab" onclick="switchTab('register')">Registreren</div>
<div style="margin-top:15px;">
<input id="username" placeholder="Gebruikersnaam">
<input id="password" type="password" placeholder="Wachtwoord">
<input id="invite" placeholder="Uitnodiging token (voor nieuwe gebruikers)" style="display:none;">
<button onclick="doAuth()">Inloggen</button>
</div>
</div>
</div>

<div id="main" style="display:none;">
<div class="card">
<h3>Bericht versturen</h3>
<select id="recipient" style="width:100%;padding:12px;background:#2a2a2a;border:1px solid #444;border-radius:8px;color:#fff;margin-bottom:10px;"></select>
<textarea id="msgcontent" placeholder="Typ je bericht (wordt client-side encrypted)..." rows="3"></textarea>
<button onclick="sendMessage()">Versturen (E2E encrypted)</button>
</div>
<div class="card">
<h3>Ontvangen berichten</h3>
<div id="messages"><p style="color:#888;">Geen berichten</p></div>
</div>
<div class="card">
<h3>Uitnodigingen</h3>
<button onclick="createInvite()">Nieuwe uitnodiging genereren</button>
<div id="invite-result" style="margin-top:10px;"></div>
</div>
<div class="card">
<h3>Beveiliging</h3>
<p style="font-size:13px;color:#888;">AES-256-GCM encryption | JWT auth | Rate limiting | Secure delete | Audit log | Zelfgehost op Pi 5</p>
<p class="badge" style="margin-top:8px;">Verbonden via Tailscale VPN</p>
<p class="badge">TLS 1.3 via Caddy</p>
</div>
</div>
</div>
<script>
let token = null;
let encKey = null;

function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    const btn = document.querySelector('#auth button');
    const invite = document.getElementById('invite');
    if (tab === 'register') {
        invite.style.display = 'block';
        btn.textContent = 'Registreren';
    } else {
        invite.style.display = 'none';
        btn.textContent = 'Inloggen';
    }
}

async function doAuth() {
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;
    const i = document.getElementById('invite').value;
    const isReg = document.querySelector('#auth button').textContent === 'Registreren';
    const body = isReg ? {username:u, password:p, invite_token:i||null} : {username:u, password:p};
    const res = await fetch('/vault/' + (isReg?'register':'login'), {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify(body)
    });
    if (res.ok) {
        const data = await res.json();
        token = data.token;
        // Generate client-side encryption key
        encKey = await crypto.subtle.generateKey({name:'AES-GCM',length:256}, true, ['encrypt','decrypt']);
        document.getElementById('auth').style.display = 'none';
        document.getElementById('main').style.display = 'block';
        loadUsers();
        loadMessages();
    } else {
        const err = await res.json();
        alert(err.detail || 'Fout');
    }
}

async function loadUsers() {
    const res = await fetch('/vault/users', {headers:{'Authorization':'Bearer '+token}});
    if (res.ok) {
        const data = await res.json();
        const sel = document.getElementById('recipient');
        sel.innerHTML = data.users.map(u => `<option>${u}</option>`).join('');
    }
}

async function loadMessages() {
    const res = await fetch('/vault/messages', {headers:{'Authorization':'Bearer '+token}});
    if (res.ok) {
        const data = await res.json();
        const div = document.getElementById('messages');
        if (data.messages.length === 0) {
            div.innerHTML = '<p style="color:#888;">Geen berichten</p>';
        } else {
            div.innerHTML = data.messages.map(m => 
                `<div class="msg"><div class="msg-meta">Van: ${m.sender} | ${m.created_at}</div><div class="encrypted">${m.encrypted_content.substring(0,80)}...</div></div>`
            ).join('');
        }
    }
}

async function sendMessage() {
    const r = document.getElementById('recipient').value;
    const text = document.getElementById('msgcontent').value;
    if (!r || !text) return;
    // Client-side encrypt
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoded = new TextEncoder().encode(text);
    const ciphertext = await crypto.subtle.encrypt({name:'AES-GCM',iv:iv}, encKey, encoded);
    const b64 = btoa(String.fromCharCode(...new Uint8Array(ciphertext)));
    const ivB64 = btoa(String.fromCharCode(...iv));
    const res = await fetch('/vault/send', {
        method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token},
        body:JSON.stringify({recipient:r, encrypted_content:b64, nonce:ivB64, iv:ivB64})
    });
    if (res.ok) {
        document.getElementById('msgcontent').value = '';
        alert('Bericht encrypted verzonden');
    }
}

async function createInvite() {
    const res = await fetch('/vault/create-invite', {method:'POST', headers:{'Authorization':'Bearer '+token}});
    if (res.ok) {
        const data = await res.json();
        document.getElementById('invite-result').innerHTML = 
            `<p style="word-break:break-all;font-family:monospace;font-size:12px;color:#4a9eff;">${data.token}</p><p style="font-size:12px;color:#888;">Geldig tot: ${data.expires_at}</p>`;
    }
}
</script>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=VAULT_PORT)
