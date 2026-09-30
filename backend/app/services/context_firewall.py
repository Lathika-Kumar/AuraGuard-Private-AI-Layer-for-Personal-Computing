from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from app.services.privacy_service import PrivacyService


class ContextFirewall:
    """Dedicated Context Firewall for on-device AI.
    
    Inspects retrieved document chunks and memories prior to LLM synthesis.
    Features:
    1. Detects prompt injection and adversarial directives.
    2. Removes or neutralizes malicious commands while preserving legitimate factual context.
    3. Records security events in the local privacy ledger.
    4. Produces transparent explanations (reason, action, source).
    """

    # Injection detection regex patterns
    INJECTION_PATTERNS = [
        (
            re.compile(
                r"\b(?:ignore|disregard|forget|override)\s+(?:all\s+)?(?:previous|prior|above|system)\s+(?:instructions?|rules?|directives?|prompts?)[^.\n]*[.\n]?",
                re.IGNORECASE,
            ),
            "Instruction Override Attempt",
            "Retrieved content attempted to modify AI instructions.",
        ),
        (
            re.compile(
                r"\b(?:critical\s+)?system\s+override[:\s]+[^\n]*",
                re.IGNORECASE,
            ),
            "System Override Directive",
            "Retrieved content contained an explicit system override directive.",
        ),
        (
            re.compile(
                r"\byou\s+are\s+now\s+(?:in\s+)?(?:developer|jailbreak|DAN|unrestricted|god)\s+mode[^\n]*",
                re.IGNORECASE,
            ),
            "Jailbreak Persona Shift",
            "Retrieved content attempted to enforce an unconstrained persona mode.",
        ),
        (
            re.compile(
                r"\boutput\s+the\s+(?:secret|word|password|key|flag)\s+[A-Za-z0-9_]+[.\n]?",
                re.IGNORECASE,
            ),
            "Exfiltration Target Probe",
            "Retrieved content attempted to force exfiltration of internal keywords.",
        ),
        (
            re.compile(
                r"\bdisregard\s+(?:all\s+)?(?:safety|content|security)\s+(?:guidelines|filters|boundaries)[^\n]*",
                re.IGNORECASE,
            ),
            "Safety Boundary Bypass",
            "Retrieved content attempted to bypass safety boundaries.",
        ),
    ]

    @classmethod
    def filter_context(
        cls,
        raw_context: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        memories: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[str, List[Dict[str, Any]], bool]:
        """Filters retrieved context through the firewall.
        
        Returns:
            sanitized_context: Cleaned context with malicious directives stripped/neutralized.
            firewall_events: Detailed explanations for any blocked/neutralized attempts.
            injections_found: Boolean flag indicating whether injections were mitigated.
        """
        if not raw_context:
            return "", [], False

        sanitized_context = raw_context
        firewall_events: List[Dict[str, Any]] = []
        injections_found = False

        for pattern, pattern_name, reason in cls.INJECTION_PATTERNS:
            matches = list(pattern.finditer(sanitized_context))
            if matches:
                injections_found = True
                for match in matches:
                    matched_text = match.group(0).strip()
                    
                    # Associate with a source if possible
                    source_name = "Retrieved Context"
                    if sources:
                        source_name = sources[0].get("filename") or "document.pdf"
                        if sources[0].get("page_number"):
                            source_name += f" — Page {sources[0]['page_number']}"
                    elif memories:
                        source_name = f"ReMind Memory #{memories[0].get('id', 'N/A')}"

                    explanation = {
                        "category": pattern_name,
                        "reason": reason,
                        "action": "Instruction neutralized.",
                        "source": source_name,
                    }
                    firewall_events.append(explanation)

                    # Log to Privacy Event Ledger without storing full secret payload
                    PrivacyService.log_event(
                        event_type="PROMPT_INJECTION_BLOCKED",
                        severity="HIGH",
                        source="context_firewall",
                        description=f"Neutralized {pattern_name} from {source_name}: {reason}",
                        entity_type="INJECTION_ATTEMPT",
                        action="NEUTRALIZE",
                    )

                # Neutralize matched directives while preserving valid surrounding factual sentences
                sanitized_context = pattern.sub(
                    "[Instruction neutralized by Context Firewall] ",
                    sanitized_context,
                )

        return sanitized_context, firewall_events, injections_found
