import logging
from typing import Any, cast

import chromadb
from chromadb.utils import embedding_functions
from chromadb.api.types import Where

logger = logging.getLogger(__name__)

# Reutilizamos la conexión a ChromaDB mapeada al disco
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_func: Any = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(
    name="autotramite_docs",
    embedding_function=embedding_func,
)


def get_rag_context(
    query: str, state_filter: str | None = None, top_k: int = 2
) -> str:
    """Busca en ChromaDB los requisitos gubernamentales más relevantes."""

    where_clause: Where | None = None
    if state_filter:
        where_clause = cast(Where, {"estado": state_filter})

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=where_clause,
    )

    if not results or not results["documents"] or not results["documents"][0]:
        return "No se encontraron regulaciones oficiales al respecto."

    context = ""
    raw_docs = results["documents"]
    raw_meta = results["metadatas"]

    # Safely extract first-batch lists; both values are Optional in the chromadb type stubs
    documents = raw_docs[0] if raw_docs is not None else []
    metadatas = raw_meta[0] if raw_meta is not None else []

    if documents and metadatas:
        for doc, meta in zip(documents, metadatas):
            if meta is None:
                continue
            context += (
                f"--- DATOS OFICIALES ---\n"
                f"Estado: {meta.get('estado', 'N/A')} | "
                f"Trámite: {meta.get('tipo_tramite', 'N/A')}\n"
                f"{doc}\n"
            )

    return context
