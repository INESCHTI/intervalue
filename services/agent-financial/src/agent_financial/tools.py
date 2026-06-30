"""
MCP tools for the Financial Assistant agent.

All numbers come from the single canonical portfolio in agentkit.portfolio,
which the metrics library computes from calibrated inputs — so the figures the
agent reports match the orchestrator API, the dashboards, and the demo exactly.
"""

from __future__ import annotations

from typing import Any

from agentkit.mcp.tool import MCPTool, ToolResult
from agentkit.portfolio import GEO as _GEO
from agentkit.portfolio import HOLDINGS as _HOLDINGS
from agentkit.portfolio import SECTOR as _SECTOR
from agentkit.portfolio import TOP_DEALS as _TOP_DEALS
from agentkit.portfolio import get_metrics as _get_metrics

# ── MCP Tools ─────────────────────────────────────────────────────────────────


class PortfolioSummaryTool(MCPTool):
    @property
    def name(self) -> str:
        return "portfolio.summary"

    @property
    def description(self) -> str:
        return "Return high-level portfolio summary: AUM, TWR, profit, number of deals."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **_kwargs: Any) -> ToolResult:
        m = _get_metrics()
        content = (
            f"Portfolio Summary:\n"
            f"  AUM: {m['aum_fmt']} ({m['num_deals']} deals, {m['num_active']} active)\n"
            f"  Total Profit: {m['profit_fmt']}\n"
            f"  ITD TWR: {m['twr_pct']:.2f}%\n"
            f"  Annualized Return: {m['annualized_pct']:.2f}%\n"
            f"  IRR: {m['irr_pct']:.2f}%\n"
            f"  Sharpe Ratio: {m['sharpe']:.2f}\n"
            f"  Volatility: {m['volatility_pct']:.2f}%\n"
            f"  Inception: {m['years']:.1f} years"
        )
        return ToolResult(content=content)


class MetricsComputeTool(MCPTool):
    @property
    def name(self) -> str:
        return "metrics.compute"

    @property
    def description(self) -> str:
        return "Compute specific portfolio metrics: aum, twr, irr, sharpe, volatility, annualized."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": ["aum", "twr", "irr", "sharpe", "volatility", "annualized", "all"],
                }
            },
            "required": ["metric"],
        }

    async def execute(self, metric: str = "all", **_kwargs: Any) -> ToolResult:
        m = _get_metrics()
        if metric == "aum":
            return ToolResult(content=f"AUM: {m['aum_fmt']}")
        if metric == "twr":
            return ToolResult(content=f"ITD TWR: {m['twr_pct']:.2f}%")
        if metric == "irr":
            return ToolResult(content=f"IRR: {m['irr_pct']:.2f}%" if m["irr_pct"] else "IRR: N/A")
        if metric == "sharpe":
            return ToolResult(content=f"Sharpe Ratio: {m['sharpe']:.2f}")
        if metric == "volatility":
            return ToolResult(content=f"Volatility: {m['volatility_pct']:.2f}%")
        if metric == "annualized":
            return ToolResult(content=f"Annualized Return: {m['annualized_pct']:.2f}%")
        # all
        return ToolResult(
            content=(
                f"AUM: {m['aum_fmt']} | TWR: {m['twr_pct']:.2f}% | "
                f"Annualized: {m['annualized_pct']:.2f}% | IRR: {m['irr_pct']:.2f}% | "
                f"Sharpe: {m['sharpe']:.2f} | Volatility: {m['volatility_pct']:.2f}%"
            )
        )


class GeographyBreakdownTool(MCPTool):
    @property
    def name(self) -> str:
        return "portfolio.geo_breakdown"

    @property
    def description(self) -> str:
        return "Return portfolio allocation by geography."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **_kwargs: Any) -> ToolResult:
        header = "| Region | Allocation |"
        sep = "|---|---|"
        rows = [f"| {k} | **{v:.0f}%** |" for k, v in _GEO.items()]
        content = f"## Geographic Allocation\n\n{header}\n{sep}\n" + "\n".join(rows)
        return ToolResult(content=content)


