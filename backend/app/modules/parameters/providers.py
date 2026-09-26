from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.modules.parameters.models import LlmConfiguration

logger = logging.getLogger(__name__)

_TRANSIENT_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
_MAX_PROVIDER_ATTEMPTS = 3


@dataclass(frozen=True)
class ProviderTestResult:
    ok: bool
    message: str


class ProviderGenerationError(RuntimeError):
    """Safe provider failure that never contains a credential or raw response."""

    def __init__(
        self,
        message: str,
        *,
        category: str = "provider_error",
        status_code: int | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.status_code = status_code
        self.request_id = request_id


@dataclass(frozen=True)
class ProviderErrorDetails:
    message: str = ""
    code: str = ""
    request_id: str = ""


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


def _groq_reasoning_options(model_id: str, reasoning_level: str) -> dict[str, object]:
    """Use the reasoning controls documented for each Groq model family."""
    effort = _groq_reasoning_effort(reasoning_level)
    result: dict[str, object] = {}
    if effort is not None:
        result["reasoning_effort"] = effort
    if model_id.startswith("openai/gpt-oss-"):
        result["include_reasoning"] = False
    else:
        result["reasoning_format"] = "hidden"
    return result


def _groq_test_budget(reasoning_level: str) -> int:
    effort = _groq_reasoning_effort(reasoning_level)
    return {"medium": 384, "high": 512}.get(effort or "low", 256)


def _provider_error_details(response: Any) -> ProviderErrorDetails:
    headers = getattr(response, "headers", {})
    request_id = str(headers.get("x-request-id", "") or headers.get("request-id", ""))[:160]
    try:
        payload = response.json()
    except (AttributeError, ValueError):
        return ProviderErrorDetails(request_id=request_id)
    if not isinstance(payload, dict) or not isinstance(payload.get("error"), dict):
        return ProviderErrorDetails(request_id=request_id)
    return ProviderErrorDetails(
        message=str(payload["error"].get("message", ""))[:500],
        code=str(payload["error"].get("code", ""))[:120],
        request_id=request_id,
    )


def _provider_error_message(response: Any) -> str:
    return _provider_error_details(response).message


def _retry_delay_seconds(response: Any, attempt: int) -> float:
    headers = getattr(response, "headers", {})
    raw_retry_after = headers.get("retry-after")
    if raw_retry_after is not None:
        try:
            retry_after = float(str(raw_retry_after))
            return min(max(retry_after, 0.0), 10.0)
        except (TypeError, ValueError):
            pass
    return float(min(0.25 * (2 ** (attempt - 1)), 2.0))


def _is_transient_response(response: Any) -> bool:
    status_code = int(getattr(response, "status_code", 0))
    if status_code in _TRANSIENT_STATUS_CODES:
        return True
    details = _provider_error_details(response)
    normalized = f"{details.code} {details.message}".casefold()
    return status_code == 413 and any(
        marker in normalized for marker in ("rate_limit", "rate limit", "too many requests")
    )


def _log_provider_response(
    provider_kind: str,
    model_id: str,
    attempt: int,
    response: Any,
) -> None:
    status_code = int(getattr(response, "status_code", 0))
    headers = getattr(response, "headers", {})
    details = (
        _provider_error_details(response)
        if status_code >= 300
        else ProviderErrorDetails(
            request_id=str(headers.get("x-request-id", "") or headers.get("request-id", ""))[:160]
        )
    )
    log = logger.warning if status_code >= 300 else logger.info
    log(
        "llm_provider_response provider=%s model=%s attempt=%s status=%s code=%s "
        "request_id=%s remaining_requests=%s remaining_tokens=%s retry_after=%s",
        provider_kind,
        model_id,
        attempt,
        status_code,
        details.code or "none",
        details.request_id or "none",
        headers.get("x-ratelimit-remaining-requests", "unknown"),
        headers.get("x-ratelimit-remaining-tokens", "unknown"),
        headers.get("retry-after", "none"),
    )


async def _post_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    provider_kind: str,
    model_id: str,
    max_attempts: int = _MAX_PROVIDER_ATTEMPTS,
    **kwargs: Any,
) -> Any:
    for attempt in range(1, max_attempts + 1):
        try:
            response = await client.post(url, **kwargs)
        except httpx.TimeoutException:
            logger.warning(
                "llm_provider_timeout provider=%s model=%s attempt=%s",
                provider_kind,
                model_id,
                attempt,
            )
            if attempt >= max_attempts:
                raise
            await asyncio.sleep(min(0.25 * (2 ** (attempt - 1)), 2.0))
            continue
        _log_provider_response(provider_kind, model_id, attempt, response)
        if not _is_transient_response(response) or attempt >= max_attempts:
            return response
        await asyncio.sleep(_retry_delay_seconds(response, attempt))
    raise RuntimeError("unreachable provider retry state")


