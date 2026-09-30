from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.database.database import get_user_policy, save_user_policy
from app.services.hardware_service import HardwareService
from app.services.privacy_service import PrivacyAction, PrivacyClassification, PrivacyService


@dataclass
class DecisionResult:
    processing_mode: str
    privacy_mode: str
    sensitivity: str
    user_intent: str
    memory_allowed: bool
    retrieval_allowed: bool
    sensitive_data_detected: bool
    execution_provider: str
    fallback_active: bool
    network_policy: str
    model_id: str
    reason: str
    allowed: bool = True
    block_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PrivateAIDecisionService:
    """AuraGuard Private AI Decision Layer.
    
    Dynamically governs how personal information is processed, remembered,
    retrieved, and protected based on:
    1. Data Sensitivity (PUBLIC, PERSONAL, SENSITIVE, SECRET)
    2. User Intent (DOCUMENT_QUERY, MEMORY_RECALL, MEMORY_STORE, GENERAL_QUERY)
    3. Available Hardware (QNNExecutionProvider on Qualcomm NPU vs CPUExecutionProvider)
    4. User Privacy Policy (Strict, Balanced, Performance)
    5. Memory Policy (Off, Ask, Auto)
    6. Model Availability & Fallback Architecture
    """

    @classmethod
    def get_effective_policy(cls) -> Dict[str, Any]:
        """Fetches the persisted user privacy policy."""
        return get_user_policy()

    @classmethod
    def update_policy(cls, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates user privacy policy settings and logs a ledger event."""
        updated = save_user_policy(updates)
        PrivacyService.log_event(
            event_type="POLICY_CHANGED",
            severity="LOW",
            source="user_settings",
            description=f"User privacy policy updated: {', '.join(f'{k}={v}' for k, v in updates.items())}",
            action="UPDATE",
        )
        return updated

    @classmethod
    def classify_sensitivity(cls, text: str, policy_mode: str = "balanced") -> Tuple[str, bool, Any]:
        """Classifies text sensitivity into PUBLIC, PERSONAL, SENSITIVE, or SECRET."""
        analysis = PrivacyService.analyze(text, mode=policy_mode, stage="input")

        raw_class = analysis.classification
        if raw_class in (PrivacyClassification.SECRET, PrivacyClassification.HIGHLY_SENSITIVE):
            level = "SECRET"
            has_sensitive = True
        elif raw_class == PrivacyClassification.SENSITIVE:
            level = "SENSITIVE"
            has_sensitive = True
        elif raw_class == PrivacyClassification.PERSONAL:
            level = "PERSONAL"
            has_sensitive = False
        else:
            level = "PUBLIC"
            has_sensitive = False

        return level, has_sensitive, analysis

    @classmethod
    def classify_intent(cls, query: str) -> str:
        """Determines the user's operational intent from their query."""
        q_lower = query.lower().strip()

        # Intent: Storing a memory
        if re.search(r"\b(?:remember\s+(?:that|this)?|don't\s+forget|note\s+that|save\s+(?:to\s+)?memory)\b", q_lower):
            return "MEMORY_STORE"

        # Intent: Recalling personal memories
        if re.search(r"\b(?:what\s+(?:did\s+i|do\s+you)\s+remember|my\s+preferences?|what\s+is\s+my\s+favorite|my\s+notes?)\b", q_lower):
            return "MEMORY_RECALL"

        # Intent: Inquiring about documents / files
        if re.search(r"\b(?:in\s+(?:the\s+)?(?:document|pdf|file|notes?|page)|according\s+to|what\s+does\s+the\s+contract|summary\s+of)\b", q_lower):
            return "DOCUMENT_QUERY"

        return "GENERAL_QUERY"

    @classmethod
    def evaluate(
        cls,
        query: str,
        policy_override: Optional[Dict[str, Any]] = None,
    ) -> DecisionResult:
        """Determines the end-to-end execution decision for an AI query."""
        policy = policy_override or cls.get_effective_policy()
        privacy_mode = policy.get("privacy_mode", settings.privacy_mode)

        # 1. Sensitivity classification
        sensitivity, has_sensitive, analysis = cls.classify_sensitivity(query, policy_mode=privacy_mode)

        # 2. Intent classification
        user_intent = cls.classify_intent(query)

        # 3. Hardware & Execution Provider resolution
        active_ep, status_reason, fallback_occurred = HardwareService.resolve_execution_provider()
        is_sd = HardwareService.is_snapdragon()
        is_npu = HardwareService.is_npu_available()
        snapdragon_ready = is_sd and is_npu and (active_ep == "QNNExecutionProvider")

        # 4. Model resolution
        model_id = settings.llm_model

        # 5. Policy rules evaluation
        local_processing = policy.get("local_processing", "ON") == "ON"
        external_ai = policy.get("external_ai", "BLOCKED")
        memory_mode = policy.get("memory_mode", "ASK")
        sensitive_action = policy.get("sensitive_data_action", "BLOCK")
        doc_retrieval = policy.get("document_retrieval", "ON") == "ON"

        processing_mode = "LOCAL_ONLY" if local_processing else "HYBRID"
        network_policy = "BLOCKED" if external_ai == "BLOCKED" else "RESTRICTED"

        retrieval_allowed = doc_retrieval
        memory_allowed = memory_mode != "OFF"

        allowed = True
        block_reason = None

        # Check for blocked sensitive content
        if has_sensitive:
            if sensitivity == "SECRET" and sensitive_action == "BLOCK":
                allowed = False
                block_reason = analysis.block_reason or "Prohibited SECRET credential detected in query"
            elif sensitivity == "SENSITIVE" and privacy_mode == "strict" and sensitive_action == "BLOCK":
                allowed = False
                block_reason = analysis.block_reason or "Sensitive PII blocked under Strict privacy policy"

        # Determine human-readable rationale
        if not allowed:
            reason = f"Request blocked: {block_reason}."
        elif active_ep == "QNNExecutionProvider" and snapdragon_ready:
            reason = "Qualcomm NPU available; executing locally via QNNExecutionProvider."
        elif fallback_occurred:
            reason = f"Local processing policy selected; {status_reason}."
        else:
            reason = f"Local processing policy selected; executing locally on {active_ep}."

        return DecisionResult(
            processing_mode=processing_mode,
            privacy_mode=privacy_mode,
            sensitivity=sensitivity,
            user_intent=user_intent,
            memory_allowed=memory_allowed,
            retrieval_allowed=retrieval_allowed,
            sensitive_data_detected=has_sensitive,
            execution_provider=active_ep,
            fallback_active=fallback_occurred,
            network_policy=network_policy,
            model_id=model_id,
            reason=reason,
            allowed=allowed,
            block_reason=block_reason,
        )

    @classmethod
    def detect_memory_candidate(cls, query: str, answer: str = "") -> Optional[Dict[str, Any]]:
        """Detects if user input contains personal context worth remembering (Part 5)."""
        policy = cls.get_effective_policy()
        if policy.get("memory_mode") == "OFF":
            return None

        # Detect candidate phrasing
        pref_match = re.search(
            r"\b(?:i\s+(?:prefer|like|want|need|always\s+use|usually\s+choose)|my\s+(?:favorite|preferred|email|phone|role|team|project|manager|doctor)\s+(?:is|are)?)\s+(.+)",
            query,
            re.IGNORECASE,
        )
        explicit_match = re.search(
            r"\b(?:remember\s+(?:that|this)?|don't\s+forget\s+(?:that)?|note\s+that)\s+(.+)",
            query,
            re.IGNORECASE,
        )

        content = None
        mem_type = "NOTE"

        if pref_match:
            content = query.strip()
            mem_type = "PREFERENCE"
        elif explicit_match:
            content = explicit_match.group(1).strip()
            mem_type = "FACT"

        if not content:
            return None

        # Check sensitivity: Never automatically prompt to remember SECRET credentials
        level, has_sensitive, analysis = cls.classify_sensitivity(content)
        if level == "SECRET":
            return None

        return {
            "content": content,
            "memory_type": mem_type,
            "sensitivity": level,
            "reason": "User preference or recurring context detected.",
            "requires_user_approval": policy.get("automatic_memory", "OFF") != "ON",
        }
