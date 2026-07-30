from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.secrets import resolve_openai_api_key


class Settings(BaseSettings):
    PROJECT_NAME: str = "Knowledge RAG Agent"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"

    # Provider selection per domain (independent so local/prod can mix
    # during migration).
    LLM_PROVIDER: str = "ollama"  # ollama | openai
    EMBEDDING_PROVIDER: str = "ollama"  # ollama | openai
    VECTOR_DB_PROVIDER: str = "chroma"  # chroma | pgvector
    STORAGE_PROVIDER: str = "filesystem"  # filesystem | s3

    # Unified model ids (ollama locally, openai in production/demo).
    LLM_MODEL: str = "qwen2.5:3b"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    # Vector width for the active embedding model. text-embedding-3-small
    # defaults to 1536; nomic-embed-text is 768 (Chroma does not require
    # this for schema, but pgvector does).
    EMBEDDING_DIMENSIONS: int = 768

    # Local/dev: set OPENAI_API_KEY directly.
    # Production: leave empty and set OPENAI_API_KEY_SSM_PARAMETER to the
    # SSM SecureString name; the value is loaded at runtime.
    OPENAI_API_KEY: str = ""
    OPENAI_API_KEY_SSM_PARAMETER: str = ""

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    # Legacy aliases; prefer LLM_MODEL / EMBEDDING_MODEL.
    OLLAMA_LLM_MODEL: str = "qwen2.5:3b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    CHROMA_PATH: str = "./chroma_db"
    CHROMA_COLLECTION: str = "documents"

    RAG_TOP_K: int = 8
    RAG_MIN_SCORE: float = 0.35

    AWS_REGION: str = "sa-east-1"

    # Aurora PostgreSQL Serverless v2 + pgvector (RDS Data API)
    AURORA_CLUSTER_ARN: str = ""
    AURORA_SECRET_ARN: str = ""
    AURORA_DATABASE_NAME: str = "ragagent"
    AURORA_TABLE_NAME: str = "document_chunks"

    # S3 (original PDFs + ingest status markers in production)
    S3_DOCUMENTS_BUCKET: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    def resolve_llm_model(self) -> str:
        """Return the model id for the active LLM provider."""
        if self.LLM_PROVIDER.lower() == "ollama":
            return self.LLM_MODEL or self.OLLAMA_LLM_MODEL
        return self.LLM_MODEL

    def resolve_embedding_model(self) -> str:
        """Return the model id for the active embedding provider."""
        if self.EMBEDDING_PROVIDER.lower() == "ollama":
            return self.EMBEDDING_MODEL or self.OLLAMA_EMBEDDING_MODEL
        return self.EMBEDDING_MODEL

    def resolve_openai_api_key(self) -> str:
        """Return the OpenAI API key from env or SSM SecureString."""
        return resolve_openai_api_key(
            api_key=self.OPENAI_API_KEY,
            ssm_parameter_name=self.OPENAI_API_KEY_SSM_PARAMETER,
            aws_region=self.AWS_REGION,
        )


settings = Settings()
