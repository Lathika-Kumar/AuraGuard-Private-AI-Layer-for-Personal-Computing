from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get('/api/health')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['app'] == 'AuraGuard'


def test_root_endpoint() -> None:
    response = client.get('/')
    assert response.status_code == 200
    assert response.json()['message'] == 'AuraGuard backend is running locally.'
