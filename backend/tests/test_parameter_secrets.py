from __future__ import annotations

import stat

import pytest
from pydantic import ValidationError

from app.modules.parameters.schemas import LlmConfigurationCreate
from app.modules.parameters.secrets import SecretCipher, SecretDecryptionError


def test_secret_cipher_persists_key_and_never_stores_plaintext(tmp_path) -> None:
    key_path = tmp_path / "private" / "master.key"
    cipher = SecretCipher(key_path)

    ciphertext = cipher.encrypt("clave-super-secreta")

    assert "clave-super-secreta" not in ciphertext
    assert cipher.decrypt(ciphertext) == "clave-super-secreta"
    assert SecretCipher(key_path).decrypt(ciphertext) == "clave-super-secreta"
    assert stat.S_IMODE(key_path.stat().st_mode) == 0o600


def test_secret_cipher_rejects_tampered_ciphertext(tmp_path) -> None:
    cipher = SecretCipher(tmp_path / "master.key")
    ciphertext = cipher.encrypt("clave-super-secreta")

    with pytest.raises(SecretDecryptionError):
        cipher.decrypt(f"{ciphertext[:-2]}xx")


def test_llm_endpoint_validation_rejects_similar_untrusted_hostname() -> None:
    with pytest.raises(ValidationError):
        LlmConfigurationCreate(
            name="Proveedor no confiable",
            provider_kind="gemini",
            base_url="https://generativelanguage.googleapis.com.example.test",
            model_id="gemini-2.5-flash",
        )


def test_llm_reasoning_level_is_controlled_and_defaults_to_minimal() -> None:
    configuration = LlmConfigurationCreate(
        name="Gemini de prueba",
        provider_kind="gemini",
        base_url="https://generativelanguage.googleapis.com",
        model_id="gemini-3.6-flash",
    )

    assert configuration.reasoning_level == "minimal"
    with pytest.raises(ValidationError):
        LlmConfigurationCreate(
            name="Gemini de prueba",
            provider_kind="gemini",
            base_url="https://generativelanguage.googleapis.com",
            model_id="gemini-3.6-flash",
            reasoning_level="extremo",  # type: ignore[arg-type]
        )


def test_groq_endpoint_and_recommended_model_are_allowed() -> None:
    configuration = LlmConfigurationCreate(
        name="Groq para análisis BI",
        provider_kind="groq-cloud",
        base_url="https://api.groq.com/openai/v1",
        model_id="openai/gpt-oss-120b",
        reasoning_level="low",
    )

    assert configuration.provider_kind == "groq-cloud"
    with pytest.raises(ValidationError):
        LlmConfigurationCreate(
            name="Groq no confiable",
            provider_kind="groq-cloud",
            base_url="https://api.groq.com.example.test/openai/v1",
            model_id="openai/gpt-oss-120b",
        )