def _generation_error(
    provider_kind: str,
    status_code: int,
    provider_message: str = "",
    provider_code: str = "",
    request_id: str = "",
) -> ProviderGenerationError:
    normalized = provider_message.casefold()

    def error(message: str, category: str) -> ProviderGenerationError:
        return ProviderGenerationError(
            message,
            category=category,
            status_code=status_code,
            request_id=request_id or None,
        )

    if provider_kind == "gemini" and status_code == 404:
        return error(
            "El modelo Gemini configurado no está disponible para este proyecto.",
            "model_unavailable",
        )
    if provider_kind == "gemini" and status_code == 403:
        return error(
            "El proyecto asociado a la clave no tiene acceso al modelo Gemini configurado.",
            "authorization",
        )
    if provider_kind == "gemini" and status_code == 503:
        return error(
            "Gemini está temporalmente saturado. Reintente la generación en unos minutos.",
            "provider_unavailable",
        )
    if provider_kind == "groq-cloud" and status_code == 401:
        return error(
            "La API key de Groq no es válida o fue revocada.",
            "authentication",
        )
    if provider_kind == "groq-cloud" and status_code == 403:
        return error(
            "La cuenta de Groq no tiene acceso al modelo o a esta operación.",
            "authorization",
        )
    if provider_kind == "groq-cloud" and status_code == 404:
        return error(
            "El modelo configurado no está disponible en Groq.",
            "model_unavailable",
        )
    if status_code == 429 or (
        status_code == 413
        and any(
            marker in f"{provider_code} {normalized}"
            for marker in ("rate_limit", "rate limit", "too many requests")
        )
    ):
        return error(
            "El proveedor alcanzó un límite temporal de solicitudes o tokens. Los reintentos "
            "automáticos no fueron suficientes; espere el tiempo indicado y vuelva a intentar.",
            "rate_limit",
        )
    if status_code in {500, 502, 503, 504}:
        return error(
            "El proveedor continúa temporalmente no disponible después de los reintentos seguros.",
            "provider_unavailable",
        )
    if provider_kind == "groq-cloud" and status_code == 400:
        if provider_code == "json_validate_failed" or "validate json" in normalized:
            return error(
                "Groq no completó la salida JSON estructurada dentro del presupuesto disponible. "
                "El nivel de razonamiento es compatible; reduzca la complejidad o aumente el "
                "presupuesto de salida.",
                "structured_output",
            )
        if any(
            phrase in normalized
            for phrase in ("context length", "max_completion_tokens", "too many tokens")
        ):
            return error(
                "La solicitud excede el contexto o el presupuesto de salida permitido por Groq.",
                "token_budget",
            )
        return error(
            "Groq rechazó un parámetro de generación. Revise la compatibilidad del modelo y "
            "la configuración enviada.",
            "invalid_parameter",
        )
    return error(
        f"El proveedor respondió con estado HTTP {status_code}.",
        "provider_error",
    )


