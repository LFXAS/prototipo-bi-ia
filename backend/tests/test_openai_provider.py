from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from app.modules.parameters import providers
from app.modules.parameters.schemas import LlmConfigurationCreate


def configuration(model: str = "gpt-6.2-sol", effort: str = "medium") -> SimpleNamespace:
    return SimpleNamespace(
        provider_kind="openai-cloud",
        base_url="https://api.openai.com/v1",
        model_id=model,
        reasoning_level=effort,
    )


def envelope(text: str = '{"ok":true}', **overrides: Any) -> dict[str, Any]:
    return {
        "status": "completed",
        "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [{"type": "output_text", "text": text}]},
        ],
        **overrides,
    }


def client_stub(
    monkeypatch: MonkeyPatch,
    payload: dict[str, Any],
    status: int = 200,
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    class Response:
        status_code = status
        headers: dict[str, str] = {}

        def json(self) -> dict[str, Any]:
            return payload

    class Client:
        async def __aenter__(self) -> Client:
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(self, url: str, **kwargs: Any) -> Response:
            calls.append({"url": url, **kwargs})
            return Response()

    monkeypatch.setattr(providers.httpx, "AsyncClient", lambda **_: Client())
    return calls


SCHEMA = {
    "type": "object",
    "properties": {"ok": {"type": "boolean"}},
    "required": ["ok"],
    "additionalProperties": False,
}


def test_openai_configuration_accepts_only_official_endpoint() -> None:
    model = LlmConfigurationCreate(
        name="OpenAI para BI",
        provider_kind="openai-cloud",
        base_url="https://api.openai.com/v1",
        model_id="gpt-6.2-sol",
        reasoning_level="medium",
    )
    assert model.provider_kind == "openai-cloud"
    for endpoint in (
        "http://api.openai.com/v1",
        "https://api.openai.com.example.test/v1",
        "https://api.openai.com/v1/responses",
        "https://api.openai.com/v1?key=not-a-secret",
        "https://untrusted@api.openai.com/v1",
        "https://api.openai.com:8443/v1",
    ):
        with pytest.raises(ValidationError):
            LlmConfigurationCreate(
                name="OpenAI no permitido",
                provider_kind="openai-cloud",
                base_url=endpoint,
                model_id="gpt-6.2-sol",
            )


@pytest.mark.parametrize(
    ("model", "effort", "expected"),
    [
        ("gpt-6.2-sol", "medium", {"reasoning": {"effort": "medium"}}),
        ("gpt-6.2-sol", "minimal", {"reasoning": {"effort": "low"}}),
        ("gpt-6.1-sol", "minimal", {"reasoning": {"effort": "low"}}),
        ("gpt-5-mini", "minimal", {"reasoning": {"effort": "low"}}),
        ("gpt-5.5", "high", {"reasoning": {"effort": "high"}}),
        ("gpt-6.2-sol", "automatic", {}),
        ("gpt-4.1", "medium", {}),
    ],
)
def test_openai_reasoning_mapping_is_model_compatible(
    model: str, effort: str, expected: dict[str, Any]
) -> None:
    assert providers._openai_reasoning_options(model, effort) == expected


def test_openai_uses_responses_strict_schema_and_does_not_store_output(
    monkeypatch: MonkeyPatch,
) -> None:
    calls = client_stub(monkeypatch, envelope())
    document = asyncio.run(
        providers.generate_json(
            configuration(),
            "Valida el contrato BI.",
            {"structural_metadata": "no rows"},
            credential="test-key",
            max_output_tokens=2048,
            response_schema=SCHEMA,
        )
    )
    assert document == {"ok": True}
    assert len(calls) == 1
    request = calls[0]
    assert request["url"] == "https://api.openai.com/v1/responses"
    assert request["headers"] == {"Authorization": "Bearer test-key"}
    body = request["json"]
    assert body["store"] is False
    assert body["max_output_tokens"] == 8192
    assert body["reasoning"] == {"effort": "medium"}
    assert "temperature" not in body
    assert body["input"][0]["role"] == "developer"
    assert body["text"]["format"]["strict"] is True
    assert body["text"]["format"]["schema"] == SCHEMA


@pytest.mark.parametrize(
    ("model", "effort", "requested", "expected"),
    [
        ("gpt-6.2-sol", "minimal", 450, 4096),
        ("gpt-6.2-sol", "low", 1200, 4096),
        ("gpt-6.2-sol", "automatic", 700, 4096),
        ("gpt-6.2-sol", "medium", 1200, 8192),
        ("gpt-6.2-sol", "high", 2400, 16384),
        ("gpt-5.5", "medium", 12000, 12000),
        ("gpt-6.2-sol", "high", 64000, 32768),
        ("gpt-4.1", "medium", 1024, 1024),
        ("future-model", "medium", 4096, 4096),
    ],
)
def test_openai_reserves_bounded_shared_reasoning_output_budget(
    model: str, effort: str, requested: int, expected: int
) -> None:
    assert providers._openai_output_budget(model, effort, requested) == expected


def test_openai_optional_nulls_restore_absence_without_mutating_canonical_schema(
    monkeypatch: MonkeyPatch,
) -> None:
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "maxLength": 20},
            "details": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"code": {"type": "string"}, "note": {"type": "string"}},
                    "required": ["code"],
                    "additionalProperties": False,
                },
            },
            "note": {"type": "string"},
        },
        "required": ["name", "details"],
        "additionalProperties": False,
    }
    original = deepcopy(schema)
    calls = client_stub(
        monkeypatch,
        envelope('{"name":"Ventas","details":[{"code":"sales","note":null}],"note":null}'),
    )
    document = asyncio.run(
        providers.generate_json(configuration(), "Contrato", {}, "test-key", response_schema=schema)
    )
    assert document == {"name": "Ventas", "details": [{"code": "sales"}]}
    assert schema == original
    transport = calls[0]["json"]["text"]["format"]["schema"]
    assert transport["required"] == ["name", "details", "note"]
    assert transport["properties"]["note"] == {"anyOf": [{"type": "string"}, {"type": "null"}]}
    assert transport["properties"]["details"]["items"]["required"] == ["code", "note"]


