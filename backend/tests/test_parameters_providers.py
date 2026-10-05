from __future__ import annotations

import asyncio
from types import SimpleNamespace

import httpx
import pytest
from pytest import MonkeyPatch

from app.modules.parameters import providers


class FakeResponse:
    def __init__(
        self,
        payload: dict[str, object],
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.payload = payload
        self.status_code = status_code
        self.headers = headers or {}

    def json(self) -> dict[str, object]:
        return self.payload


class FakeAsyncClient:
    def __init__(self, payload: dict[str, object], status_code: int = 200, **_: object) -> None:
        self.payload = payload
        self.status_code = status_code

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def get(self, _: str, **__: object) -> FakeResponse:
        return FakeResponse(self.payload, self.status_code)

    async def post(self, _: str, **__: object) -> FakeResponse:
        return FakeResponse(self.payload, self.status_code)


def ollama_configuration(model_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        provider_kind="ollama-local",
        base_url="http://ollama:11434",
        model_id=model_id,
        reasoning_level="minimal",
    )


def cloud_configuration() -> SimpleNamespace:
    return SimpleNamespace(
        provider_kind="gemini",
        base_url="https://generativelanguage.googleapis.com",
        model_id="gemini-3.6-flash",
        reasoning_level="minimal",
    )


def groq_configuration() -> SimpleNamespace:
    return SimpleNamespace(
        provider_kind="groq-cloud",
        base_url="https://api.groq.com/openai/v1",
        model_id="openai/gpt-oss-120b",
        reasoning_level="minimal",
    )


def anthropic_configuration() -> SimpleNamespace:
    return SimpleNamespace(
        provider_kind="anthropic-cloud",
        base_url="https://api.anthropic.com",
        model_id="claude-haiku-4-5-20251001",
        reasoning_level="minimal",
    )


async def no_sleep(_: float) -> None:
    return None


def test_ollama_connection_requires_downloaded_model(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient({"models": [{"name": "qwen2.5:3b"}]}, **kwargs),
    )

    result = asyncio.run(providers.test_provider(ollama_configuration("qwen3:8b")))

    assert not result.ok
    assert "no está descargado" in result.message


def test_ollama_connection_accepts_downloaded_model(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient({"models": [{"name": "qwen2.5:3b"}]}, **kwargs),
    )

    result = asyncio.run(providers.test_provider(ollama_configuration("qwen2.5:3b")))

    assert result.ok
    assert "modelo local validada" in result.message


def test_cloud_connection_requires_credential_registered_in_platform() -> None:
    result = asyncio.run(providers.test_provider(cloud_configuration()))

    assert not result.ok
    assert "desde la plataforma" in result.message


def test_gemini_connection_rejects_unavailable_model(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient({}, status_code=404, **kwargs),
    )

    result = asyncio.run(providers.test_provider(cloud_configuration(), "credential"))

    assert not result.ok
    assert "no está disponible" in result.message


def test_provider_json_parser_accepts_json_fence() -> None:
    assert providers._json_object('```json\n{"contract_version": 1}\n```') == {
        "contract_version": 1
    }


def test_gemini_structured_generation_uses_minimal_thinking() -> None:
    assert providers._gemini_thinking_config("gemini-3.6-flash", "minimal") == {
        "thinkingConfig": {"thinkingLevel": "minimal"}
    }
    assert providers._gemini_thinking_config("gemini-2.5-flash", "minimal") == {
        "thinkingConfig": {"thinkingBudget": 0}
    }
    assert providers._gemini_thinking_config("gemini-3.6-flash", "medium") == {
        "thinkingConfig": {"thinkingLevel": "medium"}
    }
    assert providers._gemini_thinking_config("gemini-3.6-flash", "automatic") == {}


def test_gemini_saturation_has_safe_actionable_message(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(providers.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient({}, status_code=503, **kwargs),
    )

    result = asyncio.run(providers.test_provider(cloud_configuration(), "credential"))

    assert not result.ok
    assert "temporalmente saturado" in result.message


def test_groq_minimal_reasoning_maps_to_supported_low_level() -> None:
    assert providers._groq_reasoning_effort("minimal") == "low"
    assert providers._groq_reasoning_effort("automatic") is None
    assert providers._groq_reasoning_effort("high") == "high"


def test_groq_connection_uses_cloud_credential(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(
            {"choices": [{"message": {"content": '{"ok":true}'}}]}, **kwargs
        ),
    )

    result = asyncio.run(providers.test_provider(groq_configuration(), "groq-secret"))

    assert result.ok


def test_anthropic_connection_uses_messages_api_without_business_data(
    monkeypatch: MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class RecordingClient(FakeAsyncClient):
        async def post(self, url: str, **kwargs: object) -> FakeResponse:
            captured["url"] = url
            captured["headers"] = kwargs.get("headers", {})
            captured["json"] = kwargs.get("json", {})
            return FakeResponse({"content": [{"type": "text", "text": '{"ok":true}'}]})

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: RecordingClient({}, **kwargs),
    )

    result = asyncio.run(providers.test_provider(anthropic_configuration(), "anthropic-secret"))

    assert result.ok
    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["x-api-key"] == "anthropic-secret"
    assert headers["anthropic-version"] == "2023-06-01"
    body = captured["json"]
    assert isinstance(body, dict)
    assert body["model"] == "claude-haiku-4-5-20251001"
    assert body["max_tokens"] == 32
    assert "thinking" not in body


def test_anthropic_generation_includes_schema_contract_and_parses_text_blocks(
    monkeypatch: MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class RecordingClient(FakeAsyncClient):
        async def post(self, url: str, **kwargs: object) -> FakeResponse:
            captured["url"] = url
            captured["json"] = kwargs.get("json", {})
            return FakeResponse({"content": [{"type": "text", "text": '{"answer":"ok"}'}]})

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: RecordingClient({}, **kwargs),
    )

    result = asyncio.run(
        providers.generate_json(
            anthropic_configuration(),
            "Devuelve el contrato solicitado.",
            {"request": "test"},
            credential="anthropic-secret",
            max_output_tokens=640,
            response_schema={
                "type": "object",
                "required": ["answer"],
                "properties": {"answer": {"type": "string"}},
                "additionalProperties": False,
            },
        )
    )

    assert result == {"answer": "ok"}
    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    body = captured["json"]
    assert isinstance(body, dict)
    assert body["max_tokens"] == 640
    assert "properties" in str(body["system"])
    assert body["messages"] == [{"role": "user", "content": '{"request":"test"}'}]
    assert body["output_config"] == {
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "required": ["answer"],
                "properties": {"answer": {"type": "string"}},
                "additionalProperties": False,
            },
        }
    }


