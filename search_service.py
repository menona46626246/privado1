import logging
import asyncio
from duckduckgo_search import AsyncDDGS

logger = logging.getLogger(__name__)

async def search_web_latest(query: str, max_results: int = 4) -> str:
    """
    Busca en internet información reciente sobre trámites vehiculares. 
    Retorna un string con los resultados resumidos.
    """
    logger.info("[AgentSearch] Buscando en la web: %s", query)
    
    # Optimizamos la query para buscar temas de gobierno en México
    search_query = f"{query} México trámites oficiales"
    
    try:
        async with AsyncDDGS() as ddgs:
            results = await ddgs.text(search_query, max_results=max_results, region="mx-es")
            
            if not results:
                return "No se encontraron resultados recientes en la web."
            
            summary = "\n\n--- RESULTADOS DE INVESTIGACIÓN EN VIVO ---\n"
            for r in results:
                summary += f"🔹 {r.get('title')}\n   {r.get('body')}\n   🔗 [Fuente: {r.get('href')}]\n\n"
            
            return summary
            
    except Exception as e:
        logger.error("[AgentSearch] Error en búsqueda web: %s", e)
        return "Hubo un error al intentar investigar en la web en este momento."