def test_openai_required_invalid_null_is_rejected_by_original_contract(
    monkeypatch: MonkeyPatch,
) -> None:
    calls = client_stub(monkeypatch, envelope('{"ok":null}'))
    with pytest.raises(providers.ProviderGenerationError) as error:
        asyncio.run(
            providers.generate_json(
                configuration(),
                "Contrato",
                {},
                "test-key",
                response_schema=SCHEMA,
                _allow_contract_retry=False,
            )
        )
    assert error.value.category == "structured_contract"
    assert len(calls) == 1


def test_openai_all_pipeline_schemas_satisfy_strict_container_requirements() -> None:
    from app.modules.analytics.router import _ANALYTICS_COPILOT_SCHEMA
    from app.modules.copilot.need_advisor import DRAFT_SCHEMA, SUGGESTION_SCHEMA
    from app.modules.copilot.service import PROPOSAL_RESPONSE_SCHEMA, SEMANTIC_RESPONSE_SCHEMA
    from app.modules.etl.router import _LOCALIZATION_SCHEMA

    def check(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node["properties"])
            if node.get("type") == "array":
                assert isinstance(node["items"], dict)
            for child in node.values():
                check(child)
        if isinstance(node, list):
            for child in node:
                check(child)

    for original in (
        DRAFT_SCHEMA,
        SUGGESTION_SCHEMA,
        PROPOSAL_RESPONSE_SCHEMA,
        SEMANTIC_RESPONSE_SCHEMA,
        _LOCALIZATION_SCHEMA,
        _ANALYTICS_COPILOT_SCHEMA,
    ):
        check(providers._openai_output_schema(original))


