"""
Canonical synthetic portfolio — the single source of truth for every surface
(financial agent, orchestrator REST API, web + mobile dashboards).

Headline figures are authored once; the pure metrics functions in
agentkit.finance recompute AUM / TWR / volatility / Sharpe / IRR from these
inputs so the numbers are genuinely *computed* and unit-testable.
"""

from __future__ import annotations

import math
from datetime import date
from decimal import Decimal
from typing import Any

from agentkit.finance.metrics import (
    CashflowRow,
    DealSnapshot,
    compute_portfolio_metrics,
)

# ── Canonical inputs ────────────────────────────────────────────────────────

_TARGET_AUM = Decimal("20400000")  # $20.4M assets under management
_TARGET_COST_BASIS = Decimal("12550000")  # AUM − cost = $7.85M total profit
NUM_DEALS = 48
INCEPTION = date(2011, 8, 1)  # ≈14.9y holding period → 7.14% annualized at 178.65% TWR
_RISK_FREE = 0.0  # demo measures excess return over a ~0% cash rate

# One aggregate snapshot drives AUM + profit exactly (active book = whole book).
_SEED_DEALS: list[DealSnapshot] = [
    DealSnapshot(_TARGET_AUM, _TARGET_COST_BASIS, _TARGET_AUM, "active"),
]


def _build_monthly_returns() -> list[float]:
    """
    Deterministic monthly HPR series calibrated so the metrics library yields:
      • ITD TWR            ≈ 178.65%   (cumulative product of (1+r) ≈ 2.7865)
      • annual volatility  ≈ 12.27%    (monthly std-dev ≈ 3.53%)
    """
    n = 178  # ~14.8 years of monthly observations
    amp = 0.03532  # ±3.532% monthly swing → ≈12.27% annualized volatility
    target = 2.7865  # 1 + 1.7865 (ITD TWR)
    per_pair = target ** (1.0 / (n / 2))
    drift = math.sqrt(per_pair + amp * amp) - 1.0
    series = [drift + amp if i % 2 == 0 else drift - amp for i in range(n)]
    prod = 1.0
    for r in series:
        prod *= 1.0 + r
    series[0] = (1.0 + series[0]) * (target / prod) - 1.0
    return series


_SEED_MONTHLY_RETURNS: list[float] = _build_monthly_returns()

# Capital calls + a closing NAV distribution, calibrated to IRR ≈ 8%.
_SEED_CASHFLOWS: list[CashflowRow] = [
    CashflowRow(date(2011, 8, 1), 3_300_000.0),
    CashflowRow(date(2014, 1, 1), 2_100_000.0),
    CashflowRow(date(2017, 6, 1), 1_300_000.0),
    CashflowRow(date(2020, 3, 1), 800_000.0),
    CashflowRow(date(2026, 6, 1), -20_400_000.0),
]

# Geography allocation (by NAV %) — sums to 100.
GEO: dict[str, float] = {
    "Asia": 37.0,
    "North America": 35.0,
    "Global": 16.0,
    "Europe": 8.0,
    "Middle East": 4.0,
}

# Sector allocation (by NAV %) — sums to 100.
SECTOR: dict[str, float] = {
    "Real Estate": 45.0,
    "Private Equity": 35.0,
    "Equities": 15.0,
    "Credit": 5.0,
}

# Top deals by MOIC (fictional holdings).
TOP_DEALS: list[dict[str, Any]] = [
    {"name": "Aurora Brands", "moic": 1.55, "asset_class": "PE", "status": "exited"},
    {"name": "Project Summit", "moic": 1.52, "asset_class": "PE", "status": "exited"},
    {"name": "Project Delta", "moic": 1.47, "asset_class": "PE", "status": "active"},
    {"name": "Singapore Grade-A Office", "moic": 1.42, "asset_class": "RE", "status": "active"},
    {"name": "Metro Class-A Office Tower", "moic": 1.29, "asset_class": "RE", "status": "active"},
]

