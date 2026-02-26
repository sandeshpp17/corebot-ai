from corebot_ai.utils.prompts import build_rag_prompt


def test_build_rag_prompt_contains_inputs() -> None:
    prompt = build_rag_prompt(
        "What is this?",
        [{"source": "README.md", "content": "Corebot docs"}],
        [{"role": "user", "content": "Hi"}],
    )
    assert "What is this?" in prompt
    assert "README.md" in prompt
    assert "Hi" in prompt
