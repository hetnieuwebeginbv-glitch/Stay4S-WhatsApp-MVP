#!/usr/bin/env python3
"""
Stay4S Computer-Use Agent v3.0
Verbeteringen t.o.v. v2.1:
- Conversation history: model weet wat het al gedaan heeft (geen loops)
- Multi-command splitting: splitst response op | of nieuwe regels
- State tracking: vertelt model wat de volgende stap is
- Beter prompt: duidelijke instructie over voortgang
"""
import os, sys, time, json, logging, subprocess, re
import requests

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger("stay4s.computeruse")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://192.168.2.21:11434")
PRIMARY_MODEL = os.environ.get("COMPUTERUSE_MODEL", "eigen-cyc6")
FALLBACK_MODEL = "qwen3:1.7b"
DISPLAY = ":99"
SCREEN_W, SCREEN_H = 1280, 720
MAX_STEPS = 15
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
    if len(text) > 800:
        text = text[:800] + "\n[...]"
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
    """Vraag model via /api/chat met model-specifieke parameters + conversation history."""
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
                "num_predict": 200,
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
            return content if content else None
        return None
    except Exception as e:
        logger.error(f"{model} error: {e}")
        return None

def split_multi_command(response):
    """Split multi-command response op |, nieuwe regels, of slashes."""
    if not response:
        return []
    commands = []
    # Split op | of nieuwe regels
    parts = re.split(r'[|\n]', response)
    for part in parts:
        part = part.strip()
        if part:
            cmd = parse_command(part)
            if cmd:
                commands.append(cmd)
    return commands if commands else []

