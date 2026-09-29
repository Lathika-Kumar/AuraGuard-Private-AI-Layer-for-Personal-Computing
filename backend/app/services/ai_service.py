from __future__ import annotations

import os
import time
from typing import Any, List, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.core.config import settings
from app.services.retrieval_service import RetrievalService
from app.services.hardware_service import HardwareService
from app.database.database import get_db_connection


AURA_GUARD_SYSTEM_PROMPT = (
    "You are AuraGuard, a private local AI assistant.\n"
    "Answer ONLY using the supplied context.\n"
    "If the context does not contain enough information, say:\n"
    "\"I couldn't find enough relevant information in your local documents.\"\n"
    "Do not invent facts.\n"
    "Do not invent:\n"
    "- names\n"
    "- dates\n"
    "- deadlines\n"
    "- amounts\n"
    "- organizations\n"
    "- requirements\n"
    "- personal information"
)


class AIProvider:
    """Real local on-device neural language model provider.
    
    Uses Qwen2.5-0.5B-Instruct running on local CPU via Transformers / PyTorch.
    Designed with a modular boundary ready for Qualcomm AI Hub / QNN Execution Provider
    with automatic CPU fallback and runtime hardware telemetry.
    """
    _tokenizer: AutoTokenizer | None = None
    _model: AutoModelForCausalLM | None = None
    _loaded_model_id: str | None = None

    def __init__(self, model_id: str | None = None, device: str | None = None):
        self.model_id = model_id or settings.llm_model
        self.device = device or settings.llm_device
        self.retriever = RetrievalService()
        self._ensure_model_loaded()

    def _ensure_model_loaded(self) -> None:
        if AIProvider._model is None or AIProvider._loaded_model_id != self.model_id:
            # Point HF_HOME to configured cache dir on local drive
            os.environ.setdefault("HF_HOME", str(settings.model_cache_dir / "huggingface"))
            os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

            AIProvider._tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                cache_dir=str(settings.model_cache_dir / "huggingface"),
            )
            AIProvider._model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                cache_dir=str(settings.model_cache_dir / "huggingface"),
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True,
            )
            AIProvider._model.eval()
            AIProvider._loaded_model_id = self.model_id

        self.tokenizer = AIProvider._tokenizer
        self.model = AIProvider._model

    @property
    def metadata(self) -> dict[str, Any]:
        active_provider, status_reason, fallback_occurred = HardwareService.resolve_execution_provider()
        return {
            "model_id": self.model_id,
            "runtime": "pytorch",
            "active_provider": "CPU" if active_provider == "CPUExecutionProvider" else active_provider,
            "configured_provider": getattr(settings, "ai_execution_provider", "auto"),
            "fallback_occurred": fallback_occurred,
            "status_reason": status_reason,
            "device": self.device,
            "precision": "float32",
            "max_new_tokens": settings.llm_max_new_tokens,
        }

    def generate(self, question: str, context: str) -> Tuple[str, float]:
        """Generate a strictly grounded answer from context. Returns (answer, latency_seconds)."""
        messages = [
            {"role": "system", "content": AURA_GUARD_SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        t0 = time.time()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=settings.llm_max_new_tokens,
                do_sample=False,
            )
        t_gen = time.time() - t0

        generated_ids = outputs[0][inputs.input_ids.shape[1]:]
        answer = self.tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        return answer, t_gen

    def answer(self, query: str, top_k: int = 4) -> dict[str, Any]:
        """Executes full Grounded RAG: Query -> Real Embedding -> FAISS -> Chunks -> Local LLM -> Answer."""
        t_total_start = time.time()
        runtime_info = HardwareService.get_ai_runtime_info()
        active_provider = runtime_info["active_execution_provider"]

        # Check if any documents exist in the database
        conn = get_db_connection()
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        if doc_count == 0:
            return {
                "answer": "No local documents are indexed yet.",
                "sources": [],
                "query": query,
                "metrics": {
                    "total_latency_seconds": round(time.time() - t_total_start, 4),
                    "chunks_retrieved": 0,
                    "execution_provider": active_provider,
                },
                "ai_runtime": runtime_info,
            }

        # Retrieve relevant chunks using real embedding + FAISS
        results, embed_lat, search_lat = self.retriever.search(query, top_k=top_k)

        # If no relevant chunks match the minimum threshold
        if not results:
            return {
                "answer": "I couldn't find enough relevant information in your local documents.",
                "sources": [],
                "query": query,
                "metrics": {
                    "embedding_latency_seconds": round(embed_lat, 4),
                    "search_latency_seconds": round(search_lat, 4),
                    "llm_latency_seconds": 0.0,
                    "total_latency_seconds": round(time.time() - t_total_start, 4),
                    "chunks_retrieved": 0,
                    "execution_provider": active_provider,
                },
                "ai_runtime": runtime_info,
            }

        # Build context from retrieved chunks
        context_parts = []
        sources = []
        for r in results:
            context_parts.append(f"(p{r['page_number']}) {r['text']}")
            sources.append(
                {
                    "document_id": r["document_id"],
                    "filename": r["document_filename"],
                    "page_number": r["page_number"],
                    "chunk_id": r["chunk_id"],
                }
            )
        context = "\n\n".join(context_parts)

        # Generate grounded answer with real local LLM
        answer_text, llm_lat = self.generate(query, context)
        t_total = time.time() - t_total_start

        return {
            "answer": answer_text,
            "sources": sources,
            "query": query,
            "metrics": {
                "embedding_latency_seconds": round(embed_lat, 4),
                "search_latency_seconds": round(search_lat, 4),
                "llm_latency_seconds": round(llm_lat, 4),
                "total_latency_seconds": round(t_total, 4),
                "chunks_retrieved": len(results),
                "execution_provider": active_provider,
            },
            "ai_runtime": runtime_info,
        }
