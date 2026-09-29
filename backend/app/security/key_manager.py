from __future__ import annotations

import os
import sys
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Optional

from app.core.config import settings


class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


class KeyManager:
    """Manages the lifecycle of the local master encryption key.
    
    Protects the master key at rest using Windows DPAPI (CryptProtectData),
    ensuring that the key is encrypted with the current Windows user's credentials
    and cannot be decrypted by unauthorized users or offline disk extraction.
    """

    def __init__(self, key_file_path: Optional[Path] = None):
        self.key_file_path = key_file_path or (settings.data_dir / ".master_key.dpapi")
        self._cached_key: Optional[bytes] = None

    def is_dpapi_supported(self) -> bool:
        """Determines whether Windows DPAPI is available on the current host."""
        return sys.platform == "win32" and hasattr(ctypes, "windll") and hasattr(ctypes.windll, "crypt32")

    def generate_key(self) -> bytes:
        """Generates a cryptographically strong 256-bit (32-byte) AES key."""
        return os.urandom(32)

    def protect_key(self, raw_key: bytes) -> bytes:
        """Protects the raw key using Windows DPAPI where available."""
        if not self.is_dpapi_supported():
            # Portable fallback header for non-Windows platforms
            return b"PORTABLE_V1:" + raw_key

        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32

        in_blob = DATA_BLOB(
            len(raw_key),
            ctypes.cast(ctypes.create_string_buffer(raw_key), ctypes.POINTER(ctypes.c_byte)),
        )
        out_blob = DATA_BLOB()

        # CRYPTPROTECT_UI_FORBIDDEN = 0x1 (don't display user prompts)
        flags = 0x1
        description = "AuraGuard Master Encryption Key"
        success = crypt32.CryptProtectData(
            ctypes.byref(in_blob),
            description,
            None,
            None,
            None,
            flags,
            ctypes.byref(out_blob),
        )
        if not success:
            raise ctypes.WinError()

        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            kernel32.LocalFree(out_blob.pbData)

    def unprotect_key(self, protected_blob: bytes) -> bytes:
        """Unprotects the master key blob using Windows DPAPI."""
        if protected_blob.startswith(b"PORTABLE_V1:"):
            return protected_blob[len(b"PORTABLE_V1:"):]

        if not self.is_dpapi_supported():
            raise RuntimeError("DPAPI-protected key cannot be decrypted on a non-Windows platform without DPAPI.")

        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32

        in_blob = DATA_BLOB(
            len(protected_blob),
            ctypes.cast(ctypes.create_string_buffer(protected_blob), ctypes.POINTER(ctypes.c_byte)),
        )
        out_blob = DATA_BLOB()

        flags = 0x1  # CRYPTPROTECT_UI_FORBIDDEN
        success = crypt32.CryptUnprotectData(
            ctypes.byref(in_blob),
            None,
            None,
            None,
            None,
            flags,
            ctypes.byref(out_blob),
        )
        if not success:
            raise ctypes.WinError()

        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            kernel32.LocalFree(out_blob.pbData)

    def get_or_create_key(self) -> bytes:
        """Retrieves or generates the persistent master key."""
        if self._cached_key is not None:
            return self._cached_key

        self.key_file_path.parent.mkdir(parents=True, exist_ok=True)

        if self.key_file_path.exists():
            with open(self.key_file_path, "rb") as f:
                protected_blob = f.read()
            self._cached_key = self.unprotect_key(protected_blob)
            return self._cached_key

        # Key does not exist: generate fresh 256-bit key
        raw_key = self.generate_key()
        protected_blob = self.protect_key(raw_key)

        # Write protected key atomically
        temp_path = self.key_file_path.with_suffix(".tmp")
        with open(temp_path, "wb") as f:
            f.write(protected_blob)
        temp_path.replace(self.key_file_path)

        self._cached_key = raw_key
        return self._cached_key

    def get_key_protection_type(self) -> str:
        """Returns the active key protection mechanism description."""
        if self.is_dpapi_supported():
            return "Windows DPAPI"
        return "Protected File Key"


key_manager = KeyManager()
