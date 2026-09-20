#!/usr/bin/env python3
"""Stay4S Quality Monitor
Test de AI-agent periodiek met standaardvragen.
Meet response tijd, kwaliteit, en service health.
Slaat resultaten op in stay4s.db voor trending.
"""
import requests, json, time, sqlite3, os, subprocess
from datetime import datetime

DB_PATH = "/home/Miesdevries/stay4s-whatsapp/stay4s.db"
COMPA_URL = "http://localhost:8082"
WEBHOOK_URL = "http://localhost:8081"
VAULT_URL = "http://localhost:8083"
OLLAMA_URL = "http://192.168.2.21:11434"

# Standaard testvragen met verwachte kernwoorden
TEST_QUESTIONS = [
    {"q": "Wat is Stay4S?", "expect": ["stay4s", "technologie", "ai", "bedrijf", "kvk"]},
    {"q": "Wat zijn de openingstijden?", "expect": ["maandag", "vrijdag", "9", "17"]},
    {"q": "Wat is Stay4Safe AI?", "expect": ["scam", "phishing", "veilig", "detect"]},
    {"q": "Hoe kan ik contact opnemen?", "expect": ["whatsapp", "email", "telefoon", "contact"]},
    {"q": "Wat kost de WhatsApp AI?", "expect": ["prijs", "eur", "kosten", "abonnement"]},
]

def init_quality_table():
    db = sqlite3.connect(DB_PATH)
    c = db.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS quality_monitor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT (datetime('now')),
        service TEXT NOT NULL,
        metric TEXT NOT NULL,
        value TEXT NOT NULL,
        details TEXT
    )""")
    db.commit()
    db.close()

def check_service(name, url, health_path="/health"):
    """Check if a service is responding."""
    try:
        start = time.time()
        resp = requests.get(f"{url}{health_path}", timeout=10)
        elapsed = time.time() - start
        if resp.status_code == 200:
            return {"status": "ok", "latency_ms": round(elapsed * 1000), "response": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:200]}
        return {"status": "error", "code": resp.status_code}
    except Exception as e:
        return {"status": "down", "error": str(e)[:100]}

def test_compa_agent():
    """Test Stay4Compa met standaardvragen."""
    results = []
    for i, test in enumerate(TEST_QUESTIONS):
        try:
            start = time.time()
            resp = requests.post(
                f"{COMPA_URL}/chat",
                json={"message": test["q"], "phone": f"monitor_{int(time.time())}", "name": "Monitor"},
                timeout=120,
            )
            elapsed = time.time() - start
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("response", "").lower()
                # Check if any expected keyword is in the answer
                found = [kw for kw in test["expect"] if kw in answer]
                score = len(found) / len(test["expect"])
                results.append({
                    "question": test["q"],
                    "answer": data.get("response", "")[:200],
                    "score": score,
                    "passed": score >= 0.2,
                    "latency_s": round(elapsed, 1),
                    "tools_used": data.get("tools_used", []),
                })
            else:
                results.append({"question": test["q"], "error": f"HTTP {resp.status_code}", "score": 0, "passed": False})
        except Exception as e:
            results.append({"question": test["q"], "error": str(e)[:100], "score": 0, "passed": False})
        time.sleep(1)  # Avoid overwhelming the model
    return results

def check_ollama():
    """Check Ollama models and status."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return {"status": "ok", "models": models}
        return {"status": "error", "code": resp.status_code}
    except Exception as e:
        return {"status": "down", "error": str(e)[:100]}

def check_disk():
    """Check disk space."""
    result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")
    if len(lines) > 1:
        parts = lines[1].split()
        return {"total": parts[1], "used": parts[2], "avail": parts[3], "used_pct": parts[4]}

def check_ram():
    """Check RAM."""
    with open("/proc/meminfo") as f:
        mem = {}
        for line in f:
            p = line.split()
            if p[0] in ["MemTotal:", "MemAvailable:"]:
                mem[p[0]] = int(p[1])
    total = mem.get("MemTotal:", 0) / 1024
    avail = mem.get("MemAvailable:", 0) / 1024
    return {"total_mb": round(total), "available_mb": round(avail)}

def save_metric(service, metric, value, details=""):
    db = sqlite3.connect(DB_PATH)
    c = db.cursor()
    c.execute("INSERT INTO quality_monitor (service, metric, value, details) VALUES (?, ?, ?, ?)",
              (service, metric, str(value), details))
    db.commit()
    db.close()

def run_monitor():
    """Run full quality monitoring cycle."""
    init_quality_table()
    print(f"=== Stay4S Quality Monitor -- {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    print()

    # 1. Service health
    print("--- Service Health ---")
    services = {
        "webhook": (WEBHOOK_URL, "/health"),
        "compa": (COMPA_URL, "/health"),
        "vault": (VAULT_URL, "/health"),
    }
    for name, (url, path) in services.items():
        result = check_service(name, url, path)
        status = result["status"]
        latency = result.get("latency_ms", "N/A")
        print(f"  {name}: {status} ({latency}ms)")
        save_metric(name, "health", status, json.dumps(result))
        if status == "ok" and "latency_ms" in result:
            save_metric(name, "latency_ms", result["latency_ms"])

    # 2. Ollama
    print()
    print("--- Ollama ---")
    ollama = check_ollama()
    print(f"  Status: {ollama['status']}")
    if "models" in ollama:
        print(f"  Models: {', '.join(ollama['models'])}")
    save_metric("ollama", "status", ollama["status"], json.dumps(ollama))

    # 3. System
    print()
    print("--- System ---")
    disk = check_disk()
    ram = check_ram()
    print(f"  Disk: {disk['used_pct']} used ({disk['avail']} avail)")
    print(f"  RAM: {ram['available_mb']}MB available ({ram['total_mb']}MB total)")
    save_metric("system", "disk_used_pct", disk["used_pct"])
    save_metric("system", "ram_available_mb", ram["available_mb"])

    # 4. AI Quality (only if compa is healthy)
    print()
    print("--- AI Quality ---")
    compa_health = check_service("compa", COMPA_URL, "/health")
    if compa_health["status"] == "ok":
        results = test_compa_agent()
        passed = sum(1 for r in results if r.get("passed"))
        total = len(results)
        avg_score = sum(r.get("score", 0) for r in results) / total if total else 0
        avg_latency = sum(r.get("latency_s", 0) for r in results) / total if total else 0
        print(f"  Tests: {passed}/{total} passed")
        print(f"  Avg score: {avg_score:.2f}")
        print(f"  Avg latency: {avg_latency:.1f}s")
        for r in results:
            status = "PASS" if r.get("passed") else "FAIL"
            score = r.get("score", 0)
            latency = r.get("latency_s", "N/A")
            print(f"    [{status}] {r['question'][:30]} -> score={score:.0%} ({latency}s)")
        save_metric("compa", "quality_score", avg_score, json.dumps(results))
        save_metric("compa", "quality_passed", f"{passed}/{total}")
        save_metric("compa", "avg_latency_s", avg_latency)
    else:
        print("  SKIPPED (compa not healthy)")

    print()
    print("=== Monitor Complete ===")

if __name__ == "__main__":
    run_monitor()