def _response_error(provider_kind: str, response: Any) -> ProviderGenerationError:
    details = _provider_error_details(response)
    return _generation_error(
        provider_kind,
        int(response.status_code),
        details.message,
        details.code,
        details.request_id,
    )


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
                response = await _post_with_retry(
                    client,
                    f"{base_url}/api/chat",
                    provider_kind=configuration.provider_kind,
                    model_id=configuration.model_id,
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
                    raise _response_error(configuration.provider_kind, response)
                content = response.json().get("message", {}).get("content")
            elif configuration.provider_kind == "gemini":
                response = await _post_with_retry(
                    client,
                    f"{base_url}/v1beta/models/{configuration.model_id}:generateContent",
                    provider_kind=configuration.provider_kind,
                    model_id=configuration.model_id,
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
                    raise _response_error(configuration.provider_kind, response)
                candidates = response.json().get("candidates", [])
                content = (
                    candidates[0].get("content", {}).get("parts", [{}])[0].get("text")
                    if candidates
                    else None
                )
            elif configuration.provider_kind == "groq-cloud":
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
                response = await _post_with_retry(
                    client,
                    f"{base_url}/chat/completions",
                    provider_kind=configuration.provider_kind,
                    model_id=configuration.model_id,
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
                        **_groq_reasoning_options(
                            configuration.model_id,
                            configuration.reasoning_level,
                        ),
                    },
                )
                if not 200 <= response.status_code < 300:
                    raise _response_error(configuration.provider_kind, response)
                choices = response.json().get("choices", [])
                content = choices[0].get("message", {}).get("content") if choices else None
            else:
                response = await _post_with_retry(
                    client,
                    f"{base_url}/api/v1/services/aigc/text-generation/generation",
                    provider_kind=configuration.provider_kind,
                    model_id=configuration.model_id,
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
                    raise _response_error(configuration.provider_kind, response)
                choices = response.json().get("output", {}).get("choices", [])
                content = choices[0].get("message", {}).get("content") if choices else None
    except httpx.TimeoutException as exc:
        raise ProviderGenerationError(
            "El proveedor excedió el tiempo máximo configurado después de los reintentos seguros.",
            category="timeout",
        ) from exc
    except httpx.HTTPError as exc:
        raise ProviderGenerationError(
            "No fue posible conectar con el proveedor activo.",
            category="connection",
        ) from exc
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
                response = await _post_with_retry(
                    client,
                    f"{base_url}/v1beta/models/{configuration.model_id}:generateContent",
                    provider_kind=configuration.provider_kind,
                    model_id=configuration.model_id,
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
                response = await _post_with_retry(
                    client,
                    f"{base_url}/chat/completions",
                    provider_kind=configuration.provider_kind,
                    model_id=configuration.model_id,
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
                        "max_completion_tokens": _groq_test_budget(configuration.reasoning_level),
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "connection_test",
                                "strict": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {"ok": {"type": "boolean"}},
                                    "required": ["ok"],
                                    "additionalProperties": False,
                                },
                            },
                        },
                        **_groq_reasoning_options(
                            configuration.model_id,
                            configuration.reasoning_level,
                        ),
                    },
                )
            else:
                response = await _post_with_retry(
                    client,
                    f"{base_url}/api/v1/services/aigc/text-generation/generation",
                    provider_kind=configuration.provider_kind,
                    model_id=configuration.model_id,
                    headers={"Authorization": f"Bearer {credential}"},
                    json={
                        "model": configuration.model_id,
                        "input": {"messages": [{"role": "user", "content": "ping"}]},
                        "parameters": {"max_tokens": 1},
                    },
                )
    except httpx.TimeoutException:
        return ProviderTestResult(
            False,
            "El proveedor excedió el tiempo máximo después de los reintentos seguros.",
        )
    except httpx.HTTPError:
        return ProviderTestResult(False, "No fue posible conectar con el proveedor configurado.")
    if 200 <= response.status_code < 300:
        if configuration.provider_kind == "groq-cloud":
            choices = response.json().get("choices", [])
            content = choices[0].get("message", {}).get("content") if choices else None
            try:
                connection_document = _json_object(content)
            except ProviderGenerationError:
                return ProviderTestResult(
                    False,
                    "Groq respondió, pero no produjo el JSON estructurado de comprobación.",
                )
            if connection_document.get("ok") is not True:
                return ProviderTestResult(
                    False,
                    "Groq respondió con un JSON que no confirma la comprobación solicitada.",
                )
        return ProviderTestResult(
            True, "Conexión con el proveedor validada sin enviar datos del negocio."
        )
    return ProviderTestResult(False, str(_response_error(configuration.provider_kind, response)))
