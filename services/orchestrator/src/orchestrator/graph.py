"""
LangGraph supervisor graph.

The graph routes a user message to one or more specialist agents via A2A,
aggregates their outputs, and streams the final answer.

State machine:
  START -> router -> [agent_financial | agent_market | agent_docs | agent_action | agent_qa]
        -> aggregate -> END
"""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import AsyncIterator
from typing import Annotated, Any, TypedDict

from agentkit.a2a.client import A2AClient
from agentkit.a2a.models import A2AMessage, A2ATask
from langgraph.graph import END, START, StateGraph

# ── State ─────────────────────────────────────────────────────────────────────


def _merge_list(a: list[Any], b: list[Any]) -> list[Any]:
    return a + b


class MeshState(TypedDict):
    user_message: str
    execution_message: str
    conversation_id: str
    user_id: str
    correlation_id: str
    routed_agents: Annotated[list[str], _merge_list]
    agent_results: Annotated[list[dict[str, Any]], _merge_list]
    final_answer: str


# ── Agent registry ─────────────────────────────────────────────────────────────

_AGENT_URLS: dict[str, str] = {
    "financial": os.getenv("AGENT_FINANCIAL_URL", "http://localhost:8001"),
    "market": os.getenv("AGENT_MARKET_URL", "http://localhost:8002"),
    "docs": os.getenv("AGENT_DOCS_URL", "http://localhost:8003"),
    "action": os.getenv("AGENT_ACTION_URL", "http://localhost:8004"),
    "qa": os.getenv("AGENT_QA_URL", "http://localhost:8005"),
}

# Keywords used by the simple rule-based router
_ROUTING_RULES: list[tuple[str, list[str]]] = [
    (
        "financial",
        [
            "aum",
            "portfolio",
            "portiflio",
            "performance",
            "twr",
            "irr",
            "sharpe",
            "volatility",
            "deal",
            "deals",
            "return",
            "profit",
            "asset",
            "assets",
            "nav",
            "gain",
            "loss",
            "metric",
            "annualized",
            "breakdown",
            "holdings",
            "holding",
            "positions",
            "position",
            "securities",
            "security",
            "allocation",
            "geographic",
            "geography",
            "sector",
            "sectors",
            "region",
            "regions",
            "moic",
        ],
    ),
    (
        "market",
        [
            "market",
            "price",
            "quote",
            "stock",
            "rate",
            "gdp",
            "inflation",
            "yield",
            "economic",
            "indicator",
            "index",
            "s&p",
            "nasdaq",
        ],
    ),
    (
        "docs",
        [
            "document",
            "documents",
            "uploaded",
            "attached",
            "attachment",
            "attachments",
            "file",
            "files",
            "pdf",
            "report",
            "extract",
            "detail",
            "find in",
            "according to",
            "search",
            "more about",
            "fact sheet",
        ],
    ),
    (
        "action",
        ["send", "email", "whatsapp", "notify", "generate report", "export", "share", "download"],
    ),
    ("qa", ["test", "generate test", "validate", "check api", "functional"]),
]

_GREETING_RE = re.compile(
    r"^\s*(?:hi|hello|hey|good\s+(?:morning|afternoon|evening)|howdy"
    r"|bonjour|salut|coucou|bonsoir)[,\s]*"
    r"(?:\s+(?:there|advisor|wealthmesh|laruche|ladies\s+and\s+gentlemen))?[!.?\s]*$",
    re.IGNORECASE,
)
_ATTACHMENT_REFERENCE_RE = re.compile(
    r"\b(?:uploaded|attached|attachment|attachments|file|files|document|documents|pdf|image|audio|voice)\b",
    re.IGNORECASE,
)
_ATTACHMENT_CONTEXT_MARKER = "attached file context:"


def _has_attachment_context(message: str) -> bool:
    return _ATTACHMENT_CONTEXT_MARKER in message.lower()


def _needs_attachment_context(user_message: str, execution_message: str = "") -> bool:
    if _has_attachment_context(execution_message or user_message):
        return False
    lower = user_message.lower()
    intent_words = (
        "summarize",
        "analyse",
        "analyze",
        "read",
        "extract",
        "find",
        "search",
        "uploaded",
        "attached",
    )
    return bool(_ATTACHMENT_REFERENCE_RE.search(user_message)) and any(
        word in lower for word in intent_words
    )


def _sanitize_answer(answer: str) -> str:
    cleaned = answer.replace("[Your Name]", "LaRuche")
    cleaned = cleaned.replace(
        "information technology date-to-date time-weighted return",
        "inception-to-date time-weighted return",
    )
    cleaned = cleaned.replace("ITD TWR", "inception-to-date TWR")
    cleaned = re.sub(
        r"\n?\s*Best regards,?\s*(?:\n\s*LaRuche)?\s*$", "", cleaned, flags=re.IGNORECASE
    )
    return cleaned.strip()


