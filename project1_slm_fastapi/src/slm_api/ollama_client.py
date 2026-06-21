from __future__ import annotations

import time

import httpx


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip("/")

    def generate(self, model: str, prompt: str) -> dict:
        started = time.perf_counter()
        payload = {"model": model, "prompt": prompt, "stream": False}

        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()

        return {
            "response": data.get("response", ""),
            "raw": data,
            "latency_s": round(time.perf_counter() - started, 3),
        }
