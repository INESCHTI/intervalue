from project1_slm_fastapi.src.benchmark.metrics import score_json_validity, tokens_per_second


def test_tokens_per_second():
    assert tokens_per_second(10, 2.0) == 5.0


def test_score_json_validity():
    assert score_json_validity(True) == 1
    assert score_json_validity(False) == 0
