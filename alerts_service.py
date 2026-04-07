import logging
import asyncio
from config import settings
import aiohttp

logger = logging.getLogger(__name__)

async def send_admin_alert(message: str, severity: str = "ERROR"):
    """
    Envia una alerta crítica al administrador. 
    Se puede configurar para usar un webhook de Discord o un mensaje directo.
    """
    logger.info("[Alerts] %s: %s", severity, message)
    
    # Si tienes un DISCORD_WEBHOOK_URL en el .env, lo usará.
    # Por ahora, si no hay webhook, solo lo dejamos en el log central.
    # Implementación recomendada: Discord Webhook
    
    webhook_url = getattr(settings, "discord_webhook_url", None)
    
    if webhook_url:
        payload = {
            "content": f"🚨 **AUTO-TRÁMITE ALERT** [{severity}]\n{message}"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as resp:
                    if resp.status != 204:
                            logger.error("[Alerts] Error enviando a Discord Webhook: %s", resp.status)
        except Exception as e:
            logger.error("[Alerts] Fallo al mandar alerta: %s", e)
    else:
        logger.warning("[Alerts] No hay Webhook de Discord configurado para alertas.")

def notify_critical_error(error_msg: str):
    """Lanzador síncrono para usar en try/except."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(send_admin_alert(error_msg))
    else:
        asyncio.run(send_admin_alert(error_msg))