def test_anthropic_output_schema_keeps_shape_but_not_unsupported_constraints() -> None:
    original = {
        "type": "object",
        "required": ["items"],
        "properties": {
            "items": {
                "type": "array",
                "minItems": 1,
                "maxItems": 2,
                "items": {
                    "type": "object",
                    "properties": {"name": {"type": "string", "maxLength": 10}},
                    "required": ["name"],
                },
            }
        },
    }

    transformed = providers._anthropic_output_schema(original)

    assert transformed["additionalProperties"] is False
    items = transformed["properties"]["items"]
    assert items["minItems"] == 1
    assert "maxItems" not in items
    assert items["items"]["additionalProperties"] is False
    assert "maxLength" not in items["items"]["properties"]["name"]
    assert original["properties"]["items"]["maxItems"] == 2


def test_anthropic_retries_truncated_structured_output_once(monkeypatch: MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    class SequenceClient(FakeAsyncClient):
        async def post(self, _: str, **kwargs: object) -> FakeResponse:
            body = kwargs["json"]
            assert isinstance(body, dict)
            calls.append(body)
            if len(calls) == 1:
                return FakeResponse(
                    {
                        "stop_reason": "max_tokens",
                        "content": [{"type": "text", "text": '{"answer":'}],
                    }
                )
            return FakeResponse(
                {
                    "stop_reason": "end_turn",
                    "content": [{"type": "text", "text": '{"answer":"ok"}'}],
                }
            )

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: SequenceClient({}, **kwargs),
    )
    result = asyncio.run(
        providers.generate_json(
            anthropic_configuration(),
            "Devuelve JSON.",
            {"request": "test"},
            credential="anthropic-secret",
            max_output_tokens=128,
            response_schema={
                "type": "object",
                "required": ["answer"],
                "properties": {"answer": {"type": "string"}},
                "additionalProperties": False,
            },
        )
    )

    assert result == {"answer": "ok"}
    assert [call["max_tokens"] for call in calls] == [128, 256]


