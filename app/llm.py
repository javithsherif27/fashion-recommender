from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app import config
from app.text_utils import expand_query_text, infer_avoid_terms


@dataclass(slots=True)
class QueryIntent:
    original_query: str
    search_query: str
    must_have: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    llm_used: bool = False
    provider: str = "local"
    notes: str | None = None


class LocalQueryInterpreter:
    provider = "local"

    def interpret(self, query: str) -> QueryIntent:
        return QueryIntent(
            original_query=query,
            search_query=expand_query_text(query),
            avoid=infer_avoid_terms(query),
            llm_used=False,
            provider=self.provider,
            notes="Local deterministic query expansion was used.",
        )

    def explain_results(self, query: str, items: list[dict[str, Any]]) -> list[str]:
        return [item.get("why") or "Recommended based on semantic similarity." for item in items]


class OpenAIQueryInterpreter(LocalQueryInterpreter):
    provider = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self._fallback = LocalQueryInterpreter()

    def interpret(self, query: str) -> QueryIntent:
        prompt = (
            "You transform fashion shopping requests into compact search intent. "
            "Return JSON only with keys: search_query, must_have, avoid. "
            "Keep search_query under 35 words and include concrete fashion terms."
        )
        try:
            content = self._chat_json(
                [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query},
                ]
            )
            parsed = _parse_json_object(content)
            search_query = str(parsed.get("search_query") or "").strip()
            if not search_query:
                raise ValueError("OpenAI response did not include search_query")
            return QueryIntent(
                original_query=query,
                search_query=expand_query_text(search_query),
                must_have=_string_list(parsed.get("must_have")),
                avoid=list(
                    dict.fromkeys(_string_list(parsed.get("avoid")) + infer_avoid_terms(query))
                ),
                llm_used=True,
                provider=self.provider,
                notes="OpenAI query interpretation was used.",
            )
        except Exception as exc:
            fallback = self._fallback.interpret(query)
            fallback.notes = f"OpenAI interpretation failed; used local fallback: {exc}"
            return fallback

    def explain_results(self, query: str, items: list[dict[str, Any]]) -> list[str]:
        if not items:
            return []
        brief_items = [
            {
                "title": item.get("title"),
                "store": item.get("store"),
                "rating": item.get("average_rating"),
                "price": item.get("price"),
                "matched_terms": item.get("matched_terms", []),
            }
            for item in items[:5]
        ]
        prompt = (
            "Write one concise, human shopping explanation for each product. "
            "Return JSON only as {\"reasons\": [\"...\"]}. Do not invent product facts."
        )
        try:
            content = self._chat_json(
                [
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {"query": query, "products": brief_items},
                            ensure_ascii=False,
                        ),
                    },
                ]
            )
            parsed = _parse_json_object(content)
            reasons = _string_list(parsed.get("reasons"))
            if len(reasons) >= len(items[:5]):
                return reasons[: len(items[:5])]
        except Exception:
            pass
        return super().explain_results(query, items)

    def _chat_json(self, messages: list[dict[str, str]]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
        except Exception:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
            )
        return response.choices[0].message.content or "{}"


def get_interpreter() -> LocalQueryInterpreter:
    if config.USE_LLM in {"0", "false", "no", "off"}:
        return LocalQueryInterpreter()
    if not config.OPENAI_API_KEY:
        return LocalQueryInterpreter()
    try:
        return OpenAIQueryInterpreter(config.OPENAI_API_KEY, config.OPENAI_MODEL)
    except Exception:
        return LocalQueryInterpreter()


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _parse_json_object(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value
