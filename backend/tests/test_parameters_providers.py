from __future__ import annotations

import asyncio
from types import SimpleNamespace

from pytest import MonkeyPatch

from app.modules.parameters import providers


class FakeResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

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
    monkeypatch.setattr(
        providers.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient({}, status_code=503, **kwargs),
    )

    result = asyncio.run(providers.test_provider(cloud_configuration(), "credential"))

    assert not result.ok
    assert "temporalmente saturado" in result.message