class SectorBreakdownTool(MCPTool):
    @property
    def name(self) -> str:
        return "portfolio.sector_breakdown"

    @property
    def description(self) -> str:
        return "Return portfolio allocation by asset class / sector."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **_kwargs: Any) -> ToolResult:
        header = "| Asset Class | Allocation |"
        sep = "|---|---|"
        rows = [f"| {k} | **{v:.0f}%** |" for k, v in _SECTOR.items()]
        content = f"## Sector / Asset-Class Breakdown\n\n{header}\n{sep}\n" + "\n".join(rows)
        return ToolResult(content=content)


class TopDealsTool(MCPTool):
    @property
    def name(self) -> str:
        return "portfolio.top_deals"

    @property
    def description(self) -> str:
        return "Return the top deals ranked by MOIC."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 5}},
            "required": [],
        }

    async def execute(self, limit: int = 5, **_kwargs: Any) -> ToolResult:
        top = _TOP_DEALS[:limit]
        header = "| # | Deal | MOIC | Asset Class | Status |"
        sep = "|---|---|---|---|---|"
        rows = [
            f"| {i + 1} | {d['name']} | **{d['moic']}x** | {d['asset_class']} | {d['status']} |"
            for i, d in enumerate(top)
        ]
        content = f"## Top Deals by MOIC\n\n{header}\n{sep}\n" + "\n".join(rows)
        return ToolResult(content=content)


class PortfolioHoldingsTool(MCPTool):
    @property
    def name(self) -> str:
        return "portfolio.holdings"

    @property
    def description(self) -> str:
        return "Return full portfolio holdings table with per-security details."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **_kwargs: Any) -> ToolResult:
        def _fmt(v: float) -> str:
            if v >= 1_000_000:
                return f"${v / 1_000_000:.2f}M"
            if v >= 1_000:
                return f"${v / 1_000:.1f}K"
            return f"${v:,.2f}"

        header = "| Security | Type | Qty | Purchase Price | Current Price | Cost Basis | Market Value | Gain/Loss | TWR% | Status |"
        sep = "|---|---|---|---|---|---|---|---|---|---|"
        rows: list[str] = []
        total_cost = 0.0
        total_mv = 0.0
        for h in _HOLDINGS:
            gain = h["market_value"] - h["cost_basis"]
            gain_pct = (gain / h["cost_basis"] * 100) if h["cost_basis"] else 0
            sign = "+" if gain >= 0 else ""
            qty = f"{h['quantity']:,}" if h["quantity"] > 1 else "1 unit"
            pp = _fmt(h["purchase_price"]) if h["quantity"] > 1 else _fmt(h["purchase_price"])
            cp = _fmt(h["current_price"]) if h["quantity"] > 1 else _fmt(h["current_price"])
            rows.append(
                f"| {h['security']} | {h['type']} | {qty} | {pp} | {cp} "
                f"| {_fmt(h['cost_basis'])} | {_fmt(h['market_value'])} "
                f"| {sign}{_fmt(abs(gain))} ({sign}{gain_pct:.1f}%) | {h['twr_pct']:.1f}% | {h['status']} |"
            )
            total_cost += h["cost_basis"]
            total_mv += h["market_value"]

        total_gain = total_mv - total_cost
        total_gain_pct = (total_gain / total_cost * 100) if total_cost else 0
        sign = "+" if total_gain >= 0 else ""
        totals = (
            f"| **TOTAL** | | | | | **{_fmt(total_cost)}** | **{_fmt(total_mv)}** "
            f"| **{sign}{_fmt(abs(total_gain))} ({sign}{total_gain_pct:.1f}%)** | | |"
        )
        content = "\n".join([header, sep, *rows, totals])
        return ToolResult(content=content)
