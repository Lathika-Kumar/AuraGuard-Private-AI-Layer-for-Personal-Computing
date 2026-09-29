from io import BytesIO
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Minimal valid PDF containing test text
TEST_PDF_BYTES = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 73 >> stream
BT
/F1 12 Tf
100 700 Td
(The AuraGuard grant amount is 50000 USD.) Tj
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
0000000368 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
447
%%EOF"""


def test_end_to_end_neural_rag() -> None:
    # 0. Clean up any existing fixture
    existing = client.get("/api/documents").json()
    for d in existing:
        if d.get("filename") == "grant_spec.pdf":
            client.delete(f"/api/documents/{d['id']}")

    # 1. Upload test PDF fixture
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("grant_spec.pdf", TEST_PDF_BYTES, "application/pdf")},
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    doc_id = upload_data["id"]
    assert upload_data["status"] == "processed"

    try:
        # 2. Query with matching semantic question
        search_res = client.post(
            "/api/search",
            json={"query": "What is the grant amount for AuraGuard?"},
        )
        assert search_res.status_code == 200
        search_data = search_res.json()

        assert "50000" in search_data["answer"]
        assert len(search_data["sources"]) > 0
        assert search_data["sources"][0]["document_id"] == doc_id
        assert search_data["sources"][0]["page_number"] == 1
        assert "grant_spec.pdf" in search_data["sources"][0]["filename"]

        # 3. Query with unrelated question (expect refusal)
        unrelated_res = client.post(
            "/api/search",
            json={"query": "What is the boiling point of liquid helium?"},
        )
        assert unrelated_res.status_code == 200
        unrelated_data = unrelated_res.json()
        assert "couldn't find enough relevant information" in unrelated_data["answer"]

    finally:
        # 4. Clean up test document
        del_res = client.delete(f"/api/documents/{doc_id}")
        assert del_res.status_code == 200