# Representative holdings for the portfolio table (name, sector, geo, $M AUM, TWR%).
DEALS: list[dict[str, Any]] = [
    {
        "name": "Aurora Brands",
        "sector": "Private Equity",
        "geo": "North America",
        "status": "Exited",
        "aum": 0.78,
        "twr": 55.0,
    },
    {
        "name": "Project Summit",
        "sector": "Private Equity",
        "geo": "North America",
        "status": "Exited",
        "aum": 0.61,
        "twr": 52.0,
    },
    {
        "name": "Project Delta",
        "sector": "Private Equity",
        "geo": "Asia",
        "status": "Active",
        "aum": 0.59,
        "twr": 47.0,
    },
    {
        "name": "Singapore Grade-A Office",
        "sector": "Real Estate",
        "geo": "Asia",
        "status": "Active",
        "aum": 1.08,
        "twr": 42.0,
    },
    {
        "name": "Metro Class-A Office Tower",
        "sector": "Real Estate",
        "geo": "North America",
        "status": "Active",
        "aum": 1.10,
        "twr": 29.0,
    },
    {
        "name": "Helios Media",
        "sector": "Private Equity",
        "geo": "Asia",
        "status": "Active",
        "aum": 0.69,
        "twr": 44.0,
    },
    {
        "name": "Global Infrastructure Fund",
        "sector": "Real Estate",
        "geo": "Global",
        "status": "Active",
        "aum": 0.62,
        "twr": 31.0,
    },
    {
        "name": "Nordic Clean Tech",
        "sector": "Private Equity",
        "geo": "Europe",
        "status": "Active",
        "aum": 0.24,
        "twr": 24.0,
    },
]

