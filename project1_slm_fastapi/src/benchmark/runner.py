from __future__ import annotations

import json
import time
from pathlib import Path
from collections.abc import Sequence

import httpx

from .report import write_markdown_report


DEFAULT_MODELS: tuple[str, ...] = ("llama3.2:3b", "mistral:7b", "qwen2.5-coder:14b")


def quality_score(result: str, expected_keywords: Sequence[str] | None = None) -> float | None:
    if not expected_keywords:
        return None
    normalized_result = result.casefold()
    matches = sum(1 for keyword in expected_keywords if keyword.casefold() in normalized_result)
    return round(matches / len(expected_keywords), 3)


def wait_for_api(health_url: str = "http://127.0.0.1:8000/health", timeout_s: int = 30) -> bool:
    deadline = time.time() + timeout_s
    with httpx.Client(timeout=5.0) as client:
        while time.time() < deadline:
            try:
                response = client.get(health_url)
                if response.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(1)
    return False


def run_benchmark(
    corpus_path: str,
    api_url: str = "http://127.0.0.1:8000/nlp/process",
    models: Sequence[str] = DEFAULT_MODELS,
) -> list[dict]:
    corpus = json.loads(Path(corpus_path).read_text(encoding="utf-8"))
    results: list[dict] = []

    with httpx.Client(timeout=httpx.Timeout(180.0, connect=10.0)) as client:
        for sample in corpus:
            for model in models:
                try:
                    response = client.post(
                        api_url,
                        json={
                            "text": sample["text"],
                            "task": sample["task"],
                            "model": model,
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                    result_text = str(payload.get("result", ""))
                    results.append(
                        {
                            "id": sample["id"],
                            "task": sample["task"],
                            "model": model,
                            "status": response.status_code,
                            "latency_s": payload.get("latency_s"),
                            "token_count": payload.get("token_count"),
                            "tokens_per_sec": payload.get("tokens_per_sec"),
                            "quality_score": quality_score(result_text, sample.get("expected_keywords")),
                            "result": result_text,
                        }
                    )
                except httpx.TimeoutException as exc:
                    results.append(
                        {
                            "id": sample["id"],
                            "task": sample.get("task"),
                            "model": model,
                            "status": "timeout",
                            "error": str(exc),
                        }
                    )
                except Exception as exc:
                    results.append(
                        {
                            "id": sample["id"],
                            "task": sample.get("task"),
                            "model": model,
                            "status": "error",
                            "error": str(exc),
                        }
                    )

    return results


def main() -> None:
    corpus = str(Path(__file__).resolve().parents[2] / "data" / "corpus" / "sample.json")
    if not wait_for_api():
        raise SystemExit("API indisponible: lance d'abord `python run_api.py` dans project1_slm_fastapi.")
    results = run_benchmark(corpus)
    report = write_markdown_report(results)
    print(f"Benchmark terminé: {report}")


if __name__ == "__main__":
    main()