def test_contract_projection_removes_only_surplus_fields_and_items() -> None:
    result = providers._validated_json_object(
        '{"answer":"respuesta extensa","items":[1,2,3],"surplus":true}',
        {
            "type": "object",
            "required": ["answer", "items"],
            "additionalProperties": False,
            "properties": {
                "answer": {"type": "string", "maxLength": 9},
                "items": {
                    "type": "array",
                    "maxItems": 2,
                    "items": {"type": "integer"},
                },
            },
        },
    )

    assert result == {"answer": "respuesta", "items": [1, 2]}


def test_anthropic_retries_once_when_required_contract_field_is_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    class SequenceClient(FakeAsyncClient):
        async def post(self, _: str, **kwargs: object) -> FakeResponse:
            body = kwargs["json"]
            assert isinstance(body, dict)
            calls.append(body)
            content = '{"unexpected":true}' if len(calls) == 1 else '{"answer":"ok"}'
            return FakeResponse({"content": [{"type": "text", "text": content}]})

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: SequenceClient({}, **kwargs),
    )

    result = asyncio.run(
        providers.generate_json(
            anthropic_configuration(),
            "Devuelve el contrato solicitado.",
            {"request": "test"},
            credential="anthropic-secret",
            response_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["answer"],
                "properties": {"answer": {"type": "string"}},
            },
        )
    )

    assert result == {"answer": "ok"}
    assert len(calls) == 2
    assert "REINTENTO ÚNICO DE CONTRATO" in str(calls[1]["system"])


def test_anthropic_discards_second_invalid_contract_response(
    monkeypatch: MonkeyPatch,
) -> None:
    calls = 0

    class InvalidClient(FakeAsyncClient):
        async def post(self, _: str, **__: object) -> FakeResponse:
            nonlocal calls
            calls += 1
            return FakeResponse({"content": [{"type": "text", "text": '{"unexpected":true}'}]})

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: InvalidClient({}, **kwargs),
    )

    with pytest.raises(providers.ProviderGenerationError) as caught:
        asyncio.run(
            providers.generate_json(
                anthropic_configuration(),
                "Devuelve el contrato solicitado.",
                {"request": "test"},
                credential="anthropic-secret",
                response_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["answer"],
                    "properties": {"answer": {"type": "string"}},
                },
            )
        )

    assert calls == 2
    assert caught.value.category == "structured_contract"
    assert "recuperación automática" in str(caught.value)


def test_anthropic_invalid_key_has_safe_message_and_request_id() -> None:
    error = providers._response_error(
        "anthropic-cloud",
        FakeResponse(
            {"error": {"message": "invalid x-api-key", "type": "authentication_error"}},
            status_code=401,
            headers={"request-id": "req-anthropic-401"},
        ),
    )

    assert error.category == "authentication"
    assert error.request_id == "req-anthropic-401"
    assert "API key de Anthropic" in str(error)


def test_groq_connection_reserves_reasoning_budget_and_hides_trace(
    monkeypatch: MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    configuration = groq_configuration()
    configuration.reasoning_level = "high"

    class RecordingClient(FakeAsyncClient):
        async def post(self, _: str, **kwargs: object) -> FakeResponse:
            captured["json"] = kwargs.get("json", {})
            return FakeResponse({"choices": [{"message": {"content": '{"ok":true}'}}]})

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: RecordingClient({}, **kwargs),
    )

    result = asyncio.run(providers.test_provider(configuration, "groq-secret"))

    assert result.ok
    body = captured["json"]
    assert isinstance(body, dict)
    assert body["reasoning_effort"] == "high"
    assert body["include_reasoning"] is False
    assert "reasoning_format" not in body
    assert body["max_completion_tokens"] == 512
    response_format = body["response_format"]
    assert isinstance(response_format, dict)
    assert response_format["type"] == "json_schema"


def test_groq_connection_budget_matches_reasoning_level() -> None:
    assert providers._groq_test_budget("minimal") == 256
    assert providers._groq_test_budget("low") == 256
    assert providers._groq_test_budget("medium") == 384
    assert providers._groq_test_budget("high") == 512


