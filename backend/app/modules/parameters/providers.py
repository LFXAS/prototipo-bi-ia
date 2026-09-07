from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.modules.parameters.models import LlmConfiguration


@dataclass(frozen=True)
class ProviderTestResult:
    ok: bool
    message: str


def credential_for(configuration: LlmConfiguration) -> str | None:
    values = {
        "gemini": settings.gemini_api_key,
        "qwen-cloud": settings.dashscope_api_key,
        "ollama-local": None,
    }
    secret = values[configuration.provider_kind]
    return secret.get_secret_value() if secret is not None else None


async def test_provider(configuration: LlmConfiguration) -> ProviderTestResult:
    credential = credential_for(configuration)
    if configuration.provider_kind != "ollama-local" and not credential:
        return ProviderTestResult(
            False, "La referencia de credencial no está disponible en el entorno."
        )
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
            base_url = configuration.base_url.rstrip("/")
            if configuration.provider_kind == "ollama-local":
                response = await client.get(f"{base_url}/api/tags")
            elif configuration.provider_kind == "gemini":
                response = await client.get(f"{base_url}/v1beta/models", params={"key": credential})
            else:
                response = await client.post(
                    f"{base_url}/api/v1/services/aigc/text-generation/generation",
                    headers={"Authorization": f"Bearer {credential}"},
                    json={
                        "model": configuration.model_id,
                        "input": {"messages": [{"role": "user", "content": "ping"}]},
                        "parameters": {"max_tokens": 1},
                    },
                )
    except httpx.HTTPError:
        return ProviderTestResult(False, "No fue posible conectar con el proveedor configurado.")
    if 200 <= response.status_code < 300:
        return ProviderTestResult(
            True, "Conexión con el proveedor validada sin enviar datos del negocio."
        )
    return ProviderTestResult(
        False, f"El proveedor respondió con estado HTTP {response.status_code}."
    )
