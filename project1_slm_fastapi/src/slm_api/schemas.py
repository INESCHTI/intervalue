from typing import Literal

from pydantic import BaseModel, Field


TaskName = Literal["summarize", "extract", "qa", "classify"]


class ProcessRequest(BaseModel):
    text: str = Field(..., min_length=1)
    model: str = "mistral:7b"
    task: TaskName = "summarize"


class ProcessResponse(BaseModel):
    result: str | dict
    model: str
    task: TaskName
    source: str
    latency_s: float | None = None
    token_count: int | None = None
    tokens_per_sec: float | None = None
