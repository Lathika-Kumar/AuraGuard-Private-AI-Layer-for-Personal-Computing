from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class Settings:
    app_name: str = os.getenv("APP_NAME", "AuraGuard")
    app_env: str = os.getenv("APP_ENV", "development")
    app_debug: bool = os.getenv("APP_DEBUG", "true").lower() == "true"
    data_dir: Path = Path(os.getenv("DATA_DIR", "./data")).resolve()
    db_path: Path = Path(os.getenv("DB_PATH", str(data_dir / "auraguard.db"))).resolve()
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    api_version: str = "0.1.0"


settings = Settings()
