import pytest
from app.services.ai_service import AIProvider


def test_ai_provider_initialization() -> None:
    provider = AIProvider()
    assert provider.model is not None
    assert provider.tokenizer is not None


def test_grounded_generation_with_matching_context() -> None:
    provider = AIProvider()
    context = "(p1) The AuraGuard application deadline is Friday, October 15, 2026."
    question = "When is the AuraGuard application deadline?"
    answer, latency = provider.generate(question, context)
    assert "October 15, 2026" in answer
    assert latency > 0.0


def test_grounded_generation_unrelated_context_refusal() -> None:
    provider = AIProvider()
    context = "(p1) The AuraGuard project is developed for personal computers."
    question = "What is the speed of light in kilometers per second?"
    answer, latency = provider.generate(question, context)
    assert "couldn't find enough relevant information" in answer
