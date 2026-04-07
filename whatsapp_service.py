import asyncio
import logging

from twilio.rest import Client  # type: ignore[import-untyped]

from config import settings

logger = logging.getLogger(__name__)

# Validar estructuralmente si el usuario puso credenciales reales
if (
    not settings.twilio_account_sid
    or settings.twilio_account_sid == "tu_sid_de_twilio"
    or not settings.twilio_auth_token
):
    _twilio_client = None
    logger.info("Credenciales de Twilio no detectadas. Usando Modo Simulación Local.")
else:
    try:
        _twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    except Exception as e:
        logger.warning("Twilio no pudo autenticar: %s", e)
        _twilio_client = None


async def send_whatsapp_message(to_number: str, body: str) -> bool:
    """
    Envía un mensaje de WhatsApp a través de Twilio (async-safe).
    'to_number' debe tener el prefijo 'whatsapp:+52...'
    """
    if not _twilio_client:
        logger.info(
            "\n%s\n🤖 BOT (Para %s):\n%s\n%s",
            "🟢 " * 15,
            to_number,
            body,
            "🟢 " * 15,
        )
        return True

    try:
        # Asegurarse que el número empiece con whatsapp:
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"

        # Ejecutar la llamada síncrona de Twilio en un hilo separado
        # para no bloquear el event loop de FastAPI
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: _twilio_client.messages.create(  # type: ignore[union-attr]
                from_=settings.twilio_whatsapp_number, body=body, to=to_number
            ),
        )
        return True
    except Exception as e:
        logger.error("Error enviando mensaje por Twilio: %s", e)
        return False
