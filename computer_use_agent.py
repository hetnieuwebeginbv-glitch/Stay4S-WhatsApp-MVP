#!/usr/bin/env python3
"""
Stay4S Computer-Use Agent v2.1
Fixed: model-specific stop tokens, think:false for qwen3, simpler prompt.
"""
import os, sys, time, json, logging, subprocess, tempfile, re
import requests

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger("stay4s.computeruse")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://192.168.2.21:11434")
PRIMARY_MODEL = os.environ.get("COMPUTERUSE_MODEL", "eigen-cyc6")
FALLBACK_MODEL = "qwen3:1.7b"
DISPLAY = ":99"
SCREEN_W, SCREEN_H = 1280, 720
MAX_STEPS = 20
ALLOWED_APPS = ["mousepad", "thunar", "firefox-esr", "xterm", "galculator"]
PROOF_DIR = "/tmp/computer_use_proof"
os.makedirs(PROOF_DIR, exist_ok=True)

def take_screenshot(label="step"):
    path = os.path.join(PROOF_DIR, f"{label}_{int(time.time())}.png")
    subprocess.run(["scrot", path], check=True, env={**os.environ, "DISPLAY": DISPLAY})
    return path

def ocr_screenshot(image_path):
    result = subprocess.run(["tesseract", image_path, "-", "--psm", "6"],
                          capture_output=True, text=True, timeout=10)
    text = result.stdout.strip()
    if len(text) > 1000:
        text = text[:1000] + "\n[...]"
    return text

def get_screen_state():
    img_path = take_screenshot("state")
    screen_text = ocr_screenshot(img_path)
    try:
        title = subprocess.run(["xdotool", "getactivewindow", "getwindowname"],
                             capture_output=True, text=True, env={**os.environ, "DISPLAY": DISPLAY}, timeout=5)
        active_win = title.stdout.strip()
    except:
        active_win = "onbekend"
    return {"screen_text": screen_text, "active_window": active_win, "screenshot": img_path}

def ask_model(model, messages, timeout=60):
    """Vraag model via /api/chat met model-specifieke parameters."""
    if "eigen" in model.lower():
        stop_tokens = ["<|eot|>", "<|user|>", "<|assistant|>"]
        extra_body = {}
    else:
        stop_tokens = ["<|im_end|>"]
        extra_body = {"think": False}
    try:
        body = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 300,
                "num_ctx": 2048,
                "top_p": 0.9,
                "stop": stop_tokens,
            },
        }
        body.update(extra_body)
        resp = requests.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("message", {}).get("content", "").strip()
            if not content:
                logger.warning(f"{model} returned empty content")
            return content if content else None
        logger.warning(f"{model} HTTP {resp.status_code}")
        return None
    except requests.exceptions.Timeout:
        logger.warning(f"{model} timeout ({timeout}s)")
        return None
    except Exception as e:
        logger.error(f"{model} error: {e}")
        return None

def parse_command(response):
    """Parse AI response naar commando. Ondersteunt plain text en JSON."""
    if not response:
        return None
    response = response.strip()
    patterns = [
        r'(TYPE:\s*.+)',
        r'(PRESS:\s*[\w+\-]+)',
        r'(CLICK:\s*\d+\s*,\s*\d+)',
        r'(OPEN:\s*\w+)',
        r'(DONE)',
        r'(SCREENSHOT)',
        r'(WAIT:\s*[\d.]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    try:
        json_match = re.search(r'\{[^}]+\}', response)
        if json_match:
            data = json.loads(json_match.group())
            if "action" in data:
                return data["action"]
            if "command" in data:
                return data["command"]
    except (json.JSONDecodeError, AttributeError):
        pass
    resp_lower = response.lower()
    if "done" in resp_lower or "klaar" in resp_lower:
        return "DONE"
    if "enter" in resp_lower:
        return "PRESS: enter"
    if "type" in resp_lower and ":" in response:
        # Try to extract what comes after the colon
        parts = response.split(":", 1)
        if len(parts) > 1 and parts[1].strip():
            return f"TYPE: {parts[1].strip()}"
    return None

def execute_action(action):
    """Voer actie uit via xdotool met safety checks."""
    action = action.strip()
    parts = action.split(":", 1)
    cmd = parts[0].strip().upper()
    params = parts[1].strip() if len(parts) > 1 else ""
    env = {**os.environ, "DISPLAY": DISPLAY}
    try:
        if cmd == "TYPE":
            text = params[:200]
            subprocess.run(["xdotool", "type", "--delay", "80", text], env=env, check=True, timeout=30)
            return {"status": "ok", "action": f"typed: {text[:50]}"}
        elif cmd == "CLICK":
            coords = params.split(",")
            x, y = int(coords[0].strip()), int(coords[1].strip())
            if 0 <= x <= SCREEN_W and 0 <= y <= SCREEN_H:
                subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], env=env, check=True, timeout=10)
                return {"status": "ok", "action": f"clicked: {x},{y}"}
            return {"status": "error", "action": "out of bounds"}
        elif cmd == "PRESS":
            key = params.lower().strip()
            blocked = ["alt+f4", "ctrl+alt+del"]
            if key in blocked:
                return {"status": "error", "action": f"blocked: {key}"}
            subprocess.run(["xdotool", "key", key], env=env, check=True, timeout=10)
            return {"status": "ok", "action": f"pressed: {key}"}
        elif cmd == "WAIT":
            secs = min(float(params) if params else 1.0, 5.0)
            time.sleep(secs)
            return {"status": "ok", "action": f"waited: {secs}s"}
        elif cmd == "OPEN":
            app = params.strip()
            if app not in ALLOWED_APPS:
                return {"status": "error", "action": f"BLOCKED: {app}"}
            subprocess.Popen([app], env=env, start_new_session=True)
            time.sleep(3)
            return {"status": "ok", "action": f"opened: {app}"}
        elif cmd == "SCREENSHOT":
            img = take_screenshot("action")
            text = ocr_screenshot(img)
            return {"status": "ok", "action": "screenshot", "screen_text": text}
        elif cmd == "DONE":
            return {"status": "done", "action": "task complete"}
        else:
            return {"status": "error", "action": f"unknown: {cmd}"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "action": f"timeout: {cmd}"}
    except Exception as e:
        return {"status": "error", "action": f"error: {str(e)[:80]}"}

