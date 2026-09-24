from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.modules.parameters.models import LlmConfiguration


@dataclass(frozen=True)
class ProviderTestResult:
    ok: bool
    message: str


class ProviderGenerationError(RuntimeError):
    """Safe provider failure that never contains a credential or raw response."""


def _gemini_thinking_config(model_id: str, reasoning_level: str) -> dict[str, object]:
    """Keep bounded structured responses from spending their output budget on reasoning."""
    if reasoning_level == "automatic":
        return {}
    if model_id.startswith("gemini-3"):
        return {"thinkingConfig": {"thinkingLevel": reasoning_level}}
    if model_id.startswith("gemini-2.5-flash") and reasoning_level == "minimal":
        return {"thinkingConfig": {"thinkingBudget": 0}}
    if reasoning_level in {"low", "medium", "high"}:
        return {"thinkingConfig": {"thinkingLevel": reasoning_level}}
    return {}


def _groq_reasoning_effort(reasoning_level: str) -> str | None:
    """Map the shared UI vocabulary to the levels supported by GPT-OSS on Groq."""
    if reasoning_level == "automatic":
        return None
    if reasoning_level == "minimal":
        return "low"
    if reasoning_level in {"low", "medium", "high"}:
        return reasoning_level
    return "low"


def _generation_error(provider_kind: str, status_code: int) -> ProviderGenerationError:
    if provider_kind == "gemini" and status_code == 503:
        return ProviderGenerationError(
            "Gemini está temporalmente saturado. Reintente la generación en unos minutos."
        )
    if status_code == 429:
        return ProviderGenerationError("El proveedor agotó temporalmente su cuota disponible.")
    return ProviderGenerationError(f"El proveedor respondió con estado HTTP {status_code}.")


def _json_object(value: object) -> dict[str, Any]:
    if not isinstance(value, str):
        raise ProviderGenerationError("El proveedor no devolvió una respuesta utilizable.")
    candidate = value.strip()
    if candidate.startswith("```"):
        candidate = candidate.removeprefix("```json").removeprefix("```")
        candidate = candidate.removesuffix("```").strip()
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise ProviderGenerationError(
                "El proveedor no devolvió un documento JSON válido."
            ) from exc
        try:
            parsed = json.loads(candidate[start : end + 1])
        except json.JSONDecodeError as nested_exc:
            raise ProviderGenerationError(
                "El proveedor no devolvió un documento JSON válido."
            ) from nested_exc
    if not isinstance(parsed, dict):
        raise ProviderGenerationError("El proveedor no devolvió un objeto JSON.")
    return parsed


