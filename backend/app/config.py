from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # the backend/ folder


class Settings(BaseSettings):
    app_name: str = "ClaimVision API"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = f"sqlite:///{(BASE_DIR / 'claimvision.db').as_posix()}"

    upload_dir: str = str(BASE_DIR / "uploads")
    max_upload_mb: int = 10

    chroma_dir: str = str(BASE_DIR / "chroma_db")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    llm_provider: str = "gemini"
    llm_model: str = ""
    llm_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()