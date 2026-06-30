# Test Report — `run_20260618_155111_cbb3ad`

- **SUT version:** `baseline-web`
- **Channels:** web
- **Generated:** 2026-06-18T15:51:11.747675+00:00
- **Global pass rate:** **0.0%** (0/2)

| Scenario | Channel | Latency | Score | Halluc. | Verdict |
|---|---|--:|--:|:--:|:--:|
| portfolio_aum (nominal) | web | 49.9s | 0.0 | No | ❌ FAIL |
| performance_twr (nominal) | web | 17.2s | 0.0 | No | ❌ FAIL |

## Critical failures

- **portfolio_aum** [web] — crash/5xx (status 200)
- **performance_twr** [web] — crash/5xx (status 200)
