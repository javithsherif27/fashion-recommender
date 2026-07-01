from __future__ import annotations

import pytest

from app import config
from app.llm import OpenAIRequiredError, get_interpreter


def test_required_openai_without_key_raises(monkeypatch) -> None:
    monkeypatch.setattr(config, "REQUIRE_OPENAI", True)
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    monkeypatch.setattr(config, "USE_LLM", "auto")

    with pytest.raises(OpenAIRequiredError, match="OPENAI_API_KEY"):
        get_interpreter()


def test_disabled_llm_still_fails_when_openai_is_required(monkeypatch) -> None:
    monkeypatch.setattr(config, "REQUIRE_OPENAI", True)
    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(config, "USE_LLM", "off")

    with pytest.raises(OpenAIRequiredError, match="USE_LLM disables"):
        get_interpreter()