PROMPT_TMPL = "Je bent een computer-use AI. Je ziet dit scherm:\n\n{screen_text}\n\nTaak: {task}\n\nGeef EEN commando. Alleen het commando.\nCommandos: TYPE: <tekst> | PRESS: enter | OPEN: mousepad | DONE\n\nCommando:"

def run_task(task, max_steps=MAX_STEPS):
    logger.info(f"=== START TAAK: {task} ===")
    os.environ["DISPLAY"] = DISPLAY
    xvfb_check = subprocess.run(["pgrep", "-f", "Xvfb :99"], capture_output=True, text=True)
    if xvfb_check.returncode != 0:
        subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", f"{SCREEN_W}x{SCREEN_H}x24"], start_new_session=True)
        time.sleep(2)
    steps = []
    model_used = PRIMARY_MODEL
    fallback_used = False
    for step_num in range(1, max_steps + 1):
        state = get_screen_state()
        screen_text = state["screen_text"] or "[leeg scherm]"
        prompt = PROMPT_TMPL.format(task=task, screen_text=screen_text)
        logger.info(f"Stap {step_num}: Vraag {model_used}...")
        messages = [{"role": "user", "content": prompt}]
        ai_response = ask_model(model_used, messages, timeout=60)
        if ai_response is None and not fallback_used:
            logger.warning(f"{model_used} faalde, fallback naar {FALLBACK_MODEL}")
            model_used = FALLBACK_MODEL
            fallback_used = True
            ai_response = ask_model(model_used, messages, timeout=90)
        if ai_response is None:
            logger.error("Beide modellen faalden")
            steps.append({"step": step_num, "error": "both models failed"})
            break
        logger.info(f"AI ({model_used}): {ai_response[:120]}")
        command = parse_command(ai_response)
        if command is None:
            logger.warning(f"Geen commando gevonden in: {ai_response[:80]}")
            if not fallback_used:
                model_used = FALLBACK_MODEL
                fallback_used = True
                logger.info(f"Opnieuw met {model_used}...")
                ai_response = ask_model(model_used, messages, timeout=90)
                command = parse_command(ai_response)
            if command is None:
                steps.append({"step": step_num, "ai_response": ai_response[:200], "error": "unparseable"})
                continue
        logger.info(f"Commando: {command}")
        result = execute_action(command)
        proof_path = take_screenshot(f"step{step_num}_after")
        steps.append({
            "step": step_num,
            "model": model_used,
            "screen_before": screen_text[:200],
            "ai_response": ai_response[:200],
            "command": command,
            "result": result,
            "screenshot_after": proof_path,
        })
        if result.get("status") == "done":
            logger.info(f"=== VOLTOOID in {step_num} stappen ===")
            return {"status": "complete", "steps": steps, "total_steps": step_num,
                    "model_used": model_used, "fallback_used": fallback_used}
        time.sleep(1)
    logger.warning(f"=== MAX STAPPEN ({max_steps}) ===")
    return {"status": "max_steps", "steps": steps, "total_steps": max_steps,
            "model_used": model_used, "fallback_used": fallback_used}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stay4S Computer-Use Agent v2.1")
    parser.add_argument("--task", type=str, required=True)
    parser.add_argument("--steps", type=int, default=MAX_STEPS)
    parser.add_argument("--model", type=str, default=PRIMARY_MODEL)
    args = parser.parse_args()
    if args.model:
        PRIMARY_MODEL = args.model
    result = run_task(args.task, max_steps=args.steps)
    print(json.dumps(result, indent=2, ensure_ascii=False))