def test_groq_invalid_key_has_safe_message(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient({}, status_code=401, **kwargs),
    )

    result = asyncio.run(providers.test_provider(groq_configuration(), "invalid-secret"))

    assert not result.ok
    assert "API key de Groq" in result.message


def test_groq_connection_rejects_invalid_structured_output(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(
            {"choices": [{"message": {"content": "not-json"}}]}, **kwargs
        ),
    )

    result = asyncio.run(providers.test_provider(groq_configuration(), "groq-secret"))

    assert not result.ok
    assert "no produjo el JSON estructurado" in result.message


def test_groq_generation_requests_strict_json_schema(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class RecordingClient(FakeAsyncClient):
        async def post(self, url: str, **kwargs: object) -> FakeResponse:
            captured["url"] = url
            captured["json"] = kwargs.get("json", {})
            return FakeResponse({"choices": [{"message": {"content": '{"answer":"ok"}'}}]})

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: RecordingClient({}, **kwargs),
    )

    result = asyncio.run(
        providers.generate_json(
            groq_configuration(),
            "Devuelve el contrato solicitado.",
            {"request": "test"},
            credential="groq-secret",
            response_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["answer"],
                "properties": {"answer": {"type": "string"}},
            },
        )
    )

    assert result == {"answer": "ok"}
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    body = captured["json"]
    assert isinstance(body, dict)
    assert body["reasoning_effort"] == "low"
    assert body["include_reasoning"] is False
    assert "reasoning_format" not in body
    response_format = body["response_format"]
    assert isinstance(response_format, dict)
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True  # type: ignore[index]


def test_groq_structured_output_failure_is_not_reported_as_invalid_parameter(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(providers.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(
            {
                "error": {
                    "message": "Failed to validate JSON. Please adjust your prompt.",
                    "type": "invalid_request_error",
                    "code": "json_validate_failed",
                }
            },
            status_code=400,
            **kwargs,
        ),
    )

    result = asyncio.run(providers.test_provider(groq_configuration(), "groq-secret"))

    assert not result.ok
    assert "salida JSON estructurada" in result.message
    assert "nivel de razonamiento es compatible" in result.message
    assert "parámetro" not in result.message


def test_groq_schema_mismatch_is_classified_as_contract_failure() -> None:
    error = providers._generation_error(
        "groq-cloud",
        400,
        (
            "Generated JSON does not match the expected schema. Error: jsonschema: "
            "'/candidates/5/technical_refs' does not validate: maxItems got 4, want 3"
        ),
        "json_validate_failed",
        "req-contract",
    )

    assert error.category == "structured_contract"
    assert error.request_id == "req-contract"
    assert "descartó la respuesta" in str(error)
    assert "presupuesto" not in str(error)


def test_groq_retries_one_rejected_structured_generation_automatically(
    monkeypatch: MonkeyPatch,
) -> None:
    calls = 0
    monkeypatch.setattr(providers.asyncio, "sleep", no_sleep)

    class SequenceClient(FakeAsyncClient):
        async def post(self, _: str, **__: object) -> FakeResponse:
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse(
                    {
                        "error": {
                            "message": "Failed to validate JSON. Please adjust your prompt.",
                            "code": "json_validate_failed",
                        }
                    },
                    status_code=400,
                )
            return FakeResponse({"choices": [{"message": {"content": '{"answer":"ok"}'}}]})

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: SequenceClient({}, **kwargs),
    )

    result = asyncio.run(
        providers.generate_json(
            groq_configuration(),
            "Devuelve el contrato solicitado.",
            {"request": "test"},
            credential="groq-secret",
            response_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["answer"],
                "properties": {"answer": {"type": "string"}},
            },
        )
    )

    assert result == {"answer": "ok"}
    assert calls == 2