@pytest.mark.parametrize(
    ("payload", "category"),
    [
        (
            envelope(status="incomplete", incomplete_details={"reason": "max_output_tokens"}),
            "token_budget",
        ),
        (
            envelope(status="incomplete", incomplete_details={"reason": "content_filter"}),
            "structured_output",
        ),
        (envelope(status="failed"), "provider_error"),
        (envelope(status="incomplete", incomplete_details="unexpected"), "structured_output"),
        (
            envelope(
                output=[{"type": "message", "content": [{"type": "refusal", "refusal": "no"}]}]
            ),
            "refusal",
        ),
        (
            envelope(output=[{"type": "reasoning", "summary": [{"text": '{"ok":true}'}]}]),
            "structured_output",
        ),
    ],
)
def test_openai_rejects_incomplete_refused_or_reasoning_only_output(
    monkeypatch: MonkeyPatch, payload: dict[str, Any], category: str
) -> None:
    calls = client_stub(monkeypatch, payload)
    with pytest.raises(providers.ProviderGenerationError) as error:
        asyncio.run(providers.generate_json(configuration(), "Contrato", {}, "test-key"))
    assert error.value.category == category
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("status", "code", "category"),
    [
        (401, "invalid_api_key", "authentication"),
        (403, "permission_denied", "authorization"),
        (404, "model_not_found", "model_unavailable"),
        (400, "invalid_json_schema", "invalid_parameter"),
        (429, "insufficient_quota", "quota_exhausted"),
        (429, "credit_balance_exhausted", "quota_exhausted"),
        (429, "billing_hard_limit_reached", "quota_exhausted"),
    ],
)
def test_openai_permanent_failures_are_safe_and_not_retried(
    monkeypatch: MonkeyPatch, status: int, code: str, category: str
) -> None:
    calls = client_stub(
        monkeypatch, {"error": {"code": code, "message": "provider may echo test-key"}}, status
    )
    with pytest.raises(providers.ProviderGenerationError) as error:
        asyncio.run(providers.generate_json(configuration(), "Contrato", {}, "test-key"))
    assert error.value.category == category
    assert "test-key" not in str(error.value)
    assert len(calls) == 1


def test_openai_connection_exercises_same_structured_envelope(monkeypatch: MonkeyPatch) -> None:
    calls = client_stub(monkeypatch, envelope())
    result = asyncio.run(providers.test_provider(configuration(), "test-key"))
    assert result.ok
    assert "salida estructurada" in result.message
    assert len(calls) == 1
    assert json.loads(calls[0]["json"]["input"][1]["content"]) == {
        "request": 'Devuelve {"ok":true}.'
    }


def test_openai_connection_requires_credential() -> None:
    result = asyncio.run(providers.test_provider(configuration()))
    assert not result.ok
    assert "Registre una credencial" in result.message


def test_openai_connection_does_not_accept_false_ok(monkeypatch: MonkeyPatch) -> None:
    client_stub(monkeypatch, envelope('{"ok":false}'))
    result = asyncio.run(providers.test_provider(configuration(), "test-key"))
    assert not result.ok


def test_openai_non_json_http_body_is_discarded_safely(monkeypatch: MonkeyPatch) -> None:
    class InvalidResponse:
        status_code = 200
        headers: dict[str, str] = {}

        def json(self) -> object:
            raise ValueError("untrusted response body")

    async def invalid_post(*_: object, **__: object) -> InvalidResponse:
        return InvalidResponse()

    monkeypatch.setattr(providers, "_post_with_retry", invalid_post)
    with pytest.raises(providers.ProviderGenerationError) as error:
        asyncio.run(providers.generate_json(configuration(), "Contrato", {}, "test-key"))
    assert error.value.category == "structured_output"
    assert "untrusted" not in str(error.value)
