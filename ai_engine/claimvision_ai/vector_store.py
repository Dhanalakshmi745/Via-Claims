from dataclasses import dataclass

import chromadb

from claimvision_ai.embeddings import Embedder

COLLECTION_NAME = "claim_documents"


@dataclass
class SearchResult:
    text: str
    document_id: int
    claim_id: int
    document_type: str
    chunk_index: int
    distance: float


class VectorStore:
    def __init__(self, persist_directory: str, embedder: Embedder):
        self._client = chromadb.PersistentClient(path=persist_directory)
        self._collection = self._client.get_or_create_collection(name=COLLECTION_NAME)
        self._embedder = embedder

    def index_document(
        self, *, document_id: int, claim_id: int, document_type: str, chunks: list[str]
    ) -> int:
        self.delete_document(document_id)
        if not chunks:
            return 0

        self._collection.add(
            ids=[f"doc{document_id}-chunk{i}" for i in range(len(chunks))],
            documents=chunks,
            embeddings=self._embedder.embed(chunks),
            metadatas=[
                {
                    "document_id": document_id,
                    "claim_id": claim_id,
                    "document_type": document_type,
                    "chunk_index": i,
                }
                for i in range(len(chunks))
            ],
        )
        return len(chunks)

    def delete_document(self, document_id: int) -> None:
        self._collection.delete(where={"document_id": document_id})

    def search(
        self, query: str, *, claim_id: int | None = None, top_k: int = 5
    ) -> list[SearchResult]:
        if not query.strip() or self._collection.count() == 0:
            return []

        raw = self._collection.query(
            query_embeddings=self._embedder.embed([query]),
            n_results=top_k,
            where={"claim_id": claim_id} if claim_id is not None else None,
        )

        return [
            SearchResult(
                text=text,
                document_id=metadata["document_id"],
                claim_id=metadata["claim_id"],
                document_type=metadata["document_type"],
                chunk_index=metadata["chunk_index"],
                distance=distance,
            )
            for text, metadata, distance in zip(
                raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
            )
        ]