def test_groq_falls_back_once_to_locally_validated_json_after_strict_rejections(
    monkeypatch: MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(providers.asyncio, "sleep", no_sleep)

    class SequenceClient(FakeAsyncClient):
        async def post(self, _: str, **kwargs: object) -> FakeResponse:
            payload = kwargs["json"]
            assert isinstance(payload, dict)
            calls.append(payload)
            if len(calls) <= 3:
                return FakeResponse(
                    {
                        "error": {
                            "message": "Generated JSON does not match the expected schema.",
                            "code": "json_validate_failed",
                        }
                    },
                    status_code=400,
                )
            return FakeResponse({"choices": [{"message": {"content": '{"answer":"ok"}'}}]})

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: SequenceClient({}, **kwargs),
    )

    result = asyncio.run(
        providers.generate_json(
            groq_configuration(),
            "Devuelve el contrato solicitado.",
            {"request": "test"},
            credential="groq-secret",
            response_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["answer"],
                "properties": {"answer": {"type": "string"}},
            },
        )
    )

    assert result == {"answer": "ok"}
    assert len(calls) == 4
    assert calls[-1]["response_format"] == {"type": "json_object"}


def test_local_contract_rejects_invalid_json_from_provider_fallback(
    monkeypatch: MonkeyPatch,
) -> None:
    calls = 0
    monkeypatch.setattr(providers.asyncio, "sleep", no_sleep)

    class SequenceClient(FakeAsyncClient):
        async def post(self, _: str, **__: object) -> FakeResponse:
            nonlocal calls
            calls += 1
            if calls <= 3:
                return FakeResponse(
                    {
                        "error": {
                            "message": "Generated JSON does not match the expected schema.",
                            "code": "json_validate_failed",
                        }
                    },
                    status_code=400,
                )
            return FakeResponse({"choices": [{"message": {"content": '{"unexpected":true}'}}]})

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: SequenceClient({}, **kwargs),
    )

    with pytest.raises(providers.ProviderGenerationError) as caught:
        asyncio.run(
            providers.generate_json(
                groq_configuration(),
                "Devuelve el contrato solicitado.",
                {"request": "test"},
                credential="groq-secret",
                response_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["answer"],
                    "properties": {"answer": {"type": "string"}},
                },
            )
        )

    assert caught.value.category == "structured_contract"
    assert "descartada" in str(caught.value)


def test_groq_invalid_parameter_has_specific_message(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(
            {
                "error": {
                    "message": "cannot specify both include_reasoning and reasoning_format",
                    "type": "invalid_request_error",
                }
            },
            status_code=400,
            **kwargs,
        ),
    )

    result = asyncio.run(providers.test_provider(groq_configuration(), "groq-secret"))

    assert not result.ok
    assert "parámetro de generación" in result.message


def test_groq_rate_limit_retries_and_respects_retry_after(monkeypatch: MonkeyPatch) -> None:
    calls = 0
    delays: list[float] = []

    class SequenceClient(FakeAsyncClient):
        async def post(self, _: str, **__: object) -> FakeResponse:
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse(
                    {"error": {"message": "Rate limit reached", "code": "rate_limit"}},
                    status_code=429,
                    headers={"retry-after": "2", "x-request-id": "req-rate-limit"},
                )
            return FakeResponse({"choices": [{"message": {"content": '{"ok":true}'}}]})

    async def record_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(providers.asyncio, "sleep", record_sleep)
    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: SequenceClient({}, **kwargs),
    )

    result = asyncio.run(providers.test_provider(groq_configuration(), "groq-secret"))

    assert result.ok
    assert calls == 2
    assert delays == [2.0]


def test_provider_retry_window_honors_long_refill_without_unbounded_wait() -> None:
    assert (
        providers._retry_delay_seconds(
            FakeResponse({}, status_code=429, headers={"retry-after": "24"}), 1
        )
        == 24.0
    )
    assert (
        providers._retry_delay_seconds(
            FakeResponse({}, status_code=429, headers={"retry-after": "120"}), 1
        )
        == 45.0
    )


def test_groq_rate_limit_stops_after_bounded_attempts(monkeypatch: MonkeyPatch) -> None:
    calls = 0
    monkeypatch.setattr(providers.asyncio, "sleep", no_sleep)

    class RateLimitedClient(FakeAsyncClient):
        async def post(self, _: str, **__: object) -> FakeResponse:
            nonlocal calls
            calls += 1
            return FakeResponse(
                {"error": {"message": "Rate limit reached", "code": "rate_limit"}},
                status_code=429,
                headers={"retry-after": "0", "x-request-id": f"req-rate-{calls}"},
            )

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: RateLimitedClient({}, **kwargs),
    )

    result = asyncio.run(providers.test_provider(groq_configuration(), "groq-secret"))

    assert not result.ok
    assert calls == 3
    assert "límite temporal" in result.message


