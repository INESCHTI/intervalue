# Aurevia Agentic Testing Report

## Summary

- Success rate: 50.0% (1/2)
- PASS: 1
- WARN: 1
- FAIL: 0

## Results

| ID | Channel | Intent | Latency | Score | Hallucination | Verdict |
|---|---|---|---:|---:|---|---|
| web-chat-aum | web | web_chat_financial_aum | 37.282s | 0.667 | False | WARN |
| web-dashboard-dom | web | web_dashboard_dom | 6.487s | 1.0 | False | PASS |

## Top Critical Failures

- None.

## Evidence

### web-chat-aum (web)

- Verdict: WARN
- Reason: Partial match: ['AUM', 'portfolio'].
- Expected keywords: 20.4, AUM, portfolio
- Screenshot: `reports\qa-swarm\screenshots\web-chat-aum.png`
- OCR text: [OCR unavailable: tesseract is not installed or it's not in your PATH. See README file for more information.]

```text
Aurevia

Private Wealth Intelligence

WORKSPACE

Overview
Portfolio
Markets
AI Assistant
Voice Studio
Secure advisory session
A

advisor@aurevia.local

Advisor access

Sign out
AI Assistant

Type, dictate, or start a natural voice conversation.

Advisory mesh online
Hello! I'm your Aurevia advisor. How can I help you today?
What is my portfolio AUM?
I was unable to retrieve that information. 
Instant
Deep

Aurevia can make mistakes. Verify important financial information.
```

### web-dashboard-dom (web)

- Verdict: PASS
- Reason: Matched 3/3 expected keywords.
- Expected keywords: Portfolio Overview, $20.4M, Geographic Allocation
- Screenshot: `reports\qa-swarm\screenshots\web-dashboard-dom.png`
- OCR text: [OCR unavailable: tesseract is not installed or it's not in your PATH. See README file for more information.]

```text
Aurevia

Private Wealth Intelligence

WORKSPACE

Overview
Portfolio
Markets
AI Assistant
Voice Studio
Secure advisory session
A

advisor@aurevia.local

Advisor access

Sign out

LIVE PORTFOLIO

Portfolio Overview

As of June 14, 2026 Â· Reported in USD

1M
3M
YTD
1Y
ALL
Ask Aurevia
TOTAL ASSETS UNDER MANAGEMENT
$20.4M
+3.70%
Year to date
TWR Â· YTD
19.65%
Time-weighted
ANNUALIZED Â· YTD
3.70%
IRR 8.30%
NET PROFIT
$7.85M
42 of 48 deals active
Portfolio Performance
Portfolio
Benchmark
Jan
Feb
Mar
Apr
May
Jun
Sharpe
0.58
Volatility
9.57%
Annualized
3.70%
IRR
8.30%
Geographic Allocation
Exposure by region
Asia
37%
North America
35%
Global
16%
Europe
8%
Middle East
4%
Sector Mix
Capital by strategy
Real Estate
45%
Private Equity
35%
Equities
15%
Credit
5%
```

## Recommendations

- Treat every FAIL as a regression candidate.
- Run API cases before merge; run Playwright DOM/OCR cases nightly or before demos.
- Use `AUREVIA_TARGET=minikube` to validate the Kubernetes deployment path.

