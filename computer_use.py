"""
Stay4S Computer-Use Wrapper.
Laat de eigen-SFT-AI (1.67B via Ollama) een computer besturen.
Pi 5 met Xvfb virtueel display = veilige testomgeving.

Architectuur:
  Eigen-SFT-AI (tekst in) -> actie commando (tekst uit) -> pyautogui (uitvoeren)
  Screenshot -> OCR -> tekst -> terug naar AI

Onveilig? NEE. Alles draait op Xvfb virtueel display, niet op Mitchell's scherm.
"""
import os
import sys
import time
import json
import logging
import subprocess
import tempfile

import requests

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger("stay4s.computeruse")

# Ollama config
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("COMPUTERUSE_MODEL", "qwen3:1.7b")

# Display config
DISPLAY = ":99"
SCREEN_W = 1280
SCREEN_H = 720

# Safety
MAX_STEPS = 20
ALLOWED_APPS = ["mousepad", "thunar", "firefox-esr", "xterm", "galculator"]


def start_virtual_display():
    """Start Xvfb virtueel display (veilig, geen echte scherm)."""
    try:
        subprocess.run(["Xvfb", DISPLAY, "-screen", "0", f"{SCREEN_W}x{SCREEN_H}x24"], 
                      check=False, start_new_session=True)
        time.sleep(2)
        os.environ["DISPLAY"] = DISPLAY
        logger.info(f"Virtueel display gestart op {DISPLAY} ({SCREEN_W}x{SCREEN_H})")
        return True
    except Exception as e:
        logger.error(f"Kan Xvfb niet starten: {e}")
        return False