def test_groq_413_rate_limit_is_retried_and_classified(monkeypatch: MonkeyPatch) -> None:
    calls = 0
    monkeypatch.setattr(providers.asyncio, "sleep", no_sleep)

    class RateLimitedClient(FakeAsyncClient):
        async def post(self, _: str, **__: object) -> FakeResponse:
            nonlocal calls
            calls += 1
            return FakeResponse(
                {
                    "error": {
                        "message": "Rate limit exceeded for tokens",
                        "code": "rate_limit_exceeded",
                    }
                },
                status_code=413,
                headers={"retry-after": "0", "x-request-id": "req-rate-413"},
            )

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: RateLimitedClient({}, **kwargs),
    )

    result = asyncio.run(providers.test_provider(groq_configuration(), "groq-secret"))
    error = providers._response_error(
        "groq-cloud",
        FakeResponse(
            {
                "error": {
                    "message": "Rate limit exceeded for tokens",
                    "code": "rate_limit_exceeded",
                }
            },
            status_code=413,
            headers={"x-request-id": "req-rate-413"},
        ),
    )

    assert not result.ok
    assert calls == 3
    assert "límite temporal" in result.message
    assert error.category == "rate_limit"
    assert error.status_code == 413
    assert error.request_id == "req-rate-413"


def test_groq_error_categories_preserve_safe_request_id() -> None:
    cases = [
        (401, "invalid_api_key", "authentication"),
        (403, "permission_denied", "authorization"),
        (404, "model_not_found", "model_unavailable"),
        (429, "rate_limit", "rate_limit"),
        (503, "unavailable", "provider_unavailable"),
    ]
    for status_code, code, expected_category in cases:
        error = providers._response_error(
            "groq-cloud",
            FakeResponse(
                {"error": {"message": code, "code": code}},
                status_code=status_code,
                headers={"x-request-id": f"req-{code}"},
            ),
        )
        assert error.category == expected_category
        assert error.status_code == status_code
        assert error.request_id == f"req-{code}"


def test_groq_context_or_completion_limit_is_not_reported_as_parameter_error() -> None:
    error = providers._response_error(
        "groq-cloud",
        FakeResponse(
            {"error": {"message": "max_completion_tokens exceeds context length"}},
            status_code=400,
        ),
    )

    assert error.category == "token_budget"
    assert "contexto" in str(error)


def test_groq_http_400_is_not_retried(monkeypatch: MonkeyPatch) -> None:
    calls = 0

    class RecordingClient(FakeAsyncClient):
        async def post(self, _: str, **__: object) -> FakeResponse:
            nonlocal calls
            calls += 1
            return FakeResponse({"error": {"message": "unsupported parameter"}}, status_code=400)

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: RecordingClient({}, **kwargs),
    )

    result = asyncio.run(providers.test_provider(groq_configuration(), "groq-secret"))

    assert not result.ok
    assert calls == 1


def test_groq_timeout_is_retried_once_then_succeeds(monkeypatch: MonkeyPatch) -> None:
    calls = 0
    monkeypatch.setattr(providers.asyncio, "sleep", no_sleep)

    class TimeoutThenSuccessClient(FakeAsyncClient):
        async def post(self, _: str, **__: object) -> FakeResponse:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise httpx.ReadTimeout("temporary timeout")
            return FakeResponse({"choices": [{"message": {"content": '{"ok":true}'}}]})

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: TimeoutThenSuccessClient({}, **kwargs),
    )

    result = asyncio.run(providers.test_provider(groq_configuration(), "groq-secret"))

    assert result.ok
    assert calls == 2


def test_groq_retries_server_error_then_succeeds(monkeypatch: MonkeyPatch) -> None:
    calls = 0
    monkeypatch.setattr(providers.asyncio, "sleep", no_sleep)

    class ServerErrorThenSuccessClient(FakeAsyncClient):
        async def post(self, _: str, **__: object) -> FakeResponse:
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse({"error": {"message": "unavailable"}}, status_code=503)
            return FakeResponse({"choices": [{"message": {"content": '{"ok":true}'}}]})

    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: ServerErrorThenSuccessClient({}, **kwargs),
    )

    result = asyncio.run(providers.test_provider(groq_configuration(), "groq-secret"))

    assert result.ok
    assert calls == 2
