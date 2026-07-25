from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://recipe:recipe@localhost:5432/recipes")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    chat_model: str = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    retrieval_mode: str = os.getenv("RETRIEVAL_MODE", "hybrid")
    top_k: int = int(os.getenv("TOP_K", "5"))
    reranker_model: str = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")


settings = Settings()
