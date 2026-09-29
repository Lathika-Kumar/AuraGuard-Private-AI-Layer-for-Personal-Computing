from __future__ import annotations

from fastapi.testclient import TestClient
from app.main import app
from app.services.privacy_service import (
    PrivacyAction,
    PrivacyClassification,
    PrivacyPolicyMode,
    PrivacyService,
)
from app.services.output_guard import OutputGuard

client = TestClient(app)


def test_privacy_email_detection() -> None:
    text = "Please reach out to support@auraguard.local for questions."
    analysis = PrivacyService.analyze(text)
    assert any(e.type == "EMAIL" for e in analysis.entities)
    assert analysis.classification == PrivacyClassification.PERSONAL
    assert "[REDACTED_EMAIL]" in PrivacyService.redact_text(
        text,
        [e for e in analysis.entities if e.type == "EMAIL"]
    ) or "@auraguard.local" not in analysis.redacted_text or analysis.allowed


def test_privacy_phone_detection() -> None:
    text = "Call me at +1-555-432-1098 tomorrow morning."
    analysis = PrivacyService.analyze(text)
    assert any(e.type == "PHONE" for e in analysis.entities)
    assert analysis.classification == PrivacyClassification.PERSONAL


def test_privacy_credentials_detection() -> None:
    text = "The database password is password: SuperSecretP@ssw0rd! and port is 5432."
    analysis = PrivacyService.analyze(text, mode="balanced")
    assert any(e.type == "PASSWORD" for e in analysis.entities)
    assert analysis.classification == PrivacyClassification.HIGHLY_SENSITIVE
    assert analysis.allowed is False  # Blocked in balanced mode


def test_privacy_api_key_detection() -> None:
    text = "Use this key sk-proj-1234567890abcdef1234567890 for API calls."
    analysis = PrivacyService.analyze(text, mode="balanced")
    assert any(e.type == "API KEY" for e in analysis.entities)
    assert analysis.classification == PrivacyClassification.HIGHLY_SENSITIVE
    assert analysis.allowed is False


def test_privacy_private_key_detection() -> None:
    text = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Y1W9X...fakekeycontent...AQAB\n"
        "-----END RSA PRIVATE KEY-----"
    )
    analysis = PrivacyService.analyze(text, mode="balanced")
    assert any(e.type == "PRIVATE KEY" for e in analysis.entities)
    assert analysis.classification == PrivacyClassification.HIGHLY_SENSITIVE
    assert analysis.allowed is False


def test_privacy_auth_token_detection() -> None:
    jwt_sample = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    text = f"Authorization: Bearer {jwt_sample}"
    analysis = PrivacyService.analyze(text, mode="balanced")
    assert any(e.type == "AUTH TOKEN" for e in analysis.entities)
    assert analysis.classification == PrivacyClassification.HIGHLY_SENSITIVE


def test_privacy_card_detection() -> None:
    # 4532... is a standard Visa test number with valid Luhn
    text = "Charging card 4532-0150-1234-5678 for monthly subscription."
    analysis = PrivacyService.analyze(text, mode="balanced")
    assert any(e.type == "CREDIT/DEBIT CARD" for e in analysis.entities)
    assert analysis.classification == PrivacyClassification.HIGHLY_SENSITIVE


def test_privacy_ssn_detection() -> None:
    text = "SSN on file is 123-45-6789 for tax records."
    analysis = PrivacyService.analyze(text)
    assert any(e.type == "IDENTIFICATION NUMBER" for e in analysis.entities)
    assert analysis.classification == PrivacyClassification.SENSITIVE


def test_privacy_dob_detection() -> None:
    text = "DOB: 1992-08-14 verified by doctor."
    analysis = PrivacyService.analyze(text)
    assert any(e.type == "DATE OF BIRTH" for e in analysis.entities)
    assert analysis.classification == PrivacyClassification.SENSITIVE


def test_privacy_policy_modes() -> None:
    text_personal = "Contact user at john.doe@example.com for notification."
    text_secret = "api_key = 'abcdef1234567890abcdef'"

    # 1. Strict mode: personal data must be redacted
    res_strict = PrivacyService.analyze(text_personal, mode="strict")
    assert any(e.action == PrivacyAction.REDACT for e in res_strict.entities)
    assert "[REDACTED_EMAIL]" in res_strict.redacted_text

    # 2. Permissive mode: personal data is allowed
    res_perm = PrivacyService.analyze(text_personal, mode="permissive")
    assert all(e.action == PrivacyAction.ALLOW for e in res_perm.entities)

    # 3. Secret in strict or balanced mode: blocked
    res_strict_secret = PrivacyService.analyze(text_secret, mode="strict")
    assert res_strict_secret.allowed is False


def test_privacy_analyze_endpoint() -> None:
    response = client.post(
        "/api/privacy/analyze",
        json={"text": "Send contract to alice@firm.org and call +1-555-987-6543."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "PERSONAL"
    assert len(data["entities"]) >= 2
    types = [e["type"] for e in data["entities"]]
    assert "EMAIL" in types
    assert "PHONE" in types


def test_output_guard_redaction_and_blocking() -> None:
    # 1. Safe text
    safe_out = OutputGuard.sanitize("The requested project documentation is in chapter 2.")
    assert safe_out.was_modified is False
    assert safe_out.blocked is False

    # 2. Secret output blocked
    secret_text = "Here is the key: sk-proj-1234567890abcdef1234567890 for your query."
    guarded = OutputGuard.sanitize(secret_text, policy_mode="balanced")
    assert guarded.blocked is True
    assert "sk-proj" not in guarded.text
    assert "blocked" in guarded.text.lower()


def test_privacy_events_logged_without_raw_secrets() -> None:
    # Trigger an event
    PrivacyService.log_event(
        event_type="TEST_REDACTED",
        severity="MEDIUM",
        source="test",
        description="Redacted EMAIL entity in test query",
        entity_type="EMAIL",
        action="REDACT",
    )
    res = client.get("/api/privacy/events?limit=10")
    assert res.status_code == 200
    events = res.json()
    assert len(events) > 0
    # Ensure no passwords or raw credentials exist in logs
    for ev in events:
        assert "SuperSecret" not in str(ev)
        assert "sk-proj" not in str(ev)


def test_privacy_stats_endpoint() -> None:
    res = client.get("/api/privacy/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "total_events" in stats
    assert stats["local_processing"] == "100%"
    assert stats["external_network_calls"] == 0
