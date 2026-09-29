import base64
import os
import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security.encryption_service import (
    EncryptionService,
    DecryptionError,
    encryption_service,
)
from app.security.key_manager import KeyManager
from app.database.migration import migrate_to_encrypted_storage
from app.database.database import get_db_connection

client = TestClient(app)


def test_encryption_decryption_roundtrip():
    secret = "Confidential client notes: Patient allergy to Penicillin, BP 130/85."
    encrypted = encryption_service.encrypt(secret)
    assert encrypted.startswith("AG1$")
    assert secret not in encrypted
    decrypted = encryption_service.decrypt(encrypted)
    assert decrypted == secret


def test_tampered_ciphertext_fails_safely():
    secret = "Top secret financial portfolio: 50,000 USD in Treasury Bonds."
    encrypted = encryption_service.encrypt(secret)
    parts = encrypted.split("$")
    nonce_b64, ct_b64 = parts[1], parts[2]
    raw_ct = bytearray(base64.b64decode(ct_b64))

    # Flip one bit in the middle of ciphertext
    raw_ct[8] ^= 0x01
    tampered_ct = f"AG1${nonce_b64}${base64.b64encode(raw_ct).decode()}"

    with pytest.raises(DecryptionError):
        encryption_service.decrypt(tampered_ct)


def test_tampered_nonce_fails_safely():
    secret = "Employee SSN: 000-12-3456"
    encrypted = encryption_service.encrypt(secret)
    parts = encrypted.split("$")
    nonce_b64, ct_b64 = parts[1], parts[2]
    raw_nonce = bytearray(base64.b64decode(nonce_b64))

    # Flip one bit in nonce
    raw_nonce[0] ^= 0xFF
    tampered_nonce_ct = f"AG1${base64.b64encode(raw_nonce).decode()}${ct_b64}"

    with pytest.raises(DecryptionError):
        encryption_service.decrypt(tampered_nonce_ct)


def test_wrong_key_fails_safely(tmp_path):
    # Create an independent key manager with a different generated key
    alt_km = KeyManager(key_file_path=tmp_path / "alt_key.dpapi")
    alt_service = EncryptionService(custom_key_manager=alt_km)

    secret = "Cryptographic isolation test payload."
    encrypted = encryption_service.encrypt(secret)

    with pytest.raises(DecryptionError):
        alt_service.decrypt(encrypted)


def test_binary_envelope_encryption_roundtrip():
    binary_data = os.urandom(1024)
    encrypted_blob = encryption_service.encrypt_bytes(binary_data)
    assert encrypted_blob.startswith(b"AG_SEC1\x00")
    assert binary_data != encrypted_blob

    decrypted_blob = encryption_service.decrypt_bytes(encrypted_blob)
    assert decrypted_blob == binary_data


def test_binary_tampered_envelope_fails_safely():
    binary_data = b"FAISS_VECTOR_BLOB_RAW_FLOAT32_ARRAY"
    encrypted_blob = bytearray(encryption_service.encrypt_bytes(binary_data))

    # Tamper with payload byte
    encrypted_blob[-5] ^= 0xAB

    with pytest.raises(DecryptionError):
        encryption_service.decrypt_bytes(bytes(encrypted_blob))


def test_dpapi_key_protection_roundtrip():
    km = KeyManager()
    raw_key = os.urandom(32)
    protected = km.protect_key(raw_key)
    assert protected != raw_key
    recovered = km.unprotect_key(protected)
    assert recovered == raw_key


def test_memory_encryption_at_rest():
    from app.services.remind_service import RemindService
    remind = RemindService()

    secret_content = "Private passport number: X78901234, expires 2030."
    mem = remind.create_memory(
        content=secret_content,
        memory_type="NOTE",
        user_confirmed=True,
    )
    assert mem is not None
    assert mem["content"] == secret_content

    # Inspect raw SQLite database directly
    with get_db_connection() as conn:
        row = conn.execute("SELECT content FROM memories WHERE id = ?", (mem["id"],)).fetchone()
        raw_db_content = row["content"]
        assert raw_db_content.startswith("AG1$")
        assert secret_content not in raw_db_content

    # Cleanup
    remind.delete_memory(mem["id"])


def test_migration_idempotent_and_lossless(tmp_path):
    test_db = tmp_path / "migration_test.db"
    with sqlite3.connect(test_db) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE document_chunks (id INTEGER PRIMARY KEY, text TEXT)")
        conn.execute("CREATE TABLE memories (id INTEGER PRIMARY KEY, content TEXT)")
        conn.execute("INSERT INTO document_chunks (id, text) VALUES (1, 'Plaintext chunk A')")
        conn.execute("INSERT INTO memories (id, content) VALUES (1, 'Plaintext memory B')")
        conn.commit()

        # Run migration
        res1 = migrate_to_encrypted_storage(conn)
        assert res1["chunks_migrated"] == 1
        assert res1["memories_migrated"] == 1
        assert res1["already_encrypted"] is False

        # Verify content in DB is now encrypted
        c_row = conn.execute("SELECT text FROM document_chunks WHERE id = 1").fetchone()
        m_row = conn.execute("SELECT content FROM memories WHERE id = 1").fetchone()
        assert c_row["text"].startswith("AG1$")
        assert m_row["content"].startswith("AG1$")
        assert encryption_service.decrypt(c_row["text"]) == "Plaintext chunk A"
        assert encryption_service.decrypt(m_row["content"]) == "Plaintext memory B"

        # Run migration second time (idempotency check)
        res2 = migrate_to_encrypted_storage(conn)
        assert res2["chunks_migrated"] == 0
        assert res2["memories_migrated"] == 0
        assert res2["already_encrypted"] is True


def test_security_endpoint():
    res = client.get("/api/system/security")
    assert res.status_code == 200
    data = res.json()
    assert data["storage_encryption"] is True
    assert data["algorithm"] == "AES-256-GCM"
    assert data["key_length_bits"] == 256
    assert data["database_encrypted"] is True
    assert data["memory_encrypted"] is True
    assert data["documents_encrypted"] is True
    assert data["local_only"] is True
    assert data["cloud_leakage"] is False
    # Ensure no sensitive keys or paths are returned
    assert "key" not in data
    assert "secret" not in data
    assert "master_key" not in data
