import logging
import os
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from constants import Estado

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar cliente de ChromaDB local (persistencia en directorio)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_func: Any = embedding_functions.DefaultEmbeddingFunction()

collection_name = "autotramite_docs"
collection = chroma_client.get_or_create_collection(
    name=collection_name,
    embedding_function=embedding_func,
)


def ingest_dummy_data():
    """Lee documentos dummy, los divide en chunks y los indexa en Chroma"""
    
    files_to_index = [
        {"path": "data/cdmx_tramites_dummy.txt", "estado": Estado.CDMX.value},
        {"path": "data/cdmx_tramites_real.txt", "estado": Estado.CDMX.value},
        {"path": "data/chihuahua_tramites_dummy.txt", "estado": Estado.CHIHUAHUA.value},
        {"path": "data/chihuahua_tramites_real.txt", "estado": Estado.CHIHUAHUA.value},
        {"path": "data/jalisco_tramites_real.txt", "estado": Estado.JALISCO.value},
        {"path": "data/nuevoleon_tramites_real.txt", "estado": Estado.NUEVO_LEON.value},
    ]
    
    documents = []
    ids = []
    metadatas = []
    
    chunk_counter = 0

    for file_info in files_to_index:
        file_path = file_info["path"]
        estado_val = file_info["estado"]
        
        if not os.path.exists(file_path):
            logger.error("No se encontró el archivo %s", file_path)
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Dividir rudimentariamente por el separador '---'
        chunks = [c.strip() for c in content.split("---") if c.strip()]

        for chunk in chunks:
            documents.append(chunk)
            ids.append(f"chunk_{chunk_counter}")
            chunk_counter += 1

            # Extracción simple de metadatos
            tramite_type = "general"
            if "Alta de Placas" in chunk:
                tramite_type = "alta_placas"
            elif "Renovación" in chunk or "Revalidación" in chunk:
                tramite_type = "renovacion_tarjeta"
            elif "Multas" in chunk:
                tramite_type = "multas"
            elif "Licencia" in chunk:
                tramite_type = "licencias"

            metadatas.append({
                "estado": estado_val,
                "tipo_tramite": tramite_type
            })

    # Indexar en la colección
    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info("Indexados %d fragmentos en la BD Vectorial", len(documents))


if __name__ == "__main__":
    ingest_dummy_data()

