import jwt

from app.core.config import settings
from app.modules.security.service import create_access_token, hash_password, verify_password


def test_password_is_hashed_and_verified() -> None:
    encoded = hash_password("ClaveDePruebaSegura2026")

    assert encoded != "ClaveDePruebaSegura2026"
    assert verify_password("ClaveDePruebaSegura2026", encoded)
    assert not verify_password("OtraClaveDePrueba2026", encoded)


def test_access_token_contains_subject() -> None:
    token = create_access_token(42)
    payload = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "42"
