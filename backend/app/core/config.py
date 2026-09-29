from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _resolve_path(value: str, default: str) -> Path:
    return Path(value if value else default).resolve()


class Settings:
    app_name: str = os.getenv("APP_NAME", "AuraGuard")
    app_env: str = os.getenv("APP_ENV", "development")
    app_debug: bool = os.getenv("APP_DEBUG", "true").lower() == "true"
    data_dir: Path = _resolve_path(os.getenv("DATA_DIR", "./data"), "./data")
    db_path: Path = _resolve_path(os.getenv("DB_PATH", str(data_dir / "auraguard.db")), str(data_dir / "auraguard.db"))
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    api_version: str = "0.1.0"
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "700"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    retrieval_min_score: float = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.35"))
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    embedding_device: str = os.getenv("EMBEDDING_DEVICE", "cpu")
    model_cache_dir: Path = _resolve_path(os.getenv("MODEL_CACHE_DIR", "./models"), "./models")
    llm_model: str = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
    llm_device: str = os.getenv("LLM_DEVICE", "cpu")
    llm_max_new_tokens: int = int(os.getenv("LLM_MAX_NEW_TOKENS", "128"))
    vector_index_path: Path = _resolve_path(os.getenv("VECTOR_INDEX_PATH", str(data_dir / "index" / "faiss.index")), str(data_dir / "index" / "faiss.index"))
    vector_index_dir: Path = _resolve_path(os.getenv("VECTOR_INDEX_DIR", str(data_dir / "index")), str(data_dir / "index"))
    document_dir: Path = _resolve_path(os.getenv("DOCUMENT_DIR", str(data_dir / "documents")), str(data_dir / "documents"))
    extracted_dir: Path = _resolve_path(os.getenv("EXTRACTED_DIR", str(data_dir / "extracted")), str(data_dir / "extracted"))
    ai_execution_provider: str = os.getenv("AI_EXECUTION_PROVIDER", "auto").lower()


settings = Settings()

# Ensure model cache directories and environment variables are set
settings.model_cache_dir.mkdir(parents=True, exist_ok=True)
(settings.model_cache_dir / "huggingface").mkdir(parents=True, exist_ok=True)
(settings.model_cache_dir / "fastembed").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(settings.model_cache_dir / "huggingface"))
os.environ.setdefault("FASTEMBED_CACHE_PATH", str(settings.model_cache_dir / "fastembed"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
