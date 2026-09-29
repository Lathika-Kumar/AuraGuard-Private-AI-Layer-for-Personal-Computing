from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services.remind_service import RemindService

client = TestClient(app)


def test_remind_create_and_read_memory() -> None:
    payload = {
        "content": "AuraGuard uses local on-device neural embeddings.",
        "type": "FACT",
        "importance": 0.8,
        "confidence": 0.95,
        "source": "test_suite",
    }
    response = client.post("/api/memories", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["id"] > 0
    assert created["content"] == payload["content"]
    assert created["type"] == "FACT"
    assert created["status"] == "active"

    # Read back by ID
    get_res = client.get(f"/api/memories/{created['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["content"] == payload["content"]

    # Clean up
    del_res = client.delete(f"/api/memories/{created['id']}")
    assert del_res.status_code == 200


def test_remind_rejects_invalid_type() -> None:
    res = client.post(
        "/api/memories",
        json={"content": "Random memory", "type": "INVALID_TYPE_NAME"},
    )
    assert res.status_code == 400
    assert "Invalid memory type" in res.json()["detail"]


def test_remind_blocks_secrets_from_memory() -> None:
    # Attempting to store an API key or password in memory must be rejected by privacy engine
    secret_payload = {
        "content": "My secret API key is sk-proj-1234567890abcdef1234567890 for production.",
        "type": "NOTE",
    }
    res = client.post("/api/memories", json=secret_payload)
    assert res.status_code == 400
    assert "sensitive data" in res.json()["detail"].lower()


def test_remind_list_and_search_filters() -> None:
    # Create two test memories
    m1 = client.post(
        "/api/memories",
        json={"content": "User prefers concise answers with bullets.", "type": "PREFERENCE", "importance": 0.9},
    ).json()
    m2 = client.post(
        "/api/memories",
        json={"content": "Submit Snapdragon grant proposal before Friday.", "type": "TASK", "importance": 0.8},
    ).json()

    try:
        # Filter by type
        pref_list = client.get("/api/memories?type=PREFERENCE").json()
        assert any(m["id"] == m1["id"] for m in pref_list)
        assert not any(m["id"] == m2["id"] for m in pref_list)

        # Search by keyword
        task_search = client.get("/api/memories?search=Snapdragon").json()
        assert any(m["id"] == m2["id"] for m in task_search)

    finally:
        client.delete(f"/api/memories/{m1['id']}")
        client.delete(f"/api/memories/{m2['id']}")


def test_remind_update_and_archive() -> None:
    created = client.post(
        "/api/memories",
        json={"content": "Temporary note about benchmarking.", "type": "NOTE", "importance": 0.5},
    ).json()
    mem_id = created["id"]

    try:
        # Update content and importance
        patch_res = client.patch(
            f"/api/memories/{mem_id}",
            json={"content": "Updated note about CPU benchmarking.", "importance": 0.75},
        )
        assert patch_res.status_code == 200
        updated = patch_res.json()
        assert updated["content"] == "Updated note about CPU benchmarking."
        assert updated["importance"] == 0.75

        # Archive memory
        arch_res = client.post(f"/api/memories/{mem_id}/archive")
        assert arch_res.status_code == 200
        assert arch_res.json()["status"] == "archived"

    finally:
        client.delete(f"/api/memories/{mem_id}")


def test_remind_expiration_handling() -> None:
    # Create memory already expired
    past_iso = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    created = client.post(
        "/api/memories",
        json={"content": "Ephemeral security code reminder.", "type": "NOTE", "expires_at": past_iso},
    ).json()
    mem_id = created["id"]

    try:
        # Fetching should mark it expired
        get_res = client.get(f"/api/memories/{mem_id}").json()
        assert get_res["status"] == "expired"

        # List should exclude expired by default
        active_list = client.get("/api/memories").json()
        assert not any(m["id"] == mem_id for m in active_list)

    finally:
        client.delete(f"/api/memories/{mem_id}")


def test_remind_semantic_search_and_deletion_guarantee() -> None:
    # 1. Create a distinctive memory
    created = client.post(
        "/api/memories",
        json={"content": "The database port for AuraGuard SQLite WAL mode is internal only.", "type": "FACT", "importance": 0.9},
    ).json()
    mem_id = created["id"]

    try:
        # 2. Semantic search finds it
        search_res = client.post(
            "/api/memories/search",
            json={"query": "What is the database mode for AuraGuard?", "top_k": 3},
        )
        assert search_res.status_code == 200
        hits = search_res.json()["results"]
        assert len(hits) > 0
        assert any(h["id"] == mem_id for h in hits)

        # 3. Delete memory
        del_res = client.delete(f"/api/memories/{mem_id}")
        assert del_res.status_code == 200

        # 4. Deletion guarantee: verify semantic search can NEVER retrieve it again
        search_after = client.post(
            "/api/memories/search",
            json={"query": "What is the database mode for AuraGuard?", "top_k": 3},
        )
        assert search_after.status_code == 200
        hits_after = search_after.json()["results"]
        assert not any(h["id"] == mem_id for h in hits_after)

    finally:
        # Ensure cleanup if failed before delete
        client.delete(f"/api/memories/{mem_id}")
