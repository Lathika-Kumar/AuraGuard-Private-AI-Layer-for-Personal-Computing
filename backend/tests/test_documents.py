from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_documents_list_empty() -> None:
    response = client.get('/api/documents')
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_returns_no_relevant_info() -> None:
    response = client.post('/api/search', json={'query': 'What is the plan?'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['answer'] == "I couldn't find enough relevant information in your local documents."
    assert payload['sources'] == []


def test_upload_rejects_non_pdf() -> None:
    response = client.post(
        '/api/documents/upload',
        files={'file': ('notes.txt', b'plain text', 'text/plain')},
    )
    assert response.status_code == 400
    assert 'Only PDF files are supported' in response.json()['detail']
