"""
Stay4S Eigen-AI Flash Endpoint
Serveert ons eigen cyc6-sft-q4 model via RunPod serverless.

Architectuur:
  - Class-based @Endpoint: model laadt 1x per worker in __init__
  - GGUF via llama-cpp-python (GPU versneld)
  - Network Volume voor model caching (geen re-download bij cold start)
  - Scale-to-zero: $0 idle, warm in ~15s

Gebruik:
  flash dev --auto-provision    # lokaal testen met hot-reload
  flash deploy                  # productie deployen

Input:  {"prompt": "Wat is Stay4S?", "max_tokens": 200}
Output: {"response": "...", "model": "cyc6-sft-q4", "tokens_generated": 42}
"""
from runpod_flash import Endpoint, GpuGroup, DataCenter, NetworkVolume

# Network volume met GGUF model cache
# Vul vol-id in na aanmaken: runpodctl network-volume create --name stay4s-models --size 30 --data-center-id EU-RO-1
vol = NetworkVolume(id="<VUL-VOL-ID-IN>", datacenter=DataCenter.EU_RO_1)

@Endpoint(
    name="stay4s-eigen-ai",
    gpu=GpuGroup.AMPERE_16,          # RTX A4000, 16GB VRAM, ~$0.16/u
    workers=(0, 3),                  # scale-to-zero, max 3 parallel
    idle_timeout=300,                # 5 min warm blijven na laatste request
    datacenter=DataCenter.EU_RO_1,   # Europa (zelfde DC als volume)
    volume=vol,
    dependencies=[
        "llama-cpp-python",
        "huggingface-hub",
    ],
    env={
        "HF_HUB_CACHE": "/runpod-volume/hf-cache",
    },
    flashboot=True,                  # snelle cold starts via snapshot
)
class EigenAI:
    def __init__(self):
        """Laad model 1x per worker. Warm workers hergebruiken dit."""
        from llama_cpp import Llama
        import os
        
        model_path = "/runpod-volume/models/cyc6-sft-q4.gguf"
        
        # Fallback: download van HuggingFace als niet op volume
        if not os.path.exists(model_path):
            from huggingface_hub import hf_hub_download
            model_path = hf_hub_download(
                repo_id="stay4s/cyc6-sft-q4",
                filename="cyc6-sft-q4.gguf",
            )
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_gpu_layers=-1,          # alle layers op GPU
            verbose=False,
            n_threads=4,
        )
        self.model_name = "cyc6-sft-q4"
        print(f"=== {self.model_name} GELADEN ===")
    
    async def generate(self, prompt: str, max_tokens: int = 200) -> dict:
        """Genereer tekst met ons eigen model.
        
        Args:
            prompt: De prompt tekst
            max_tokens: Maximaal aantal tokens (default 200, max 500)
        
        Returns:
            {"response": str, "model": str, "tokens_generated": int}
        """
        try:
            output = self.llm(
                prompt=prompt,
                max_tokens=min(max_tokens, 500),
                stop=["<|eot|>", "<|user|>", "<|assistant|>"],
                temperature=0.7,
                top_p=0.9,
                echo=False,
            )
            text = output["choices"][0]["text"].strip()
            tokens = output["usage"]["completion_tokens"]
            return {
                "response": text,
                "model": self.model_name,
                "tokens_generated": tokens,
            }
        except Exception as e:
            return {
                "response": "",
                "error": str(e)[:200],
                "model": self.model_name,
            }
    
    async def health(self) -> dict:
        """Health check."""
        return {
            "status": "ok",
            "model": self.model_name,
            "loaded": True,
        }


# Alternatief: qwen3:1.7b als primary (beter kwaliteit)
# Vervang model_path met "/runpod-volume/models/qwen3-1.7b.gguf"
# en stop tokens met ["<|im_end|>"]