# Individual holdings with per-security detail for the portfolio table.
HOLDINGS: list[dict[str, Any]] = [
    {
        "security": "Aurora Brands",
        "type": "PE",
        "quantity": 150_000,
        "purchase_price": 3.40,
        "current_price": 5.20,
        "cost_basis": 510_000,
        "market_value": 780_000,
        "weight_pct": 3.8,
        "twr_pct": 55.0,
        "status": "Exited",
    },
    {
        "security": "Project Summit",
        "type": "PE",
        "quantity": 120_000,
        "purchase_price": 3.35,
        "current_price": 5.08,
        "cost_basis": 402_000,
        "market_value": 610_000,
        "weight_pct": 3.0,
        "twr_pct": 52.0,
        "status": "Exited",
    },
    {
        "security": "Project Delta",
        "type": "PE",
        "quantity": 100_000,
        "purchase_price": 4.00,
        "current_price": 5.90,
        "cost_basis": 400_000,
        "market_value": 590_000,
        "weight_pct": 2.9,
        "twr_pct": 47.0,
        "status": "Active",
    },
    {
        "security": "Singapore Grade-A Office",
        "type": "RE",
        "quantity": 1,
        "purchase_price": 760_000,
        "current_price": 1_080_000,
        "cost_basis": 760_000,
        "market_value": 1_080_000,
        "weight_pct": 5.3,
        "twr_pct": 42.0,
        "status": "Active",
    },
    {
        "security": "Metro Class-A Office Tower",
        "type": "RE",
        "quantity": 1,
        "purchase_price": 850_000,
        "current_price": 1_100_000,
        "cost_basis": 850_000,
        "market_value": 1_100_000,
        "weight_pct": 5.4,
        "twr_pct": 29.0,
        "status": "Active",
    },
    {
        "security": "Helios Media",
        "type": "PE",
        "quantity": 200_000,
        "purchase_price": 2.40,
        "current_price": 3.45,
        "cost_basis": 480_000,
        "market_value": 690_000,
        "weight_pct": 3.4,
        "twr_pct": 44.0,
        "status": "Active",
    },
    {
        "security": "Global Infrastructure Fund",
        "type": "RE",
        "quantity": 50_000,
        "purchase_price": 9.50,
        "current_price": 12.40,
        "cost_basis": 475_000,
        "market_value": 620_000,
        "weight_pct": 3.0,
        "twr_pct": 31.0,
        "status": "Active",
    },
    {
        "security": "Nordic Clean Tech",
        "type": "PE",
        "quantity": 60_000,
        "purchase_price": 3.00,
        "current_price": 4.00,
        "cost_basis": 180_000,
        "market_value": 240_000,
        "weight_pct": 1.2,
        "twr_pct": 24.0,
        "status": "Active",
    },
    {
        "security": "Dubai Logistics Hub",
        "type": "RE",
        "quantity": 1,
        "purchase_price": 620_000,
        "current_price": 815_000,
        "cost_basis": 620_000,
        "market_value": 815_000,
        "weight_pct": 4.0,
        "twr_pct": 31.5,
        "status": "Active",
    },
    {
        "security": "Tokyo Residential REIT",
        "type": "RE",
        "quantity": 80_000,
        "purchase_price": 12.50,
        "current_price": 16.80,
        "cost_basis": 1_000_000,
        "market_value": 1_344_000,
        "weight_pct": 6.6,
        "twr_pct": 34.4,
        "status": "Active",
    },
    {
        "security": "Atlantic Credit Fund III",
        "type": "Credit",
        "quantity": 500_000,
        "purchase_price": 1.00,
        "current_price": 1.07,
        "cost_basis": 500_000,
        "market_value": 535_000,
        "weight_pct": 2.6,
        "twr_pct": 7.0,
        "status": "Active",
    },
    {
        "security": "Pacific Basin Equities",
        "type": "Equities",
        "quantity": 25_000,
        "purchase_price": 48.00,
        "current_price": 63.20,
        "cost_basis": 1_200_000,
        "market_value": 1_580_000,
        "weight_pct": 7.7,
        "twr_pct": 31.7,
        "status": "Active",
    },
    {
        "security": "Shanghai Tech Ventures",
        "type": "PE",
        "quantity": 300_000,
        "purchase_price": 5.10,
        "current_price": 7.40,
        "cost_basis": 1_530_000,
        "market_value": 2_220_000,
        "weight_pct": 10.9,
        "twr_pct": 45.1,
        "status": "Active",
    },
    {
        "security": "European Yield Bond Fund",
        "type": "Credit",
        "quantity": 400_000,
        "purchase_price": 1.00,
        "current_price": 1.12,
        "cost_basis": 400_000,
        "market_value": 448_000,
        "weight_pct": 2.2,
        "twr_pct": 12.0,
        "status": "Active",
    },
    {
        "security": "US Growth Equity Basket",
        "type": "Equities",
        "quantity": 15_000,
        "purchase_price": 72.00,
        "current_price": 98.50,
        "cost_basis": 1_080_000,
        "market_value": 1_477_500,
        "weight_pct": 7.2,
        "twr_pct": 36.8,
        "status": "Active",
    },
    {
        "security": "Mumbai Commercial Complex",
        "type": "RE",
        "quantity": 1,
        "purchase_price": 540_000,
        "current_price": 720_000,
        "cost_basis": 540_000,
        "market_value": 720_000,
        "weight_pct": 3.5,
        "twr_pct": 33.3,
        "status": "Active",
    },
    {
        "security": "London Fintech Growth",
        "type": "PE",
        "quantity": 180_000,
        "purchase_price": 4.20,
        "current_price": 5.50,
        "cost_basis": 756_000,
        "market_value": 990_000,
        "weight_pct": 4.9,
        "twr_pct": 31.0,
        "status": "Active",
    },
    {
        "security": "Riyadh Infrastructure Dev",
        "type": "RE",
        "quantity": 1,
        "purchase_price": 380_000,
        "current_price": 510_000,
        "cost_basis": 380_000,
        "market_value": 510_000,
        "weight_pct": 2.5,
        "twr_pct": 34.2,
        "status": "Active",
    },
    {
        "security": "APAC Healthcare Fund",
        "type": "PE",
        "quantity": 250_000,
        "purchase_price": 3.80,
        "current_price": 5.20,
        "cost_basis": 950_000,
        "market_value": 1_300_000,
        "weight_pct": 6.4,
        "twr_pct": 36.8,
        "status": "Active",
    },
    {
        "security": "Emerging Markets Debt",
        "type": "Credit",
        "quantity": 350_000,
        "purchase_price": 1.00,
        "current_price": 1.05,
        "cost_basis": 350_000,
        "market_value": 367_500,
        "weight_pct": 1.8,
        "twr_pct": 5.0,
        "status": "Active",
    },
]


def get_metrics() -> dict[str, Any]:
    """Compute the canonical portfolio metrics."""
    m = compute_portfolio_metrics(
        _SEED_DEALS,
        _SEED_MONTHLY_RETURNS,
        _SEED_CASHFLOWS,
        INCEPTION,
        risk_free=_RISK_FREE,
    )
    return {
        "aum": float(m.aum),
        "aum_fmt": f"${m.aum / 1_000_000:.1f}M",
        "twr_pct": m.twr_pct,
        "annualized_pct": m.annualized_pct,
        "irr_pct": m.irr_pct,
        "sharpe": m.sharpe,
        "volatility_pct": m.volatility,
        "total_profit": float(m.total_profit),
        "profit_fmt": f"${m.total_profit / 1_000_000:.2f}M",
        "years": m.years,
        "num_deals": NUM_DEALS,
        "num_active": NUM_DEALS - 6,
    }
