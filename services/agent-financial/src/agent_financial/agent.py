"""
Financial Assistant — A2A task handler.

Receives a user message, selects the right MCP tool(s), calls them,
then uses the LLM to compose a grounded answer.
"""

from __future__ import annotations

from typing import Any

from agentkit.a2a.models import A2ATask
from agentkit.llm.client import LLMClient, ModelRole
from agentkit.mcp.registry import MCPRegistry
from agentkit.tracing import trace_span

from agent_financial.tools import (
    GeographyBreakdownTool,
    MetricsComputeTool,
    PortfolioHoldingsTool,
    PortfolioSummaryTool,
    SectorBreakdownTool,
    TopDealsTool,
)

# ── Registry ──────────────────────────────────────────────────────────────────

registry = MCPRegistry()
registry.register(PortfolioSummaryTool())
registry.register(PortfolioHoldingsTool())
registry.register(MetricsComputeTool())
registry.register(GeographyBreakdownTool())
registry.register(SectorBreakdownTool())
registry.register(TopDealsTool())

# ── Keyword → tool mapping ────────────────────────────────────────────────────

_TOOL_MAP: list[tuple[list[str], str, dict[str, Any]]] = [
    (
        [
            "table",
            "holdings",
            "positions",
            "securities",
            "list all",
            "show all",
            "all deals",
            "each security",
            "each deal",
            "breakdown by security",
            "individual",
        ],
        "portfolio.holdings",
        {},
    ),
    (
        [
            "geography",
            "geographic",
            "geographical",
            "region",
            "regions",
            "allocation",
            "asia",
            "europe",
            "america",
            "middle east",
            "global",
            "country",
            "countries",
        ],
        "portfolio.geo_breakdown",
        {},
    ),
    (
        [
            "sector",
            "sectors",
            "asset class",
            "asset classes",
            "allocation",
            "real estate",
            "private equity",
            "equities",
            "credit",
        ],
        "portfolio.sector_breakdown",
        {},
    ),
    (
        ["top deal", "best deal", "top deals", "best performing", "best performers", "mover", "moic"],
        "portfolio.top_deals",
        {"limit": 5},
    ),
    (["aum", "assets under management", "total assets"], "metrics.compute", {"metric": "aum"}),
    (
        ["twr", "time-weighted", "itd return", "since inception"],
        "metrics.compute",
        {"metric": "twr"},
    ),
    (["irr", "internal rate", "internal return"], "metrics.compute", {"metric": "irr"}),
    (["sharpe", "risk-adjusted"], "metrics.compute", {"metric": "sharpe"}),
    (["volatility", "standard deviation", "risk"], "metrics.compute", {"metric": "volatility"}),
    (["annualized", "per year", "yearly return"], "metrics.compute", {"metric": "annualized"}),
    (["summary", "overview", "how is", "performance", "portfolio"], "portfolio.summary", {}),
]


_SINGLE_KEYWORDS: set[str] = set()
for _kws, _, _ in _TOOL_MAP:
    for _kw in _kws:
        if " " not in _kw:
            _SINGLE_KEYWORDS.add(_kw)


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


def _fuzzy_replace(text: str) -> str:
    import re as _re
    tokens = _re.findall(r"[a-z0-9]+", text)
    for token in tokens:
        if len(token) < 4 or token in _SINGLE_KEYWORDS:
            continue
        threshold = 1 if len(token) <= 6 else 2
        for keyword in _SINGLE_KEYWORDS:
            if abs(len(token) - len(keyword)) > threshold:
                continue
            if _edit_distance(token, keyword) <= threshold:
                text = text.replace(token, keyword)
                break
    return text


def _pick_tools(message: str) -> list[tuple[str, dict[str, Any]]]:
    lower = message.lower()
    intent_text = lower.split("attached file context:", 1)[0]
    intent_text = intent_text.split("response format:", 1)[0]
    intent_text = _fuzzy_replace(intent_text)

    if "portfolio" in intent_text and not any(
        keyword in intent_text
        for keyword in (
            "volatility",
            "risk",
            "sharpe",
            "irr",
            "twr",
            "annualized",
            "aum",
            "allocation",
            "sector",
            "geography",
            "region",
            "deal",
            "table",
            "holdings",
            "positions",
            "securities",
            "list all",
            "show all",
            "individual",
            "top",
            "best",
        )
    ):
        return [("portfolio.summary", {})]

    picked: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for keywords, tool_name, kwargs in _TOOL_MAP:
        # Dedup by tool *and* args so multiple metrics.compute calls (aum, twr,
        # irr, …) are all kept for a multi-metric question.
        sig = f"{tool_name}:{sorted(kwargs.items())}"
        if any(kw in intent_text for kw in keywords) and sig not in seen:
            picked.append((tool_name, kwargs))
            seen.add(sig)
    return picked or [("portfolio.summary", {})]


# ── Main handler ──────────────────────────────────────────────────────────────

_llm = LLMClient(role=ModelRole.CONVERSATIONAL)

_SYSTEM_PROMPT = """You are a wealth-management financial assistant.
You have access to real portfolio data from the tools below.
Answer the client's question using ONLY the data provided by the tools.
Be precise with numbers. Do not hallucinate figures.
Format monetary values with $ and M/K suffixes where appropriate.
When the tool data contains a markdown table, include it in your answer exactly as provided.
Use markdown formatting: tables, bold for key figures, headings where useful.
Never sign the answer, never include "Best regards", and never use placeholders such as [Your Name].
Use "inception-to-date TWR" when explaining ITD TWR."""


_DIRECT_PASSTHROUGH_TOOLS = {
    "portfolio.holdings",
    "portfolio.geo_breakdown",
    "portfolio.sector_breakdown",
    "portfolio.top_deals",
}


async def handle_task(task: A2ATask) -> A2ATask:
    user_msg = task.messages[-1].content if task.messages else ""

    with trace_span("financial_agent", task_id=task.task_id):
        # 1. Select and call tools
        tool_calls = _pick_tools(user_msg)
        tool_outputs: list[str] = []
        for tool_name, kwargs in tool_calls:
            result = await registry.call(tool_name, **kwargs)
            if result.ok:
                tool_outputs.append(f"[{tool_name}]\n{result.content}")

        tool_context = "\n\n".join(tool_outputs)

        called_tools = {t for t, _ in tool_calls}
        if called_tools & _DIRECT_PASSTHROUGH_TOOLS and tool_context:
            answer = tool_context
            for tag in called_tools:
                answer = answer.replace(f"[{tag}]\n", "")
            answer = answer.strip()
        else:
            # 3. Compose grounded answer with LLM
            messages = [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Client question: {user_msg}\n\n"
                        f"Tool data:\n{tool_context}\n\n"
                        "Answer the client question using only the tool data above."
                    ),
                },
            ]
            try:
                answer = await _llm.chat(messages)
            except Exception:
                answer = tool_context or "Unable to retrieve portfolio data."
        if tool_calls and "Sources:" not in answer:
            sources = ", ".join(f"`{tool_name}`" for tool_name, _ in tool_calls)
            answer = f"{answer.rstrip()}\n\nSources: {sources}."

    return task.succeed(answer, {"tools_called": [t for t, _ in tool_calls]})
