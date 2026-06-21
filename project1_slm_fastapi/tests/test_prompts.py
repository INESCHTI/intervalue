from project1_slm_fastapi.src.slm_api.prompts import build_prompt


def test_build_prompt_contains_text() -> None:
    prompt = build_prompt("summarize", "Bonjour le monde")
    assert "Bonjour le monde" in prompt
