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


def _anthropic_system_instruction(
    system_instruction: str,
    response_schema: dict[str, Any] | None,
) -> str:
    """Ask Claude for bounded JSON while keeping schema enforcement local and auditable."""
    contract = "Responde exclusivamente con un objeto JSON válido, sin Markdown ni texto adicional."
    if response_schema is not None:
        contract += (
            " El objeto debe cumplir exactamente este esquema JSON: "
            f"{json.dumps(response_schema, ensure_ascii=False, separators=(',', ':'))}"
        )
    return f"{system_instruction.strip()}\n\n{contract}"


def _anthropic_text(payload: object) -> str | None:
    if not isinstance(payload, dict) or not isinstance(payload.get("content"), list):
        return None
    blocks = payload["content"]
    text_blocks = [
        str(block.get("text", ""))
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "text" and block.get("text")
    ]
    return "".join(text_blocks) or None


def _json_contract_error(value: object, schema: dict[str, Any], path: str = "$") -> str | None:
    """Validate the JSON Schema subset used by every provider adapter.

    Provider-side structured output is useful transport assistance, but the
    application remains the authority.  Keeping this validator provider-neutral
    lets an adapter fall back to plain JSON without weakening the BI contract.
    """
    expected = schema.get("type")
    valid_type = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, int | float) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(str(expected), True)
    if expected is not None and not valid_type:
        return f"{path}: tipo incompatible; se esperaba {expected}."
    if "enum" in schema and value not in schema["enum"]:
        return f"{path}: valor fuera del catálogo permitido."
    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            return f"{path}: texto más corto que el mínimo permitido."
        if "maxLength" in schema and len(value) > int(schema["maxLength"]):
            return f"{path}: texto más largo que el máximo permitido."
    if isinstance(value, int | float) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            return f"{path}: número menor que el mínimo permitido."
        if "maximum" in schema and value > schema["maximum"]:
            return f"{path}: número mayor que el máximo permitido."
    if isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)):
            return f"{path}: lista más corta que el mínimo permitido."
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            return f"{path}: lista más larga que el máximo permitido."
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                error = _json_contract_error(item, item_schema, f"{path}[{index}]")
                if error:
                    return error
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        for required in schema.get("required", []):
            if required not in value:
                return f"{path}: falta una propiedad obligatoria."
        if schema.get("additionalProperties") is False:
            extras = set(value) - set(properties)
            if extras:
                return f"{path}: contiene propiedades no permitidas."
        for key, child in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                error = _json_contract_error(child, child_schema, f"{path}.{key}")
                if error:
                    return error
    return None


def _validated_json_object(content: object, schema: dict[str, Any] | None) -> dict[str, Any]:
    document = _json_object(content)
    if schema is not None:
        error = _json_contract_error(document, schema)
        if error:
            raise ProviderGenerationError(
                "El proveedor devolvió JSON, pero no cumplió el contrato estructurado "
                "validado por la plataforma. La respuesta fue descartada sin usarse.",
                category="structured_contract",
            )
    return document


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
            # Respect the provider's refill window. The previous ten-second cap made
            # Groq retry too early even when it explicitly requested 24 seconds.
            return min(max(retry_after, 0.0), 45.0)
        except (TypeError, ValueError):
            pass
    return float(min(0.25 * (2 ** (attempt - 1)), 2.0))


