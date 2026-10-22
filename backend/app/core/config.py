from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CFAP"
    app_env: str = "development"
    debug: bool = True

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = (
        "http://localhost:8000/api/v1/auth/google/callback"
    )

    llm_api_key: str = ""

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 100
    max_dataset_rows: int = 100000
    max_dataset_columns: int = 100

    # AI / ML Model Configuration (no secrets)
    sentiment_model: str = "nlptown/bert-base-multilingual-uncased-sentiment"
    emotion_model: str = "j-hartmann/emotion-english-distilroberta-base"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ml_batch_size: int = 32
    ml_max_text_length: int = 512
    ml_device: str = "auto"
    ai_batch_size: int = 32
    ai_max_text_length: int = 512
    ai_device: str = "auto"
    bertopic_min_topic_size: int = 3
    bertopic_nr_topics: str = "auto"

    # AI Assistant Configuration (Phase 6)
    ai_assistant_provider: str = "mock"  # "gemini", "openai", or "mock" (for testing/offline)
    ai_assistant_model: str = "gemini-1.5-flash"
    ai_assistant_temperature: float = 0.2
    ai_assistant_max_tokens: int = 1024
    ai_assistant_max_feedback_samples: int = 5
    gemini_api_key: str = ""
    openai_api_key: str = ""

    # Benchmarking & Audit Configuration (Phase 8)
    min_benchmark_sample_size: int = 5
    audit_log_retention_days: int = 90

    redis_url: str = "redis://127.0.0.1:6380/0"

    celery_broker_url: str = "redis://127.0.0.1:6380/0"
    celery_result_backend: str = "redis://127.0.0.1:6380/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()