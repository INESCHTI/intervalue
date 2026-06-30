from __future__ import annotations

import time

import httpx


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", timeout_s: float = 180.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def generate(self, model: str, prompt: str) -> dict:
        started = time.perf_counter()
        payload = {"model": model, "prompt": prompt, "stream": False}

        with httpx.Client(timeout=self.timeout_s) as client:
            try:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
            except httpx.TimeoutException:
                # Premier lancement d'un modèle local peut être lent; une seconde tentative est souvent suffisante.
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()

        return {
            "response": data.get("response", ""),
            "raw": data,
            "latency_s": round(time.perf_counter() - started, 3),
            "token_count": data.get("eval_count"),
            "tokens_per_sec": self._tokens_per_second(data),
        }

    @staticmethod
    def _tokens_per_second(data: dict) -> float | None:
        token_count = data.get("eval_count")
        eval_duration_ns = data.get("eval_duration")
        if not token_count or not eval_duration_ns:
            return None
        eval_duration_s = eval_duration_ns / 1_000_000_000
        if eval_duration_s <= 0:
            return None
        return round(token_count / eval_duration_s, 3)
