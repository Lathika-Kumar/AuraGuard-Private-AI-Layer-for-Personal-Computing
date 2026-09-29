from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from app.services.privacy_service import (
    DetectedEntity,
    PrivacyAction,
    PrivacyClassification,
    PrivacyService,
)


@dataclass
class OutputGuardResult:
    text: str
    original_text: str
    was_modified: bool
    blocked: bool
    detected_entities: List[dict[str, Any]]
    latency_seconds: float


class OutputGuard:
    """AuraGuard Output Privacy Guard.
    
    Acts as the final barrier before any on-device AI answer is delivered to the user.
    Even if an LLM is prompted to regurgitate a credential or secret from context,
    the OutputGuard scans the final text, redacts sensitive entities, or completely blocks
    secrets from being exposed.
    """

    @classmethod
    def sanitize(
        cls,
        text: str,
        policy_mode: Optional[str] = None,
        source: str = "rag_answer",
    ) -> OutputGuardResult:
        t0 = time.time()
        analysis = PrivacyService.analyze(text, mode=policy_mode, stage="output")
        latency = time.time() - t0

        if not analysis.allowed:
            # Blocked output (e.g. LLM reproduced a private key, password, or auth token)
            blocked_types = [e.type for e in analysis.entities if e.action == PrivacyAction.BLOCK]
            for btype in set(blocked_types):
                PrivacyService.log_event(
                    event_type="OUTPUT_BLOCKED",
                    severity="CRITICAL",
                    source=source,
                    description=f"Generated output contained blocked {btype} and was shielded.",
                    entity_type=btype,
                    action="BLOCK",
                )
            sanitized = "[AuraGuard Privacy Guard: AI-generated response contained prohibited credentials or secrets and was blocked.]"
            return OutputGuardResult(
                text=sanitized,
                original_text=text,
                was_modified=True,
                blocked=True,
                detected_entities=[e.to_dict(mask_value=True) for e in analysis.entities],
                latency_seconds=round(latency, 4),
            )

        # Check if redaction was applied
        was_modified = analysis.redacted_text != text
        if was_modified:
            redacted_types = [e.type for e in analysis.entities if e.action == PrivacyAction.REDACT]
            for rtype in set(redacted_types):
                PrivacyService.log_event(
                    event_type="OUTPUT_REDACTED",
                    severity="MEDIUM",
                    source=source,
                    description=f"Output sanitized: redacted {rtype} entity.",
                    entity_type=rtype,
                    action="REDACT",
                )

        return OutputGuardResult(
            text=analysis.redacted_text,
            original_text=text,
            was_modified=was_modified,
            blocked=False,
            detected_entities=[e.to_dict(mask_value=True) for e in analysis.entities],
            latency_seconds=round(latency, 4),
        )
