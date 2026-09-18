from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.modules.parameters.models import LlmConfiguration


@dataclass(frozen=True)
class ProviderTestResult:
    ok: bool
    message: str


async def test_provider(
    configuration: LlmConfiguration,
    credential: str | None = None,
    timeout_seconds: int = 12,
) -> ProviderTestResult:
    if configuration.provider_kind != "ollama-local" and not credential:
        return ProviderTestResult(
            False, "Registre una credencial desde la plataforma antes de probar la conexión."
        )
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False) as client:
            base_url = configuration.base_url.rstrip("/")
            if configuration.provider_kind == "ollama-local":
                response = await client.get(f"{base_url}/api/tags")
                if 200 <= response.status_code < 300:
                    available_models = {
                        str(model.get("name", "")) for model in response.json().get("models", [])
                    }
                    if configuration.model_id not in available_models:
                        return ProviderTestResult(
                            False,
                            (
                                "El servicio Ollama está disponible, pero el modelo configurado "
                                "no está descargado."
                            ),
                        )
                    return ProviderTestResult(
                        True,
                        "Conexión con Ollama y modelo local validada sin enviar datos del negocio.",
                    )
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
