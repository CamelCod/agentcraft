from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    secret_key: str = "dev-secret-key"
    first_superuser_email: str = "admin@example.com"
    first_superuser_password: str = "changeme"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "youtubekg"
    postgres_user: str = "youtubekg"
    postgres_password: str = "changeme"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "changeme"
    minio_bucket_raw: str = "raw-audio"
    minio_bucket_transcripts: str = "transcripts"
    minio_bucket_reports: str = "reports"
    minio_secure: bool = False

    # YouTube
    youtube_api_key: str = ""

    # LLM
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "claude-haiku-4-5-20251001"
    llm_report_model: str = "claude-sonnet-4-6"

    # Embeddings
    embedding_provider: str = "sentence-transformers"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384

    # Whisper
    whisper_service_url: str = "http://localhost:9002"
    whisper_model: str = "medium"
    whisper_default_language: str = "auto"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_concurrency: int = 4

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # Supabase (leave blank to keep legacy JWT auth)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""  # Project Settings > API > JWT Secret

    # CORS
    cors_origins: str = "http://localhost,http://localhost:3000,https://agentcraftconsultancy.com"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    # Verification thresholds
    verification_min_occurrences: int = 2
    verification_similarity_threshold: float = 0.82
    verification_occurrence_weight: float = 0.4
    verification_source_consistency_weight: float = 0.3
    verification_semantic_coherence_weight: float = 0.3


@lru_cache
def get_settings() -> Settings:
    return Settings()
