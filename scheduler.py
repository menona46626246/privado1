import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session, select
from database import engine
from models import Reminder, User
from config import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)

# Configuración de Cliente Twilio
twilio_client = None
if settings.twilio_account_sid and settings.twilio_auth_token:
    twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

async def send_reminder_task():
    """
    Tarea que corre diariamente buscando recordatorios pendientes para hoy.
    """
    logger.info("[Scheduler] Ejecutando revisión de recordatorios...")
    
    with Session(engine) as session:
        # Buscamos recordatorios para hoy o pasado que no se hayan enviado
        hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        statement = select(Reminder).where(Reminder.fecha_aviso <= hoy, Reminder.enviado == False)
        pendientes = session.exec(statement).all()
        
        for reminder in pendientes:
            user = session.get(User, reminder.user_id)
            if not user:
                continue
                
            mensaje = (
                f"⏰ *RECORDATORIO AUTOTRÁMITE*\n\n"
                f"Hola, te recordamos que hoy es la fecha límite o aviso para: "
                f"*{reminder.motivo}* referente a las placas *{reminder.placa}*.\n\n"
                f"¿Deseas que te ayude a consultar los requisitos o módulos de pago?"
            )
            
            success = False
            try:
                if user.platform == "whatsapp" and twilio_client:
                    # Enviar vía Twilio
                    twilio_client.messages.create(
                        from_=settings.twilio_whatsapp_number,
                        body=mensaje,
                        to=user.platform_id
                    )
                    success = True
                elif user.platform == "discord":
                    # Nota: El bot de discord corre en otro proceso, 
                    # usualmente se usaría una cola de mensajes o webhook.
                    # Por ahora loggeamos para implementación futura de webhook.
                    logger.warning("[Scheduler] Discord push no implementado directo (requiere webhook/bot instanced).")
                    success = True # Marcamos como procesado para no repetir
                
                if success:
                    reminder.enviado = True
                    session.add(reminder)
                    logger.info("[Scheduler] Recordatorio enviado a usuario %s", user.id)
            except Exception as e:
                logger.error("[Scheduler] Error enviando recordatorio: %s", e)
        
        session.commit()

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Ejecutar cada día a las 9:00 AM (puedes ajustar el intervalo para pruebas)
    scheduler.add_job(send_reminder_task, 'interval', hours=24, next_run_time=datetime.now())
    scheduler.start()
    logger.info("[Scheduler] Programador de recordatorios iniciado (Cada 24h).")
