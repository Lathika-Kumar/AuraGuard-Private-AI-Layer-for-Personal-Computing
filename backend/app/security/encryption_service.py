from __future__ import annotations

import base64
import os
from typing import Optional, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from app.security.key_manager import KeyManager, key_manager


class DecryptionError(Exception):
    """Raised when ciphertext cannot be decrypted due to invalid key or tampered data."""
    pass


class EncryptionService:
    """Provides authenticated AES-256-GCM encryption and decryption for local storage."""

    ENCRYPTION_PREFIX = "AG1$"
    FILE_MAGIC = b"AG_SEC1\x00"

    def __init__(self, custom_key_manager: Optional[KeyManager] = None):
        self.km = custom_key_manager or key_manager
        self._key: Optional[bytes] = None
        self._aesgcm: Optional[AESGCM] = None

    def _get_cipher(self) -> AESGCM:
        if self._aesgcm is None:
            self._key = self.km.get_or_create_key()
            self._aesgcm = AESGCM(self._key)
        return self._aesgcm

    def is_encrypted(self, value: Union[str, bytes]) -> bool:
        """Checks if a string or byte payload is already in encrypted format."""
        if isinstance(value, str):
            return value.startswith(self.ENCRYPTION_PREFIX)
        if isinstance(value, (bytes, bytearray)):
            return value.startswith(self.FILE_MAGIC)
        return False

    def encrypt(self, plaintext: str) -> str:
        """Encrypts a plaintext string using AES-256-GCM.
        
        Format: AG1$<base64_nonce>$<base64_ciphertext_and_tag>
        """
        if not plaintext:
            return plaintext

        # If already encrypted, return as-is
        if self.is_encrypted(plaintext):
            return plaintext

        cipher = self._get_cipher()
        nonce = os.urandom(12)  # Standard 96-bit nonce for GCM
        data_bytes = plaintext.encode("utf-8")
        ct = cipher.encrypt(nonce, data_bytes, None)

        nonce_b64 = base64.b64encode(nonce).decode("ascii")
        ct_b64 = base64.b64encode(ct).decode("ascii")
        return f"{self.ENCRYPTION_PREFIX}{nonce_b64}${ct_b64}"

    def decrypt(self, ciphertext: str) -> str:
        """Decrypts an authenticated ciphertext string back to plaintext.
        
        Fails safely if ciphertext or authentication tag has been tampered with.
        """
        if not ciphertext or not self.is_encrypted(ciphertext):
            return ciphertext

        parts = ciphertext.split("$")
        if len(parts) != 3 or parts[0] != "AG1":
            raise DecryptionError("Malformed ciphertext format.")

        try:
            nonce = base64.b64decode(parts[1])
            ct = base64.b64decode(parts[2])
            cipher = self._get_cipher()
            pt_bytes = cipher.decrypt(nonce, ct, None)
            return pt_bytes.decode("utf-8")
        except InvalidTag:
            raise DecryptionError("Ciphertext integrity verification failed: tampered data or invalid tag.")
        except Exception as exc:
            raise DecryptionError(f"Decryption failed: {str(exc)}") from exc

    def encrypt_bytes(self, data: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """Encrypts a binary blob with authenticated envelope format."""
        if not data:
            return data
        if self.is_encrypted(data):
            return data

        cipher = self._get_cipher()
        nonce = os.urandom(12)
        ct = cipher.encrypt(nonce, data, associated_data)
        return self.FILE_MAGIC + nonce + ct

    def decrypt_bytes(self, payload: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """Decrypts a binary envelope back to raw bytes."""
        if not payload or not self.is_encrypted(payload):
            return payload

        magic_len = len(self.FILE_MAGIC)
        if len(payload) < magic_len + 12 + 16:
            raise DecryptionError("Payload too short for authenticated binary envelope.")

        nonce = payload[magic_len:magic_len + 12]
        ct = payload[magic_len + 12:]
        cipher = self._get_cipher()
        try:
            return cipher.decrypt(nonce, ct, associated_data)
        except InvalidTag:
            raise DecryptionError("Binary payload integrity check failed: tampered file or invalid tag.")
        except Exception as exc:
            raise DecryptionError(f"Binary decryption failed: {str(exc)}") from exc

    def get_security_metadata(self) -> dict:
        """Returns safe security configuration without exposing key material."""
        return {
            "storage_encryption": True,
            "algorithm": "AES-256-GCM",
            "key_length_bits": 256,
            "key_protection": self.km.get_key_protection_type(),
            "database_encrypted": True,
            "memory_encrypted": True,
            "documents_encrypted": True,
            "faiss_protection": "AES-256-GCM envelope at rest",
        }


encryption_service = EncryptionService()
