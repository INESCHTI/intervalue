from fastapi import FastAPI, HTTPException

from .ollama_client import OllamaClient
from .prompts import build_prompt
from .schemas import ProcessRequest, ProcessResponse


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
        source = "ollama"
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ollama indisponible: {exc}")

    return ProcessResponse(
        result=result,
        model=request.model,
        task=request.task,
        source=source,
        latency_s=latency_s,
    )


def main() -> None:
    import uvicorn

    uvicorn.run("project1_slm_fastapi.src.slm_api.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