async def generate_json(
    configuration: LlmConfiguration,
    system_instruction: str,
    payload: dict[str, Any],
    credential: str | None = None,
    timeout_seconds: int = 30,
    max_output_tokens: int = 2048,
    response_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Request a bounded JSON document from an approved provider endpoint."""
    if configuration.provider_kind != "ollama-local" and not credential:
        raise ProviderGenerationError("La configuración activa no tiene una credencial disponible.")
    user_content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False) as client:
            base_url = configuration.base_url.rstrip("/")
            if configuration.provider_kind == "ollama-local":
                response = await client.post(
                    f"{base_url}/api/chat",
                    json={
                        "model": configuration.model_id,
                        "stream": False,
                        "format": response_schema or "json",
                        "think": False,
                        "options": {"temperature": 0, "num_predict": max_output_tokens},
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_content},
                        ],
                    },
                )
                if not 200 <= response.status_code < 300:
                    raise ProviderGenerationError(
                        f"El proveedor respondió con estado HTTP {response.status_code}."
                    )
                content = response.json().get("message", {}).get("content")
            elif configuration.provider_kind == "gemini":
                response = await client.post(
                    f"{base_url}/v1beta/models/{configuration.model_id}:generateContent",
                    params={"key": credential},
                    json={
                        "systemInstruction": {"parts": [{"text": system_instruction}]},
                        "contents": [{"role": "user", "parts": [{"text": user_content}]}],
                        "generationConfig": {
                            "temperature": 0,
                            "responseMimeType": "application/json",
                            "maxOutputTokens": max_output_tokens,
                            **_gemini_thinking_config(
                                configuration.model_id,
                                configuration.reasoning_level,
                            ),
                            **(
                                {"responseJsonSchema": response_schema}
                                if response_schema is not None
                                else {}
                            ),
                        },
                    },
                )
                if not 200 <= response.status_code < 300:
                    raise _generation_error(configuration.provider_kind, response.status_code)
                candidates = response.json().get("candidates", [])
                content = (
                    candidates[0].get("content", {}).get("parts", [{}])[0].get("text")
                    if candidates
                    else None
                )
            elif configuration.provider_kind == "groq-cloud":
                reasoning_effort = _groq_reasoning_effort(configuration.reasoning_level)
                response_format: dict[str, object]
                if response_schema is None:
                    response_format = {"type": "json_object"}
                else:
                    response_format = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "bi_structured_response",
                            "strict": True,
                            "schema": response_schema,
                        },
                    }
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {credential}"},
                    json={
                        "model": configuration.model_id,
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_content},
                        ],
                        "temperature": 0,
                        "max_completion_tokens": max_output_tokens,
                        "response_format": response_format,
                        **(
                            {"reasoning_effort": reasoning_effort}
                            if reasoning_effort is not None
                            else {}
                        ),
                    },
                )
                if not 200 <= response.status_code < 300:
                    raise _generation_error(configuration.provider_kind, response.status_code)
                choices = response.json().get("choices", [])
                content = choices[0].get("message", {}).get("content") if choices else None
            else:
                response = await client.post(
                    f"{base_url}/api/v1/services/aigc/text-generation/generation",
                    headers={"Authorization": f"Bearer {credential}"},
                    json={
                        "model": configuration.model_id,
                        "input": {
                            "messages": [
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": user_content},
                            ]
                        },
                        "parameters": {
                            "temperature": 0,
                            "result_format": "message",
                            "max_tokens": max_output_tokens,
                        },
                    },
                )
                if not 200 <= response.status_code < 300:
                    raise ProviderGenerationError(
                        f"El proveedor respondió con estado HTTP {response.status_code}."
                    )
                choices = response.json().get("output", {}).get("choices", [])
                content = choices[0].get("message", {}).get("content") if choices else None
    except httpx.TimeoutException as exc:
        raise ProviderGenerationError("El proveedor excedió el tiempo máximo configurado.") from exc
    except httpx.HTTPError as exc:
        raise ProviderGenerationError("No fue posible conectar con el proveedor activo.") from exc
    return _json_object(content)


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
                response = await client.post(
                    f"{base_url}/v1beta/models/{configuration.model_id}:generateContent",
                    params={"key": credential},
                    json={
                        "contents": [
                            {
                                "role": "user",
                                "parts": [
                                    {
                                        "text": (
                                            'Responde únicamente con el objeto JSON {"ok":true}.'
                                        )
                                    }
                                ],
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0,
                            "responseMimeType": "application/json",
                            "maxOutputTokens": 20,
                            **_gemini_thinking_config(
                                configuration.model_id,
                                configuration.reasoning_level,
                            ),
                        },
                    },
                )
            elif configuration.provider_kind == "groq-cloud":
                reasoning_effort = _groq_reasoning_effort(configuration.reasoning_level)
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {credential}"},
                    json={
                        "model": configuration.model_id,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Responde únicamente con un objeto JSON válido.",
                            },
                            {"role": "user", "content": 'Devuelve {"ok":true}.'},
                        ],
                        "temperature": 0,
                        "max_completion_tokens": 32,
                        "response_format": {"type": "json_object"},
                        **(
                            {"reasoning_effort": reasoning_effort}
                            if reasoning_effort is not None
                            else {}
                        ),
                    },
                )
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
    if configuration.provider_kind == "gemini" and response.status_code == 404:
        return ProviderTestResult(
            False,
            "El modelo Gemini configurado no está disponible para este proyecto.",
        )
    if configuration.provider_kind == "gemini" and response.status_code == 403:
        return ProviderTestResult(
            False,
            "El proyecto asociado a la clave no tiene acceso al modelo Gemini configurado.",
        )
    if configuration.provider_kind == "gemini" and response.status_code == 503:
        return ProviderTestResult(
            False,
            "Gemini está temporalmente saturado. Reintente la prueba en unos minutos.",
        )
    if configuration.provider_kind == "groq-cloud" and response.status_code == 401:
        return ProviderTestResult(False, "La API key de Groq no es válida o fue revocada.")
    if configuration.provider_kind == "groq-cloud" and response.status_code == 404:
        return ProviderTestResult(False, "El modelo configurado no está disponible en Groq.")
    if configuration.provider_kind == "groq-cloud" and response.status_code == 503:
        return ProviderTestResult(
            False, "Groq está temporalmente saturado. Reintente la prueba en unos minutos."
        )
    if response.status_code == 429:
        return ProviderTestResult(False, "El proveedor agotó temporalmente su cuota disponible.")
    return ProviderTestResult(
        False, f"El proveedor respondió con estado HTTP {response.status_code}."
    )
