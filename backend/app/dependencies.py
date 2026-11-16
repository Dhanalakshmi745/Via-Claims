import logging
from functools import lru_cache

from claimvision_ai.embeddings import SentenceTransformerEmbedder
from claimvision_ai.llm import LLMClient, create_llm_client
from claimvision_ai.vector_store import VectorStore
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore(
        persist_directory=settings.chroma_dir,
        embedder=SentenceTransformerEmbedder(settings.embedding_model),
    )


@lru_cache
def build_llm_client() -> LLMClient:
    return create_llm_client(settings.llm_provider, settings.llm_api_key, settings.llm_model)


def get_llm_client() -> LLMClient:
    try:
        return build_llm_client()
    except (ValueError, ImportError) as exc:
        logger.error("The language model is not configured: %s", exc)
        raise HTTPException(status_code=503, detail="The AI assistant is not configured")