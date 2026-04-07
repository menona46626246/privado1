import logging
import os
from typing import Any, cast

import chromadb
from chromadb.utils import embedding_functions
from chromadb.api.types import Where
from dotenv import load_dotenv

from constants import Estado

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar cliente de ChromaDB local (persistencia en directorio)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Usar la función de embedding por defecto de Chroma (all-MiniLM-L6-v2)
# En el futuro, podemos cambiar a embeddings de OpenAI o Gemini
embedding_func: Any = embedding_functions.DefaultEmbeddingFunction()

collection_name = "autotramite_docs"
# Obtener o crear colección
collection = chroma_client.get_or_create_collection(
    name=collection_name,
    embedding_function=embedding_func,
)


def ingest_dummy_data():
    """Lee el documento dummy, lo divide en chunks y lo indexa en Chroma"""
    file_path = "data/cdmx_tramites_dummy.txt"
    if not os.path.exists(file_path):
        logger.error("No se encontró el archivo %s", file_path)
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Dividir rudimentariamente por el separador '---'
    chunks = [c.strip() for c in content.split("---") if c.strip()]

    documents = []
    ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        ids.append(f"cdmx_chunk_{i}")

        # Extracción simple de metadatos (para PoC)
        tramite_type = "general"
        if "Alta de Placas" in chunk:
            tramite_type = "alta_placas"
        elif "Renovación" in chunk:
            tramite_type = "renovacion_tarjeta"
        elif "Multas" in chunk:
            tramite_type = "multas"

        metadatas.append({
            "estado": Estado.CDMX.value,
            "tipo_tramite": tramite_type
        })

    # Indexar en la colección
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    logger.info("Indexados %d fragmentos en la BD Vectorial", len(documents))


def query_rag(pregunta: str, estado_filtro: str | None = None):
    """Busca fragmentos relevantes y simula el paso de generación RAG"""
    logger.info("\nUsuario: %s", pregunta)

    # Construir clausula de metadatos (Self Querying basico)
    where_clause: Where | None = None
    if estado_filtro:
        where_clause = cast(Where, {"estado": estado_filtro})

    # Búsqueda Vectorial
    results = collection.query(
        query_texts=[pregunta],
        n_results=2,
        where=where_clause,
    )

    print("\n[RECUPERACIÓN RAG - DB Vectorial]")
    if not results or not results["documents"] or not results["documents"][0]:
        print("No se encontró información relevante.")
        return

    # Safe access to results for MyPy — all values are Optional in chromadb stubs
    raw_docs = results["documents"]
    raw_dist = results["distances"]
    raw_meta = results["metadatas"]
    documents = raw_docs[0] if raw_docs is not None else []
    distances = raw_dist[0] if raw_dist is not None else []
    metadatas = raw_meta[0] if raw_meta is not None else []

    for doc, dist, meta in zip(documents, distances, metadatas):
        print(f"--- Meta: {meta} | Distancia: {dist:.4f}")
        print(doc[:100] + "...")

    print("\n[GENERACIÓN RAG - LLM (Simulado para esta PoC)]")
    print(f"Contexto recuperado: {len(results['documents'][0])} fragmentos.")
    print(
        "Prompt armado: 'Usando este contexto legal, responde la pregunta de forma natural y corta.'"
    )


if __name__ == "__main__":
    print("== PoC RAG AutoTrámite MX ==")
    # 1. Ingestar datos (solo es necesario una vez, pero repetible por el id handling de chroma)
    ingest_dummy_data()

    # 2. Hacer pruebas de preguntas
    query_rag("¿Cuánto cuesta dar de alta placas nuevas?", estado_filtro=Estado.CDMX.value)
    query_rag("Tengo una multa económica de la policia, ¿hay descuento?", estado_filtro=Estado.CDMX.value)
    query_rag("Dime sobre trámites en Monterrey", estado_filtro=Estado.NUEVO_LEON.value)  # Ahora usa el valor correcto
