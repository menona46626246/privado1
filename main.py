import logging
import os
from fastapi import FastAPI, Form, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from twilio.twiml.messaging_response import MessagingResponse
from chat_controller import handle_incoming_message
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoTrámite webhooks")

@app.on_event("startup")
async def on_startup():
    os.makedirs("output", exist_ok=True)
    app.mount("/archivos", StaticFiles(directory="output"), name="archivos")
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
        from typing import Any
        kwargs: dict[str, Any] = {
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
    request: Request,
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
        media_url = None
        if filepath:
            filename = os.path.basename(filepath)
            media_url = f"{str(request.base_url).rstrip('/')}/archivos/{filename}"
            text += f"\n\n📄 Tu documento está listo: {media_url}"
        await send_whatsapp_async(user_phone, text, media_url=media_url)

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

@app.post("/admin/actualizar-leyes")
async def admin_actualizar_leyes(background_tasks: BackgroundTasks):
    from seed_rag import actualizar_chroma_db
    background_tasks.add_task(actualizar_chroma_db)
    return {"status": "Actualización de BD Vectorial iniciada en segundo plano."}