def _is_transient_response(response: Any) -> bool:
    status_code = int(getattr(response, "status_code", 0))
    if status_code in _TRANSIENT_STATUS_CODES:
        return True
    details = _provider_error_details(response)
    normalized = f"{details.code} {details.message}".casefold()
    if status_code == 400 and details.code == "json_validate_failed":
        # A model can miss a valid structured contract nondeterministically. Retrying
        # is safe because the request is read-only and all results are validated again
        # by the application before they can become a BI proposal.
        return True
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
    if provider_kind == "anthropic-cloud" and status_code == 401:
        return error(
            "La API key de Anthropic no es válida o fue revocada.",
            "authentication",
        )
    if provider_kind == "anthropic-cloud" and status_code == 403:
        return error(
            "La cuenta de Anthropic no tiene acceso al modelo o a esta operación.",
            "authorization",
        )
    if provider_kind == "anthropic-cloud" and status_code == 404:
        return error(
            "El modelo Claude configurado no está disponible para esta cuenta.",
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
            if any(
                marker in normalized
                for marker in (
                    "does not match the expected schema",
                    "does not validate",
                    "jsonschema",
                    "maxitems",
                    "minitems",
                )
            ):
                return error(
                    "Groq no cumplió el contrato estructurado después de los reintentos y "
                    "la recuperación JSON seguros. La plataforma descartó la respuesta sin "
                    "usarla; la necesidad y su viabilidad continúan válidas para reintentar.",
                    "structured_contract",
                )
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
                request_json = {
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
                }
                response = await _post_with_retry(
                    client,
                    f"{base_url}/chat/completions",
                    provider_kind=configuration.provider_kind,
                    model_id=configuration.model_id,
                    headers={"Authorization": f"Bearer {credential}"},
                    json=request_json,
                )
                details = _provider_error_details(response)
                if (
                    response_schema is not None
                    and response.status_code == 400
                    and details.code == "json_validate_failed"
                ):
                    # Groq can reject an otherwise valid request when one sampled
                    # generation misses strict schema enforcement.  After the bounded
                    # strict retries, request JSON once and enforce the identical
                    # contract locally.  No business rule or scope is relaxed.
                    fallback_instruction = _anthropic_system_instruction(
                        system_instruction,
                        response_schema,
                    )
                    fallback_json = {
                        **request_json,
                        "messages": [
                            {"role": "system", "content": fallback_instruction},
                            {"role": "user", "content": user_content},
                        ],
                        "response_format": {"type": "json_object"},
                    }
                    response = await _post_with_retry(
                        client,
                        f"{base_url}/chat/completions",
                        provider_kind=configuration.provider_kind,
                        model_id=configuration.model_id,
                        max_attempts=1,
                        headers={"Authorization": f"Bearer {credential}"},
                        json=fallback_json,
                    )
                if not 200 <= response.status_code < 300:
                    raise _response_error(configuration.provider_kind, response)
                choices = response.json().get("choices", [])
                content = choices[0].get("message", {}).get("content") if choices else None
            elif configuration.provider_kind == "anthropic-cloud":
                response = await _post_with_retry(
                    client,
                    f"{base_url}/v1/messages",
                    provider_kind=configuration.provider_kind,
                    model_id=configuration.model_id,
                    headers={
                        "x-api-key": credential,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": configuration.model_id,
                        "max_tokens": max_output_tokens,
                        "temperature": 0,
                        "system": _anthropic_system_instruction(
                            system_instruction,
                            response_schema,
                        ),
                        "messages": [{"role": "user", "content": user_content}],
                    },
                )
                if not 200 <= response.status_code < 300:
                    raise _response_error(configuration.provider_kind, response)
                content = _anthropic_text(response.json())
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
    return _validated_json_object(content, response_schema)


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
            elif configuration.provider_kind == "anthropic-cloud":
                response = await _post_with_retry(
                    client,
                    f"{base_url}/v1/messages",
                    provider_kind=configuration.provider_kind,
                    model_id=configuration.model_id,
                    headers={
                        "x-api-key": credential,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": configuration.model_id,
                        "max_tokens": 32,
                        "temperature": 0,
                        "system": "Responde únicamente con un objeto JSON válido.",
                        "messages": [{"role": "user", "content": 'Devuelve {"ok":true}.'}],
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
        if configuration.provider_kind in {"groq-cloud", "anthropic-cloud"}:
            if configuration.provider_kind == "groq-cloud":
                choices = response.json().get("choices", [])
                content = choices[0].get("message", {}).get("content") if choices else None
                provider_name = "Groq"
            else:
                content = _anthropic_text(response.json())
                provider_name = "Anthropic"
            try:
                connection_document = _json_object(content)
            except ProviderGenerationError:
                return ProviderTestResult(
                    False,
                    (
                        f"{provider_name} respondió, pero no produjo el JSON estructurado "
                        "de comprobación."
                    ),
                )
            if connection_document.get("ok") is not True:
                return ProviderTestResult(
                    False,
                    (
                        f"{provider_name} respondió con un JSON que no confirma la "
                        "comprobación solicitada."
                    ),
                )
        return ProviderTestResult(
            True, "Conexión con el proveedor validada sin enviar datos del negocio."
        )
    return ProviderTestResult(False, str(_response_error(configuration.provider_kind, response)))
