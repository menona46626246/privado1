import logging
from fastapi import FastAPI, Form, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse
from chat_controller import handle_incoming_message
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoTrámite webhooks")

@app.on_event("startup")
async def on_startup():
    start_scheduler()

# Diccionario temporal para guardar la "vista" de respuesta y poder responder a un HTTP asíncronamente
# Sin embargo, en Twilio Webhooks si respondemos tarde (>15s) falla.
# Lo ideal es enviar respuesta vacía y luego mandar mensaje usando Client de Twilio.
# Para este MVP si procesamos rápido, respondemos TwiML.
from twilio.rest import Client
from config import settings

twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token) if settings.twilio_account_sid else None

async def send_whatsapp_async(to_number: str, text: str, media_url: str | None = None):
    if not twilio_client:
        logger.error("Twilio no configurado. Ignorando mensaje: %s", text)
        return
        
    try:
        kwargs = {
            "from_": settings.twilio_whatsapp_number,
            "body": text[:1600],
            "to": to_number
        }
        if media_url:
            kwargs["media_url"] = [media_url]
            
        twilio_client.messages.create(**kwargs)
    except Exception as e:
        logger.error("Error enviando WhatsApp via Twilio: %s", e)

@app.post("/webhook/whatsapp")
async def twilio_whatsapp_webhook(
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(default=""),
    MediaUrl0: str = Form(default=None),
):
    # En WhatsApp, From viene como 'whatsapp:+52155...'
    user_phone = From
    
    # Capturar imagen si existe
    image_urls = [MediaUrl0] if MediaUrl0 else None
    
    async def whatsapp_reply(text: str, filepath: str | None = None):
        # A diferencia de Discord, Twilio requiere URLs públicas para adjuntos, 
        # así que enviar el archivo local PDF directamente por Twilio no funcionará sin S3.
        # Por ahora lo mandaremos como texto, o enviaremos enlaces mock.
        if filepath:
            text += "\n\n📄 [El documento PDF se generó, pero en WhatsApp requieres un servidor público para enviarlo]. Usa Discord para bajarlo directamente."
        await send_whatsapp_async(user_phone, text)

    # background task para no trabar el webhook
    background_tasks.add_task(
        handle_incoming_message,
        platform="whatsapp",
        platform_id=user_phone,
        text=Body,
        response_func=whatsapp_reply,
        image_urls=image_urls
    )
    
    # Twilio espera un HTTP 200 rápido
    return str(MessagingResponse())
