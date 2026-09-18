"""
StayLM Client -- Ollama primary (Pi 5 local), RunPod fallback.
Ollama: lokaal, geen cold start, gratis, ~25s per response op Pi 5.
RunPod: hogere kwaliteit (staylm2:1, 8B) maar cold start 90-180s.
"""
import httpx
import os
import logging
import asyncio

logger = logging.getLogger("stay4s.whatsapp")

RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
STAYLM2_ENDPOINT = os.environ.get("STAYLM2_ENDPOINT", "zk3607hf3f9pso")
STAYLM2_FALLBACK = os.environ.get("STAYLM2_FALLBACK", "zk3607hf3f9pso")
RUNPOD_BASE = f"https://api.runpod.ai/v2/{STAYLM2_ENDPOINT}"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:1.7b")


async def generate_response(prompt, context="", max_tokens=512, temperature=0.7):
    full_prompt = f"{context}\n\nVraag: {prompt}\nAntwoord: " if context else f"{prompt}"

    # 1. Ollama first (local, no cold start)
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": full_prompt, "stream": False,
                      "options": {"temperature": temperature, "num_predict": max_tokens}}
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("response", "").strip()
                if text:
                    logger.info(f"Ollama responded ({len(text)} chars)")
                    return {"text": text, "source": "ollama", "confidence": 0.75}
            else:
                logger.error(f"Ollama HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"Ollama failed: {e}")

    # 2. RunPod fallback (higher quality, but may have cold start)
    if RUNPOD_API_KEY:
        primary = f"https://api.runpod.ai/v2/{STAYLM2_ENDPOINT}"
        secondary = f"https://api.runpod.ai/v2/{STAYLM2_FALLBACK}"
        for ep in (primary, secondary):
            if ep == primary and STAYLM2_ENDPOINT == STAYLM2_FALLBACK:
                ep = secondary  # zelfde endpoint, geen dubbel
            try:
                result = await _runpod_async(full_prompt, max_tokens, temperature, endpoint=ep)
                if result:
                    return result
            except Exception as e:
                logger.error(f"RunPod {ep} failed: {e}")

    return {"text": "Sorry, ik ben momenteel niet bereikbaar. Probeer het later opnieuw of neem contact op via telefoon.", "source": "error", "confidence": 0.0}


async def _runpod_async(prompt, max_tokens, temperature, endpoint=None):
    ep = endpoint or RUNPOD_BASE
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}", "Content-Type": "application/json"}
    body = {"input": {"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature, "top_p": 0.9}}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{ep}/run", headers=headers, json=body)
        if resp.status_code != 200:
            logger.error(f"RunPod /run HTTP {resp.status_code}")
            return None

        data = resp.json()
        if isinstance(data, list):
            data = data[0] if data else {}
        job_id = data.get("id")
        if not job_id:
            return None

        logger.info(f"RunPod job: {job_id[:25]}...")

        for i in range(36):
            await asyncio.sleep(5)
            try:
                sr = await client.get(f"{ep}/status/{job_id}", headers=headers)
                if sr.status_code == 200:
                    sdata = sr.json()
                    if isinstance(sdata, list):
                        sdata = sdata[0] if sdata else {}
                    if not isinstance(sdata, dict):
                        continue
                    status = sdata.get("status", "")

                    if status == "COMPLETED":
                        output = sdata.get("output", {})
                        if isinstance(output, list):
                            output = output[0] if output else {}
                        text = output.get("response", output.get("text", ""))
                        if not text and isinstance(output.get("choices"), list) and output["choices"]:
                            text = output["choices"][0].get("text", "")
                        if text:
                            logger.info(f"RunPod completed after {(i+1)*5}s")
                            return {"text": text.strip(), "source": "runpod", "confidence": 0.85}
                        return None
                    elif status == "FAILED":
                        logger.error(f"RunPod failed: {sdata.get('error', '?')}")
                        return None
                    elif status in ("IN_QUEUE", "IN_PROGRESS"):
                        if i % 6 == 0:
                            logger.info(f"RunPod {status} ({(i+1)*5}s)")
            except Exception as e:
                logger.error(f"RunPod poll error: {e}")

    logger.error("RunPod timed out after 180s")
    return None