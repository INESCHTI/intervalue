from __future__ import annotations


def tokens_per_second(token_count: int, latency_s: float) -> float:
    if latency_s <= 0:
        return 0.0
    return round(token_count / latency_s, 3)


def score_json_validity(is_valid: bool) -> int:
    return 1 if is_valid else 0