def parse_command(response):
    """Parse AI response naar een commando."""
    if not response:
        return None
    response = response.strip()
    patterns = [
        r'(TYPE:\s*.+)',
        r'(PRESS:\s*[\w+\-]+)',
        r'(CLICK:\s*\d+\s*,\s*\d+)',
        r'(OPEN:\s*\w+)',
        r'(DONE)',
        r'(WAIT:\s*[\d.]+)',
        r'(SCROLL:\s*\w+)',
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
    except:
        pass
    resp_lower = response.lower()
    if any(w in resp_lower for w in ["done", "klaar", "voltooid", "finished", "sluit", "sluiten", "close"]):
        return "DONE"
    if "enter" in resp_lower and "press" in resp_lower:
        return "PRESS: enter"
    if "enter" in resp_lower and len(resp_lower) < 20:
        return "PRESS: enter"
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
            # Map common names to xdotool key names
            key_map = {"enter": "Return", "return": "Return", "esc": "Escape",
                       "escape": "Escape", "tab": "Tab", "space": "space",
                       "backspace": "BackSpace", "delete": "Delete"}
            key = key_map.get(key, key)
            if key in ["alt+f4", "ctrl+alt+del"]:
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
        elif cmd == "DONE":
            return {"status": "done", "action": "task complete"}
        else:
            return {"status": "error", "action": f"unknown: {cmd}"}
    except Exception as e:
        return {"status": "error", "action": f"error: {str(e)[:80]}"}

def build_prompt_with_history(task, screen_text, action_history):
    """Bouw prompt met conversation history zodat model voortgang kent."""
    history_str = ""
    if action_history:
        history_str = "\n\nEerdere acties (al uitgevoerd):\n"
        for i, (cmd, result) in enumerate(action_history, 1):
            status = "OK" if result.get("status") == "ok" else "FOUT"
            history_str += f"  {i}. {cmd} -> {status}\n"
        history_str += "\nJe hebt al acties uitgevoerd. Ga door met de VOLGENDE stap.\n"
    else:
        history_str = "\nDit is de eerste stap. Begin met de taak.\n"
    
    prompt = f"""Je bent een computer-use AI op een Linux desktop.

Scherm tekst:
{screen_text}

Taak: {task}{history_str}
Geef EEN commando voor de volgende stap. Alleen het commando.
Commandos: TYPE: <tekst> | PRESS: enter | PRESS: tab | OPEN: mousepad | DONE

Als de taak klaar is, zeg: DONE
Commando:"""
    return prompt

def run_task(task, max_steps=MAX_STEPS):
    logger.info(f"=== START TAAK: {task} ===")
    os.environ["DISPLAY"] = DISPLAY
    
    # Ensure Xvfb + openbox
    xvfb_check = subprocess.run(["pgrep", "-f", "Xvfb :99"], capture_output=True, text=True)
    if xvfb_check.returncode != 0:
        subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", f"{SCREEN_W}x{SCREEN_H}x24"], start_new_session=True)
        time.sleep(2)
    ob_check = subprocess.run(["pgrep", "-f", "openbox"], capture_output=True, text=True)
    if ob_check.returncode != 0:
        subprocess.Popen(["openbox"], env={**os.environ, "DISPLAY": DISPLAY}, start_new_session=True)
        time.sleep(2)
    
    steps = []
    action_history = []  # Track wat de AI al gedaan heeft
    model_used = PRIMARY_MODEL
    fallback_used = False
    conversation = []  # Full conversation history for the model
    
    for step_num in range(1, max_steps + 1):
        # 1. Schermstatus
        state = get_screen_state()
        screen_text = state["screen_text"] or "[leeg scherm]"
        
        # 2. Bouw prompt MET history
        prompt = build_prompt_with_history(task, screen_text, action_history)
        
        # 3. Voeg toe aan conversation (houd laatste 5 messages voor context)
        user_msg = {"role": "user", "content": prompt}
        conversation.append(user_msg)
        if len(conversation) > 6:
            conversation = conversation[-6:]
        
        # 4. Vraag AI
        logger.info(f"Stap {step_num}: Vraag {model_used}...")
        ai_response = ask_model(model_used, conversation, timeout=60)
        
        if ai_response is None and not fallback_used:
            logger.warning(f"{model_used} faalde, fallback naar {FALLBACK_MODEL}")
            model_used = FALLBACK_MODEL
            fallback_used = True
            ai_response = ask_model(model_used, conversation, timeout=90)
        
        if ai_response is None:
            steps.append({"step": step_num, "error": "both models failed"})
            break
        
        # Voeg AI response toe aan conversation
        conversation.append({"role": "assistant", "content": ai_response})
        
        logger.info(f"AI ({model_used}): {ai_response[:100]}")
        
        # 5. Parse commando(s) -- probeer multi-command split
        commands = split_multi_command(ai_response)
        if not commands:
            single = parse_command(ai_response)
            commands = [single] if single else []
        
        if not commands:
            logger.warning(f"Geen commando in: {ai_response[:80]}")
            if not fallback_used:
                model_used = FALLBACK_MODEL
                fallback_used = True
                ai_response = ask_model(model_used, conversation, timeout=90)
                commands = split_multi_command(ai_response) or ([parse_command(ai_response)] if parse_command(ai_response) else [])
            if not commands:
                steps.append({"step": step_num, "ai_response": ai_response[:200], "error": "unparseable"})
                action_history.append(("(unparseable)", {"status": "error"}))
                continue
        
        # 6. Voer elk commando uit (max 2 per stap voor safety)
        for cmd in commands[:2]:
            logger.info(f"Uitvoeren: {cmd}")
            result = execute_action(cmd)
            action_history.append((cmd, result))
            
            # Screenshot na actie
            proof_path = take_screenshot(f"step{step_num}_after")
            
            steps.append({
                "step": step_num,
                "model": model_used,
                "ai_response": ai_response[:200],
                "command": cmd,
                "result": result,
                "screenshot_after": proof_path,
            })
            
            if result.get("status") == "done":
                logger.info(f"=== VOLTOOID in {step_num} stappen ===")
                return {"status": "complete", "steps": steps, "total_steps": step_num,
                        "model_used": model_used, "fallback_used": fallback_used,
                        "action_history": [h[0] for h in action_history]}
            
            time.sleep(0.5)
        
        time.sleep(1)
    
    logger.warning(f"=== MAX STAPPEN ({max_steps}) ===")
    return {"status": "max_steps", "steps": steps, "total_steps": max_steps,
            "model_used": model_used, "fallback_used": fallback_used,
            "action_history": [h[0] for h in action_history]}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stay4S Computer-Use Agent v3.0")
    parser.add_argument("--task", type=str, required=True)
    parser.add_argument("--steps", type=int, default=MAX_STEPS)
    parser.add_argument("--model", type=str, default=PRIMARY_MODEL)
    args = parser.parse_args()
    if args.model:
        PRIMARY_MODEL = args.model
    result = run_task(args.task, max_steps=args.steps)
    print(json.dumps(result, indent=2, ensure_ascii=False))