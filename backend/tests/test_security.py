from __future__ import annotations

import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_security_path_traversal_prevention() -> None:
    # Attempting to upload or access files outside data dir
    res = client.post(
        "/api/documents/upload",
        files={"file": ("../../../../etc/passwd.pdf", b"%PDF-1.4\n%EOF", "application/pdf")},
    )
    # The endpoint strips path components or validates PDF
    if res.status_code == 200:
        doc = res.json()
        assert ".." not in doc["filename"]
        # Clean up
        client.delete(f"/api/documents/{doc['id']}")


def test_security_memory_poisoning_credentials_blocked() -> None:
    # Adversary tries to insert private key or password into ReMind context
    malicious_inputs = [
        "DB_PASS=password: rootAdminSecretKey99!",
        "sk-proj-99999999999999999999999999999999",
        "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----",
    ]
    for m in malicious_inputs:
        res = client.post(
            "/api/memories",
            json={"content": m, "type": "FACT"},
        )
        assert res.status_code == 400
        assert "sensitive data" in res.json()["detail"].lower()


def test_security_document_deletion_guarantee() -> None:
    # Upload document
    pdf_bytes = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 58 >> stream
BT
/F1 12 Tf
100 700 Td
(UniqueSecretProjectCodenameOmega99) Tj
ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000353 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
432
%%EOF"""
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("secret_omega.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["id"]

    # Verify query retrieves it
    found_res = client.post(
        "/api/search",
        json={"query": "What is the UniqueSecretProjectCodenameOmega99?"},
    )
    assert found_res.status_code == 200
    assert "Omega99" in found_res.json()["answer"]

    # Delete document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200

    # Verify query NO LONGER retrieves it
    after_res = client.post(
        "/api/search",
        json={"query": "What is the UniqueSecretProjectCodenameOmega99?"},
    )
    assert after_res.status_code == 200
    assert "couldn't find enough relevant information" in after_res.json()["answer"] or "No local documents" in after_res.json()["answer"]
