from __future__ import annotations

import fcntl
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class SecretDecryptionError(ValueError):
    """Raised without exposing ciphertext details when stored data cannot be decrypted."""


class SecretCipher:
    def __init__(self, key_path: str | Path) -> None:
        self.key_path = Path(key_path)

    def _load_or_create_key(self) -> bytes:
        self.key_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        lock_descriptor = os.open(f"{self.key_path}.lock", os.O_RDWR | os.O_CREAT, 0o600)
        with os.fdopen(lock_descriptor, "rb+") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            if self.key_path.exists():
                return self.key_path.read_bytes().strip()

            key = Fernet.generate_key()
            temporary_path = self.key_path.with_suffix(f".tmp-{os.getpid()}")
            temporary_descriptor = os.open(
                temporary_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            with os.fdopen(temporary_descriptor, "wb") as key_file:
                key_file.write(key)
                key_file.flush()
                os.fsync(key_file.fileno())
            os.replace(temporary_path, self.key_path)
            return key

    def ensure_ready(self) -> None:
        Fernet(self._load_or_create_key())

    def encrypt(self, plaintext: str) -> str:
        return Fernet(self._load_or_create_key()).encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        try:
            return Fernet(self._load_or_create_key()).decrypt(ciphertext.encode()).decode()
        except (InvalidToken, ValueError) as exc:
            message = "No fue posible descifrar la credencial almacenada."
            raise SecretDecryptionError(message) from exc
