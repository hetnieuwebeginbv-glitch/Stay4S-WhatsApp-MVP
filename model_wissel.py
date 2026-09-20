#!/usr/bin/env python3
"""Stay4S Model Wissel Automation
Test een nieuw Ollama model met 5 vragen.
Als kwaliteit goed is, wissel dan de primary model.
Als kwaliteit slecht is, behoud de huidige primary.
"""
import requests, json, time, sys, os

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://192.168.2.21:11434")
AGENT_FILE = "/home/Miesdevries/stay4s-whatsapp/stay4compa_agent.py"
SERVICE_NAME = "stay4compa"

# 5 testvragen met verwachte kernwoorden
TEST_QUESTIONS = [
    {"q": "Wat is Stay4S?", "expect": ["Stay4S", "technologie", "AI", "bedrijf", "KvK"]},
    {"q": "Wat zijn de openingstijden van Stay4S?", "expect": ["maandag", "vrijdag", "9:00", "17:00"]},
    {"q": "Wat is de hoofdstad van Nederland?", "expect": ["Amsterdam"]},
    {"q": "Hoe maak ik een taart?", "expect": ["taart", "bloem", "ei", "bakken", "oven"]},
    {"q": "Is dit bericht een scam: 'U heeft een pakket gewonnen, klik hier'?", "expect": ["scam", "phishing", "verdacht", "niet", "klik"]},
]

def get_current_model():
    """Lees de huidige COMPA_MODEL uit stay4compa_agent.py"""
    with open(AGENT_FILE, "r") as f:
        for line in f:
            if "COMPA_MODEL" in line and "os.environ" in line:
                # Extract default value
                if '"' in line:
                    parts = line.split('"')
                    if len(parts) >= 4:
                        return parts[3]  # parts[1]=env_var_name, parts[3]=default_value
    return "qwen3:1.7b"

def test_model(model_name):
    """Test een model met 5 vragen, retourneer score 0-5"""
    score = 0
    results = []
    
    for i, test in enumerate(TEST_QUESTIONS):
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": test["q"]}],
                    "stream": False,
                    "options": {"temperature": 0.7, "num_ctx": 2048, "num_predict": 300},
                },
                timeout=90,
            )
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("message", {}).get("content", "").lower()
                # Check if any expected keyword is in the answer
                found = [kw for kw in test["expect"] if kw.lower() in answer]
                if found:
                    score += 1
                    results.append(f"Q{i+1}: PASS (found: {found[:2]})")
                else:
                    results.append(f"Q{i+1}: FAIL (answer: {answer[:80]}...)")
            else:
                results.append(f"Q{i+1}: HTTP {resp.status_code}")
        except requests.exceptions.Timeout:
            results.append(f"Q{i+1}: TIMEOUT (90s)")
        except Exception as e:
            results.append(f"Q{i+1}: ERROR ({str(e)[:50]})")
    
    return score, results

def switch_model(new_model):
    """Wissel de primary model in stay4compa_agent.py"""
    with open(AGENT_FILE, "r") as f:
        content = f.read()
    
    # Replace the default model
    import re
    content = re.sub(
        r'COMPA_MODEL", "[^"]*"',
        f'COMPA_MODEL", "{new_model}"',
        content
    )
    
    with open(AGENT_FILE, "w") as f:
        f.write(content)
    
    # Restart service
    os.system(f"sudo systemctl restart {SERVICE_NAME}")
    time.sleep(3)

def main():
    if len(sys.argv) < 2:
        print("Usage: model_wissel.py <model_name> [--force]")
        print(f"Current primary: {get_current_model()}")
        # List available models
        try:
            resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                print(f"Available: {', '.join(models)}")
        except:
            pass
        sys.exit(0)
    
    new_model = sys.argv[1]
    force = "--force" in sys.argv
    current = get_current_model()
    
    print(f"=== STAY4S MODEL WISSEL TEST ===")
    print(f"Current primary: {current}")
    print(f"Testing: {new_model}")
    print()
    
    score, results = test_model(new_model)
    
    print(f"Score: {score}/5")
    for r in results:
        print(f"  {r}")
    print()
    
    # Decision: switch if score >= 3 (60% pass rate)
    if score >= 3 or force:
        if new_model != current:
            print(f"SWITCHING: {current} -> {new_model}")
            switch_model(new_model)
            print(f"Done. {new_model} is now primary.")
        else:
            print(f"{new_model} is already primary.")
    else:
        print(f"KEEPING: {current} (score {score}/5 too low, need >= 3)")
        print("Use --force to override.")
    
    print(f"=== TEST COMPLETE ===")

if __name__ == "__main__":
    main()