def take_screenshot():
    """Maak screenshot van virtueel display."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    subprocess.run(["scrot", tmp.name], check=True, env={**os.environ, "DISPLAY": DISPLAY})
    return tmp.name


def ocr_screenshot(image_path):
    """OCR de screenshot -> tekst representatie van scherm."""
    result = subprocess.run(["tesseract", image_path, "-", "--psm", "6"],
                          capture_output=True, text=True)
    text = result.stdout.strip()
    # Cleanup
    os.unlink(image_path)
    # Beperk tekst lengte voor AI context
    if len(text) > 2000:
        text = text[:2000] + "\n[...afgekapt...]"
    return text


def get_active_window():
    """Krijg actieve window titel en positie."""
    try:
        title = subprocess.run(["xdotool", "getactivewindow", "getwindowname"],
                             capture_output=True, text=True, env={**os.environ, "DISPLAY": DISPLAY})
        return title.stdout.strip()
    except Exception:
        return "onbekend"


def execute_action(action: str) -> dict:
    """
    Voer een actie uit. Actie format: "COMMAND: params"
    
    Ondersteunde acties:
      TYPE: <tekst>          - Typ tekst op cursor positie
      CLICK: <x>,<y>         - Links klik op coordinaten
      DOUBLE_CLICK: <x>,<y>  - Dubbel klik
      RIGHT_CLICK: <x>,<y>   - Rechts klik
      PRESS: <key>           - Druk toets (enter, tab, escape, ctrl+s, etc.)
      SCROLL: <direction>    - Scroll (up, down)
      WAIT: <seconds>        - Wacht X seconden
      OPEN: <app>            - Open applicatie (alleen toegestane apps)
      SCREENSHOT             - Neem screenshot + OCR
      DONE                   - Taak voltooid
    """
    action = action.strip()
    parts = action.split(":", 1)
    cmd = parts[0].strip().upper()
    params = parts[1].strip() if len(parts) > 1 else ""
    
    env = {**os.environ, "DISPLAY": DISPLAY}
    
    try:
        if cmd == "TYPE":
            subprocess.run(["xdotool", "type", "--delay", "50", params],
                         env=env, check=True)
            return {"status": "ok", "action": f"typed: {params[:50]}"}
            
        elif cmd == "CLICK":
            x, y = params.split(",")
            subprocess.run(["xdotool", "mousemove", x.strip(), y.strip(), "click", "1"],
                         env=env, check=True)
            return {"status": "ok", "action": f"clicked: {x},{y}"}
            
        elif cmd == "DOUBLE_CLICK":
            x, y = params.split(",")
            subprocess.run(["xdotool", "mousemove", x.strip(), y.strip(), "click", "--repeat", "2", "1"],
                         env=env, check=True)
            return {"status": "ok", "action": f"double-clicked: {x},{y}"}
            
        elif cmd == "RIGHT_CLICK":
            x, y = params.split(",")
            subprocess.run(["xdotool", "mousemove", x.strip(), y.strip(), "click", "3"],
                         env=env, check=True)
            return {"status": "ok", "action": f"right-clicked: {x},{y}"}
            
        elif cmd == "PRESS":
            subprocess.run(["xdotool", "key", params.lower()],
                         env=env, check=True)
            return {"status": "ok", "action": f"pressed: {params}"}
            
        elif cmd == "SCROLL":
            direction = params.lower()
            if direction == "down":
                subprocess.run(["xdotool", "click", "--repeat", "5", "5"], env=env)
            else:
                subprocess.run(["xdotool", "click", "--repeat", "5", "4"], env=env)
            return {"status": "ok", "action": f"scrolled: {direction}"}
            
        elif cmd == "WAIT":
            secs = float(params) if params else 1.0
            time.sleep(min(secs, 5.0))  # max 5s veiligheid
            return {"status": "ok", "action": f"waited: {secs}s"}
            
        elif cmd == "OPEN":
            app = params.strip()
            if app not in ALLOWED_APPS:
                return {"status": "error", "action": f"blocked: {app} not in allowed list"}
            subprocess.Popen([app], env=env, start_new_session=True)
            time.sleep(2)
            return {"status": "ok", "action": f"opened: {app}"}
            
        elif cmd == "SCREENSHOT":
            img = take_screenshot()
            text = ocr_screenshot(img)
            return {"status": "ok", "action": "screenshot", "screen_text": text}
            
        elif cmd == "DONE":
            return {"status": "done", "action": "task complete"}
            
        else:
            return {"status": "error", "action": f"unknown command: {cmd}"}
            
    except Exception as e:
        return {"status": "error", "action": f"execution error: {str(e)}"}


def get_screen_state():
    """Krijg huidige schermstatus als tekst voor de AI."""
    img = take_screenshot()
    screen_text = ocr_screenshot(img)
    active_win = get_active_window()
    return {
        "screen_text": screen_text,
        "active_window": active_win,
        "screen_size": f"{SCREEN_W}x{SCREEN_H}",
    }


def ask_ai(prompt: str) -> str:
    """Stuur prompt naar eigen-SFT-AI via Ollama."""
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 100}
            },
            timeout=90
        )
        data = resp.json()
        return data.get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return f"ERROR: {e}"


SYSTEM_PROMPT = """Je bent Stay4S Computer-Use AI. Je bestuurt een computer via tekstcommandos.

Je ziet het scherm als OCR-tekst. Je geeft acties als commandos.

Beschikbare commandos:
  TYPE: <tekst>          - Typ tekst
  CLICK: <x>,<y>         - Klik op positie
  DOUBLE_CLICK: <x>,<y>  - Dubbelklik
  RIGHT_CLICK: <x>,<y>   - Rechtsklik
  PRESS: <key>           - Druk toets (enter, tab, escape, ctrl+s, ctrl+c, ctrl+v, alt+F4)
  SCROLL: <up|down>      - Scroll
  WAIT: <seconds>        - Wacht
  OPEN: <app>            - Open app (mousepad, thunar, firefox-esr, xterm, galculator)
  DONE                   - Taak klaar

Regels:
- Eén commando per beurt
- Kijk naar de schermtekst om te bepalen wat te doen
- Gebruik coordinaten tussen 0-{SCREEN_W} (x) en 0-{SCREEN_H} (y)
- Als taak klaar is, zeg DONE

Taak: {task}

Scherm tekst:
{screen_text}

Actief venster: {active_window}

