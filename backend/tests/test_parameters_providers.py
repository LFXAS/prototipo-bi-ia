from __future__ import annotations

import asyncio
from types import SimpleNamespace

from pytest import MonkeyPatch

from app.modules.parameters import providers


class FakeResponse:
    status_code = 200

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def json(self) -> dict[str, object]:
        return self.payload


class FakeAsyncClient:
    def __init__(self, payload: dict[str, object], **_: object) -> None:
        self.payload = payload

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def get(self, _: str, **__: object) -> FakeResponse:
        return FakeResponse(self.payload)


def ollama_configuration(model_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        provider_kind="ollama-local",
        base_url="http://ollama:11434",
        model_id=model_id,
    )


def cloud_configuration() -> SimpleNamespace:
    return SimpleNamespace(
        provider_kind="gemini",
        base_url="https://generativelanguage.googleapis.com",
        model_id="gemini-2.5-flash",
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
