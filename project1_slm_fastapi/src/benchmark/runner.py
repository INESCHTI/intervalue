from __future__ import annotations

import json
from pathlib import Path

import httpx

from .report import write_markdown_report


def run_benchmark(corpus_path: str, api_url: str = "http://127.0.0.1:8000/nlp/process") -> list[dict]:
    corpus = json.loads(Path(corpus_path).read_text(encoding="utf-8"))
    results: list[dict] = []

    with httpx.Client(timeout=60.0) as client:
        for sample in corpus:
            try:
                response = client.post(
                    api_url,
                    json={
                        "text": sample["text"],
                        "task": sample["task"],
                        "model": sample.get("model", "mistral"),
                    },
                )
                response.raise_for_status()
                results.append({"id": sample["id"], "status": response.status_code, "response": response.text})
            except Exception as exc:
                results.append({"id": sample["id"], "status": "offline", "error": str(exc)})

    return results


def main() -> None:
    corpus = str(Path(__file__).resolve().parents[2] / "data" / "corpus" / "sample.json")
    results = run_benchmark(corpus)
    report = write_markdown_report(results)
    print(f"Benchmark terminé: {report}")


if __name__ == "__main__":
    main()