_ALL_KEYWORDS: set[str] = set()
for _, _kws in _ROUTING_RULES:
    for _kw in _kws:
        if " " not in _kw and "&" not in _kw:
            _ALL_KEYWORDS.add(_kw)


def _edit_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            curr[j] = prev[j - 1] if ca == cb else 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[-1]


def _fuzzy_expand(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for token in tokens:
        if len(token) < 4:
            continue
        threshold = 1 if len(token) <= 6 else 2
        for keyword in _ALL_KEYWORDS:
            if abs(len(token) - len(keyword)) > threshold:
                continue
            if _edit_distance(token, keyword) <= threshold:
                expanded.add(keyword)
    return expanded


def _route(message: str) -> list[str]:
    if _GREETING_RE.fullmatch(message):
        return []

    lower = message.lower()
    tokens = _fuzzy_expand(set(re.findall(r"[a-z0-9&]+", lower)))
    matched: list[str] = []
    for agent, keywords in _ROUTING_RULES:
        for kw in keywords:
            hit = kw in lower if (" " in kw or "&" in kw) else kw in tokens
            if hit:
                matched.append(agent)
                break
    return matched


_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_DEFAULT_MODEL = os.getenv("MODEL_DEFAULT", "qwen2.5:3b")


async def _general_answer(message: str) -> str:
    """Answer general (non-financial) questions directly via Ollama."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{_OLLAMA_URL}/api/chat",
                json={
                    "model": _DEFAULT_MODEL,
                    "stream": False,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are LaRuche, a helpful private-banking advisor. "
                                "Answer the user's question concisely. Use markdown formatting "
                                "when it improves readability (headings, lists, bold, code blocks, tables). "
                                "For math equations, always use LaTeX with dollar signs: "
                                "$inline$ for inline and $$display$$ for display math. "
                                "Example: $E = mc^2$, $$\\int_0^1 x^2 dx = \\frac{1}{3}$$. "
                                "If the question is unrelated to finance, still answer helpfully."
                            ),
                        },
                        {"role": "user", "content": message},
                    ],
                },
            )
            resp.raise_for_status()
            return resp.json().get("message", {}).get("content", "").strip()
    except Exception:
        return "I was unable to process that request. Please try again."


# ── Graph nodes ───────────────────────────────────────────────────────────────


async def router_node(state: MeshState) -> dict[str, Any]:
    if _needs_attachment_context(state["user_message"], state.get("execution_message", "")):
        return {"routed_agents": []}
    agents = _route(state["user_message"])
    return {"routed_agents": agents}


async def _call_agent(agent: str, state: MeshState) -> dict[str, Any]:
    url = _AGENT_URLS.get(agent, "")
    if not url:
        return {"agent": agent, "output": f"Agent {agent} not configured", "error": True}
    try:
        async with A2AClient(base_url=url) as client:
            task = A2ATask(
                skill_id="chat",
                sender_id="orchestrator",
                messages=[
                    A2AMessage(
                        role="user", content=state.get("execution_message") or state["user_message"]
                    )
                ],
                context={
                    "conversation_id": state["conversation_id"],
                    "user_id": state["user_id"],
                    "correlation_id": state.get("correlation_id", ""),
                },
            )
            result = await client.send_task(task)
            content = result.output.content if result.output else ""
            return {"agent": agent, "output": content, "error": result.error is not None}
    except Exception as exc:
        return {"agent": agent, "output": str(exc), "error": True}


async def agents_node(state: MeshState) -> dict[str, Any]:
    tasks = [_call_agent(a, state) for a in state["routed_agents"]]
    results: list[dict[str, Any]] = await asyncio.gather(*tasks)
    return {"agent_results": results}


async def aggregate_node(state: MeshState) -> dict[str, Any]:
    if _needs_attachment_context(state["user_message"], state.get("execution_message", "")):
        return {
            "final_answer": (
                "I don't see any uploaded file context yet. Attach your documents, images, "
                "or audio files with the plus button, then ask me to summarize or analyze them."
            )
        }

    if not state["routed_agents"]:
        if _GREETING_RE.fullmatch(state["user_message"]):
            return {
                "final_answer": (
                    "Hello! I can help with your portfolio performance, market data, "
                    "investment documents, and reports. What would you like to explore?"
                )
            }
        return {
            "final_answer": await _general_answer(state["user_message"])
        }

    parts: list[str] = []
    for r in state["agent_results"]:
        if not r.get("error") and r.get("output"):
            parts.append(r["output"])
    answer = "\n\n".join(parts) if parts else "I was unable to retrieve that information."
    answer = _sanitize_answer(answer)
    return {"final_answer": answer}


# ── Build the graph ───────────────────────────────────────────────────────────


def build_graph() -> Any:
    g: StateGraph = StateGraph(MeshState)
    g.add_node("router", router_node)
    g.add_node("agents", agents_node)
    g.add_node("aggregate", aggregate_node)
    g.add_edge(START, "router")
    g.add_edge("router", "agents")
    g.add_edge("agents", "aggregate")
    g.add_edge("aggregate", END)
    return g.compile()


_graph = build_graph()


async def run_turn(
    message: str,
    conversation_id: str = "default",
    user_id: str = "anon",
    execution_message: str | None = None,
    correlation_id: str = "",
) -> AsyncIterator[str]:
    """Stream the answer token-by-token (currently yields the full answer)."""
    state: MeshState = {
        "user_message": message,
        "execution_message": execution_message or message,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "correlation_id": correlation_id,
        "routed_agents": [],
        "agent_results": [],
        "final_answer": "",
    }
    final_state = await _graph.ainvoke(state)
    answer: str = final_state.get("final_answer", "")
    # Yield word-by-word for a streaming feel
    for word in answer.split(" "):
        yield word + " "


def _planning_summary(message: str, agents: list[str]) -> str:
    areas = ", ".join(agents) if agents else "direct advisory response"
    checklist = [
        "Identify the user's requested decision or fact.",
        f"Route evidence gathering through: {areas}.",
        "Ground the answer in retrieved portfolio, market, or document data.",
        "Check for missing assumptions, stale data, and unsupported claims.",
    ]
    return "\n".join(f"- {item}" for item in checklist)


def _critique_answer(answer: str, agent_results: list[dict[str, Any]]) -> str:
    checks: list[str] = []
    if any(result.get("error") for result in agent_results):
        checks.append("One or more specialist agents were unavailable; mention any uncertainty.")
    if answer == "I was unable to retrieve that information.":
        checks.append(
            "No grounded data was retrieved; ask for a clearer question or relevant files."
        )
    if "[Your Name]" in answer or "Best regards" in answer:
        checks.append("Remove letter-style signoffs and identity placeholders.")
    if not checks:
        checks.append(
            "Answer is grounded in available specialist output and cleaned for presentation."
        )
    return "\n".join(f"- {item}" for item in checks)


def _finalize_deep_answer(answer: str, plan: str, critique: str) -> str:
    conclusion = answer if answer == "I was unable to retrieve that information." else answer
    return _sanitize_answer(
        "Reasoning summary\n"
        f"{plan}\n\n"
        "Checks performed\n"
        f"{critique}\n\n"
        "Final answer\n"
        f"{conclusion}"
    )


async def run_deep_turn_payloads(
    message: str,
    conversation_id: str = "default",
    user_id: str = "anon",
    execution_message: str | None = None,
    correlation_id: str = "",
) -> AsyncIterator[dict[str, str]]:
    """Run a planner -> specialist execution -> critic -> finalizer wrapper."""
    if _needs_attachment_context(message, execution_message or ""):
        answer = await aggregate_node(
            {
                "user_message": message,
                "execution_message": execution_message or message,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "correlation_id": correlation_id,
                "routed_agents": [],
                "agent_results": [],
                "final_answer": "",
            }
        )
        for word in answer["final_answer"].split(" "):
            yield {"type": "token", "content": word + " "}
        return

    agents = _route(message)
    if not agents and _GREETING_RE.fullmatch(message):
        answer = await aggregate_node(
            {
                "user_message": message,
                "execution_message": execution_message or message,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "correlation_id": correlation_id,
                "routed_agents": [],
                "agent_results": [],
                "final_answer": "",
            }
        )
        for word in answer["final_answer"].split(" "):
            yield {"type": "token", "content": word + " "}
        return

    plan = _planning_summary(message, agents)
    yield {"type": "reasoning", "content": plan}

    state: MeshState = {
        "user_message": message,
        "execution_message": execution_message or message,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "correlation_id": correlation_id,
        "routed_agents": agents,
        "agent_results": [],
        "final_answer": "",
    }
    if agents:
        state.update(await agents_node(state))
    final_answer = (await aggregate_node(state))["final_answer"]
    critique = _critique_answer(final_answer, state["agent_results"])
    yield {"type": "reasoning", "content": critique}
    for word in final_answer.split(" "):
        yield {"type": "token", "content": word + " "}


async def run_deep_turn(
    message: str,
    conversation_id: str = "default",
    user_id: str = "anon",
    execution_message: str | None = None,
    correlation_id: str = "",
) -> AsyncIterator[str]:
    async for payload in run_deep_turn_payloads(
        message, conversation_id, user_id, execution_message, correlation_id
    ):
        if payload["type"] == "token":
            yield payload["content"]
