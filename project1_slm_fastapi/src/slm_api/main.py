from fastapi import FastAPI, HTTPException

try:
    from .ollama_client import OllamaClient
    from .prompts import build_prompt
    from .schemas import ProcessRequest, ProcessResponse
except ImportError:  # pragma: no cover - permet l'exécution directe depuis le dossier du projet
    from src.slm_api.ollama_client import OllamaClient
    from src.slm_api.prompts import build_prompt
    from src.slm_api.schemas import ProcessRequest, ProcessResponse


app = FastAPI(title="Projet 1 - SLMs locaux + FastAPI")
client = OllamaClient()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "project": "project1_slm_fastapi"}


@app.post("/nlp/process", response_model=ProcessResponse)
def process(request: ProcessRequest) -> ProcessResponse:
    prompt = build_prompt(request.task, request.text)

    try:
        output = client.generate(request.model, prompt)
        result = output["response"]
        latency_s = output["latency_s"]
        token_count = output.get("token_count")
        tokens_per_sec = output.get("tokens_per_sec")
        source = "ollama"
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ollama indisponible: {exc}")

    return ProcessResponse(
        result=result,
        model=request.model,
        task=request.task,
        source=source,
        latency_s=latency_s,
        token_count=token_count,
        tokens_per_sec=tokens_per_sec,
    )


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