Welke actie voer je uit? Geef alleen het commando, niets anders."""


def run_task(task: str, max_steps: int = MAX_STEPS):
    """
    Voer een taak uit met de AI als beslisser.
    Loop: screenshot -> OCR -> AI -> actie -> herhaal
    """
    logger.info(f"Start taak: {task}")
    
    # Start virtueel display
    if not start_virtual_display():
        return {"status": "error", "reason": "Kan virtueel display niet starten"}
    
    steps = []
    for step_num in range(1, max_steps + 1):
        # 1. Krijg schermstatus
        state = get_screen_state()
        screen_text = state["screen_text"]
        active_win = state["active_window"]
        
        if not screen_text.strip():
            screen_text = "[leeg scherm]"
        
        # 2. Bouw prompt voor AI
        prompt = SYSTEM_PROMPT.format(
            task=task,
            screen_text=screen_text,
            active_window=active_win,
            SCREEN_W=SCREEN_W,
            SCREEN_H=SCREEN_H
        )
        
        # 3. Vraag AI wat te doen
        logger.info(f"Stap {step_num}: Vraag AI...")
        ai_response = ask_ai(prompt)
        logger.info(f"AI zegt: {ai_response[:100]}")
        
        # 4. Voer actie uit
        result = execute_action(ai_response)
        steps.append({
            "step": step_num,
            "screen_text": screen_text[:200],
            "ai_command": ai_response,
            "result": result
        })
        
        # 5. Check of klaar
        if result.get("status") == "done":
            logger.info(f"Taak voltooid in {step_num} stappen!")
            return {"status": "complete", "steps": steps, "total_steps": step_num}
        
        # 6. Wacht beetje
        time.sleep(1)
    
    logger.warning(f"Max stappen bereikt ({max_steps})")
    return {"status": "max_steps", "steps": steps, "total_steps": max_steps}


# --- Test scenarios ---

TEST_SCENARIOS = [
    {
        "name": "Tekst editor openen en typen",
        "task": "Open mousepad (teksteditor), typ 'Hallo Stay4S AI', sla op als test.txt",
        "difficulty": "easy",
        "expected_steps": 5,
    },
    {
        "name": "Map maken in bestandsbeheer",
        "task": "Open thunar (bestandsbeheer), maak een nieuwe map aan genaamd 'Stay4S-Test'",
        "difficulty": "easy",
        "expected_steps": 6,
    },
    {
        "name": "Rekenmachine gebruiken",
        "task": "Open galculator (rekenmachine), bereken 5 plus 3",
        "difficulty": "medium",
        "expected_steps": 7,
    },
    {
        "name": "Terminal commando uitvoeren",
        "task": "Open xterm (terminal), typ 'echo Hello Stay4S', druk op enter",
        "difficulty": "easy",
        "expected_steps": 4,
    },
    {
        "name": "Website openen",
        "task": "Open firefox-esr, ga naar stay4s.com",
        "difficulty": "medium",
        "expected_steps": 8,
    },
]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stay4S Computer-Use Agent")
    parser.add_argument("--task", type=str, help="Taak om uit te voeren")
    parser.add_argument("--test", action="store_true", help="Run test scenarios")
    parser.add_argument("--steps", type=int, default=MAX_STEPS, help="Max stappen")
    args = parser.parse_args()
    
    if args.test:
        for scenario in TEST_SCENARIOS:
            print(f"\n{'='*60}")
            print(f"TEST: {scenario['name']} (moeilijkheid: {scenario['difficulty']})")
            print(f"TAAK: {scenario['task']}")
            print(f"VERWACHT: {scenario['expected_steps']} stappen")
            print(f"{'='*60}")
            result = run_task(scenario["task"], max_steps=scenario["expected_steps"] + 5)
            print(f"Resultaat: {result['status']} ({result.get('total_steps', 0)} stappen)")
    elif args.task:
        result = run_task(args.task, max_steps=args.steps)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Stay4S Computer-Use Agent")
        print("Gebruik: --task 'open mousepad en typ hello' of --test")
        print("\nTest scenarios:")
        for s in TEST_SCENARIOS:
            print(f"  - {s['name']}: {s['task']}")