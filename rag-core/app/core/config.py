from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Knowledge RAG Agent"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"

    # Selección de proveedor por dominio. Se seleccionan de forma
    # independiente (no por un único ENVIRONMENT) para permitir
    # combinaciones durante la migración o pruebas.
    LLM_PROVIDER: str = "ollama"  # ollama | openai | bedrock
    EMBEDDING_PROVIDER: str = "ollama"  # ollama | bedrock
    VECTOR_DB_PROVIDER: str = "chroma"  # chroma | pgvector
    STORAGE_PROVIDER: str = "filesystem"  # filesystem | s3

    # Modelo LLM unificado (ollama / openai). Bedrock sigue usando
    # BEDROCK_LLM_MODEL_ID por compatibilidad con infra existente.
    LLM_MODEL: str = "qwen2.5:3b"
    OPENAI_API_KEY: str = ""

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    # Legacy alias; prefer LLM_MODEL. Kept so existing .env files still work.
    OLLAMA_LLM_MODEL: str = "qwen2.5:3b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    CHROMA_PATH: str = "./chroma_db"
    CHROMA_COLLECTION: str = "documents"

    RAG_TOP_K: int = 8
    RAG_MIN_SCORE: float = 0.35

    # AWS / Bedrock
    AWS_REGION: str = "sa-east-1"
    BEDROCK_LLM_MODEL_ID: str = "amazon.nova-micro-v1:0"
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v2:0"
    BEDROCK_EMBEDDING_DIMENSIONS: int = 1024

    # Aurora PostgreSQL Serverless v2 + pgvector (acceso vía RDS Data API,
    # sin necesidad de que Lambda esté dentro de la VPC)
    AURORA_CLUSTER_ARN: str = ""
    AURORA_SECRET_ARN: str = ""
    AURORA_DATABASE_NAME: str = "ragagent"
    AURORA_TABLE_NAME: str = "document_chunks"

    # S3 (almacenamiento de PDFs originales en producción)
    S3_DOCUMENTS_BUCKET: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    def resolve_llm_model(self) -> str:
        """Return the model id for the active LLM provider."""
        provider = self.LLM_PROVIDER.lower()
        if provider == "bedrock":
            return self.BEDROCK_LLM_MODEL_ID
        if provider == "ollama":
            # Prefer unified LLM_MODEL; fall back to legacy OLLAMA_LLM_MODEL.
            return self.LLM_MODEL or self.OLLAMA_LLM_MODEL
        return self.LLM_MODEL


settings = Settings()
