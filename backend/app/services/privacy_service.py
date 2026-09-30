from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Tuple

from app.core.config import settings
from app.database.database import get_db_connection


class PrivacyClassification(str, Enum):
    PUBLIC = "PUBLIC"
    PERSONAL = "PERSONAL"
    SENSITIVE = "SENSITIVE"
    SECRET = "SECRET"
    HIGHLY_SENSITIVE = "HIGHLY_SENSITIVE"


class PrivacyAction(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    REDACT = "REDACT"
    BLOCK = "BLOCK"


class PrivacyPolicyMode(str, Enum):
    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"


@dataclass
class DetectedEntity:
    type: str
    text: str
    start: int
    end: int
    classification: PrivacyClassification
    action: PrivacyAction
    confidence: float = 1.0

    def to_dict(self, mask_value: bool = False) -> dict[str, Any]:
        val = "[PROTECTED]" if mask_value else self.text
        return {
            "type": self.type,
            "text": val,
            "start": self.start,
            "end": self.end,
            "classification": self.classification.value,
            "action": self.action.value,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class PrivacyAnalysisResult:
    classification: PrivacyClassification
    entities: List[DetectedEntity] = field(default_factory=list)
    allowed: bool = True
    policy_mode: str = "balanced"
    redacted_text: str = ""
    block_reason: Optional[str] = None

    def to_dict(self, mask_values: bool = False) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "entities": [e.to_dict(mask_value=mask_values) for e in self.entities],
            "allowed": self.allowed,
            "policy_mode": self.policy_mode,
            "redacted_text": self.redacted_text,
            "block_reason": self.block_reason,
        }


def _luhn_checksum_valid(number_str: str) -> bool:
    digits = [int(c) for c in number_str if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0


class PrivacyService:
    """AuraGuard Local Privacy Engine.
    
    Inspects text prior to and during AI processing to detect sensitive entities,
    assign privacy classifications, enforce configured privacy policies (strict, balanced, permissive),
    and safely redact or block unauthorized data leakage without calling any external cloud APIs.
    """

    # --- Regular Expression Patterns for Entity Detection ---

    # EMAIL
    _RE_EMAIL = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    # PHONE (International & National)
    _RE_PHONE = re.compile(
        r"(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\+?[1-9]\d{1,2}[-\s]?\d{4,5}[-\s]?\d{4,5}\b)"
    )

    # CREDIT/DEBIT CARD
    _RE_CARD = re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b"
    )

    # SSN / IDENTIFICATION NUMBER
    _RE_SSN = re.compile(
        r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"
    )
    _RE_ID_NUMBER = re.compile(
        r"\b(?:SSN|Passport|National\s*ID|Aadhaar|Govt\s*ID)[:\s#]+([A-Za-z0-9-]{6,16})\b",
        re.IGNORECASE,
    )

    # PRIVATE KEY
    _RE_PRIVATE_KEY = re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
    )

    # API KEYS & TOKENS
    _RE_API_KEY = re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z-_]{35}|(?:api[_-]?key|secret[_-]?key)[\s:=]+['\"]?([A-Za-z0-9_\-]{16,})['\"]?)\b",
        re.IGNORECASE,
    )

    # AUTH TOKENS (JWT & Bearer)
    _RE_JWT = re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    )
    _RE_BEARER = re.compile(
        r"\bBearer\s+([A-Za-z0-9._~+/-]{20,})\b",
        re.IGNORECASE,
    )

    # PASSWORDS
    _RE_PASSWORD = re.compile(
        r"\b(?:password|passwd|pwd)[\s:=]+['\"]?([^\s'\";,]{6,})['\"]?\b",
        re.IGNORECASE,
    )

    # BANK ACCOUNT & IBAN
    _RE_IBAN = re.compile(
        r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"
    )
    _RE_BANK_ACCOUNT = re.compile(
        r"\b(?:Account|Routing|Acc)[\s#:]+(\d{8,17})\b",
        re.IGNORECASE,
    )

    # DATE OF BIRTH
    _RE_DOB = re.compile(
        r"\b(?:DOB|Date of Birth|born on|Birth date)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|[A-Za-z]+ \d{1,2},? \d{4})\b",
        re.IGNORECASE,
    )

    # ADDRESS (Street patterns & PO Box)
    _RE_ADDRESS = re.compile(
        r"\b\d{1,5}\s+[A-Za-z0-9\s.,]{3,40}\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct|Circle|Cir)\b|\bP\.?O\.?\s+Box\s+\d+\b",
        re.IGNORECASE,
    )

    # PERSONAL NAME (Common honorifics or labeled names)
    _RE_NAME_LABELED = re.compile(
        r"\b(?:Name|Full Name|Patient|Client)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
    )
    _RE_NAME_HONORIFIC = re.compile(
        r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
    )

    @classmethod
    def get_policy_mode(cls, override_mode: Optional[str] = None) -> PrivacyPolicyMode:
        mode_str = (override_mode or getattr(settings, "privacy_mode", "balanced")).lower()
        if mode_str == "strict":
            return PrivacyPolicyMode.STRICT
        elif mode_str == "permissive":
            return PrivacyPolicyMode.PERMISSIVE
        return PrivacyPolicyMode.BALANCED

    @classmethod
    def _determine_action(
        cls,
        classification: PrivacyClassification,
        policy_mode: PrivacyPolicyMode,
        stage: str = "general",
    ) -> PrivacyAction:
        """Determines the appropriate PrivacyAction given the classification, policy mode, and processing stage.
        
        Stages:
        - "input": user query input
        - "context": retrieved chunks / memories to be sent to LLM
        - "output": LLM generated text before presentation
        - "memory_create": storing a new explicit user memory
        - "general": standalone analysis
        """
        if policy_mode == PrivacyPolicyMode.STRICT:
            if classification == PrivacyClassification.HIGHLY_SENSITIVE:
                return PrivacyAction.BLOCK
            elif classification == PrivacyClassification.SENSITIVE:
                return PrivacyAction.REDACT
            elif classification == PrivacyClassification.PERSONAL:
                return PrivacyAction.REDACT
            return PrivacyAction.ALLOW

        elif policy_mode == PrivacyPolicyMode.BALANCED:
            if classification == PrivacyClassification.HIGHLY_SENSITIVE:
                return PrivacyAction.BLOCK
            elif classification == PrivacyClassification.SENSITIVE:
                return PrivacyAction.REDACT
            elif classification == PrivacyClassification.PERSONAL:
                if stage in ("context", "output"):
                    return PrivacyAction.REDACT
                elif stage == "input":
                    return PrivacyAction.WARN
                elif stage == "memory_create":
                    return PrivacyAction.ALLOW
                return PrivacyAction.WARN
            return PrivacyAction.ALLOW

        else:  # PERMISSIVE
            if classification == PrivacyClassification.HIGHLY_SENSITIVE:
                return PrivacyAction.REDACT if stage in ("context", "output") else PrivacyAction.WARN
            elif classification == PrivacyClassification.SENSITIVE:
                return PrivacyAction.WARN
            elif classification == PrivacyClassification.PERSONAL:
                return PrivacyAction.ALLOW
            return PrivacyAction.ALLOW

    @classmethod
    def detect_entities(
        cls,
        text: str,
        policy_mode: PrivacyPolicyMode = PrivacyPolicyMode.BALANCED,
        stage: str = "general",
    ) -> List[DetectedEntity]:
        """Scans the text for all known sensitive entity categories."""
        if not text:
            return []

        entities: List[DetectedEntity] = []

        def add_entity(
            etype: str,
            match_text: str,
            start: int,
            end: int,
            classification: PrivacyClassification,
            confidence: float = 1.0,
        ):
            action = cls._determine_action(classification, policy_mode, stage)
            entities.append(
                DetectedEntity(
                    type=etype,
                    text=match_text,
                    start=start,
                    end=end,
                    classification=classification,
                    action=action,
                    confidence=confidence,
                )
            )

        # 1. PRIVATE KEY (Highest sensitivity)
        for m in cls._RE_PRIVATE_KEY.finditer(text):
            add_entity("PRIVATE KEY", m.group(0), m.start(), m.end(), PrivacyClassification.HIGHLY_SENSITIVE, 1.0)

        # 2. PASSWORDS
        for m in cls._RE_PASSWORD.finditer(text):
            add_entity("PASSWORD", m.group(0), m.start(), m.end(), PrivacyClassification.HIGHLY_SENSITIVE, 0.95)

        # 3. AUTH TOKENS (JWT & Bearer)
        for m in cls._RE_JWT.finditer(text):
            add_entity("AUTH TOKEN", m.group(0), m.start(), m.end(), PrivacyClassification.HIGHLY_SENSITIVE, 0.98)
        for m in cls._RE_BEARER.finditer(text):
            add_entity("AUTH TOKEN", m.group(0), m.start(), m.end(), PrivacyClassification.HIGHLY_SENSITIVE, 0.95)

        # 4. API KEYS
        for m in cls._RE_API_KEY.finditer(text):
            add_entity("API KEY", m.group(0), m.start(), m.end(), PrivacyClassification.HIGHLY_SENSITIVE, 0.96)

        # 5. CREDIT/DEBIT CARD
        for m in cls._RE_CARD.finditer(text):
            raw = m.group(0)
            cleaned = re.sub(r"[-\s]", "", raw)
            is_valid_luhn = _luhn_checksum_valid(cleaned)
            conf = 0.98 if is_valid_luhn else 0.70
            add_entity("CREDIT/DEBIT CARD", raw, m.start(), m.end(), PrivacyClassification.HIGHLY_SENSITIVE, conf)

        # 6. BANK ACCOUNT & IBAN
        for m in cls._RE_IBAN.finditer(text):
            add_entity("BANK ACCOUNT", m.group(0), m.start(), m.end(), PrivacyClassification.HIGHLY_SENSITIVE, 0.92)
        for m in cls._RE_BANK_ACCOUNT.finditer(text):
            add_entity("BANK ACCOUNT", m.group(0), m.start(), m.end(), PrivacyClassification.HIGHLY_SENSITIVE, 0.90)

        # 7. IDENTIFICATION NUMBER & SSN
        for m in cls._RE_SSN.finditer(text):
            add_entity("IDENTIFICATION NUMBER", m.group(0), m.start(), m.end(), PrivacyClassification.SENSITIVE, 0.95)
        for m in cls._RE_ID_NUMBER.finditer(text):
            add_entity("IDENTIFICATION NUMBER", m.group(0), m.start(), m.end(), PrivacyClassification.SENSITIVE, 0.90)

        # 8. DATE OF BIRTH
        for m in cls._RE_DOB.finditer(text):
            add_entity("DATE OF BIRTH", m.group(0), m.start(), m.end(), PrivacyClassification.SENSITIVE, 0.90)

        # 9. ADDRESS
        for m in cls._RE_ADDRESS.finditer(text):
            add_entity("ADDRESS", m.group(0), m.start(), m.end(), PrivacyClassification.SENSITIVE, 0.85)

        # 10. EMAIL
        for m in cls._RE_EMAIL.finditer(text):
            add_entity("EMAIL", m.group(0), m.start(), m.end(), PrivacyClassification.PERSONAL, 0.98)

        # 11. PHONE
        for m in cls._RE_PHONE.finditer(text):
            # Exclude numbers that overlap with cards or short digits
            raw = m.group(0)
            digits = re.sub(r"\D", "", raw)
            if 7 <= len(digits) <= 15:
                add_entity("PHONE", raw, m.start(), m.end(), PrivacyClassification.PERSONAL, 0.88)

        # 12. PERSONAL NAME
        for m in cls._RE_NAME_LABELED.finditer(text):
            add_entity("PERSONAL NAME", m.group(1), m.start(1), m.end(1), PrivacyClassification.PERSONAL, 0.90)
        for m in cls._RE_NAME_HONORIFIC.finditer(text):
            add_entity("PERSONAL NAME", m.group(0), m.start(), m.end(), PrivacyClassification.PERSONAL, 0.92)

        rank = {
            PrivacyClassification.PUBLIC: 0,
            PrivacyClassification.PERSONAL: 1,
            PrivacyClassification.SENSITIVE: 2,
            PrivacyClassification.SECRET: 3,
            PrivacyClassification.HIGHLY_SENSITIVE: 3,
        }
        entities.sort(key=lambda e: (e.start, -rank[e.classification], -(e.end - e.start)))
        filtered_entities: List[DetectedEntity] = []
        last_end = -1

        for ent in entities:
            if ent.start >= last_end:
                filtered_entities.append(ent)
                last_end = ent.end
            else:
                prev = filtered_entities[-1]
                if rank[ent.classification] > rank[prev.classification]:
                    filtered_entities[-1] = ent
                    last_end = max(last_end, ent.end)

        return filtered_entities

    @classmethod
    def redact_text(cls, text: str, entities: List[DetectedEntity]) -> str:
        """Redacts text by substituting detected entities marked for REDACT or BLOCK."""
        if not text or not entities:
            return text

        # Sort descending by start position to replace from end to beginning
        redactable = [e for e in entities if e.action in (PrivacyAction.REDACT, PrivacyAction.BLOCK)]
        if not redactable:
            return text

        redactable.sort(key=lambda e: e.start, reverse=True)
        result = list(text)

        for ent in redactable:
            tag = f"[REDACTED_{ent.type.replace(' ', '_').replace('/', '_')}]"
            result[ent.start:ent.end] = list(tag)

        return "".join(result)

    @classmethod
    def analyze(
        cls,
        text: str,
        mode: Optional[str] = None,
        stage: str = "general",
    ) -> PrivacyAnalysisResult:
        """Performs full privacy analysis, classification, action assignment, and redaction."""
        policy_mode = cls.get_policy_mode(mode)
        entities = cls.detect_entities(text, policy_mode=policy_mode, stage=stage)

        # Determine overall classification
        if any(e.classification == PrivacyClassification.HIGHLY_SENSITIVE for e in entities):
            overall_class = PrivacyClassification.HIGHLY_SENSITIVE
        elif any(e.classification == PrivacyClassification.SENSITIVE for e in entities):
            overall_class = PrivacyClassification.SENSITIVE
        elif any(e.classification == PrivacyClassification.PERSONAL for e in entities):
            overall_class = PrivacyClassification.PERSONAL
        else:
            overall_class = PrivacyClassification.PUBLIC

        # Determine if allowed or blocked
        has_block_action = any(e.action == PrivacyAction.BLOCK for e in entities)
        allowed = not has_block_action
        block_reason = None
        if not allowed:
            blocked_types = sorted(list({e.type for e in entities if e.action == PrivacyAction.BLOCK}))
            block_reason = f"Contains prohibited sensitive data: {', '.join(blocked_types)}"

        redacted_text = cls.redact_text(text, entities)

        return PrivacyAnalysisResult(
            classification=overall_class,
            entities=entities,
            allowed=allowed,
            policy_mode=policy_mode.value,
            redacted_text=redacted_text,
            block_reason=block_reason,
        )

    @classmethod
    def log_event(
        cls,
        event_type: str,
        severity: str,
        source: str,
        description: str,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        """Safely records a privacy event in SQLite.
        
        CRITICAL: Never logs actual sensitive values, passwords, keys, or card numbers.
        Only logs event metadata, entity type, severity, and generic descriptions.
        """
        should_close = False
        if conn is None:
            conn = get_db_connection()
            should_close = True

        try:
            conn.execute(
                """
                INSERT INTO privacy_events (event_type, severity, source, description, entity_type, action)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_type, severity, source, description, entity_type, action),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            if should_close:
                conn.close()
