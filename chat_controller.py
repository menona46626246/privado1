import logging
from typing import Any, cast, Callable, Coroutine

from sqlmodel import Session, select
from sqlalchemy import desc

from constants import ESTADO_CONFIRMACIONES, ESTADO_KEYWORDS
from database import engine
from llm_service import (
    generate_agent_response,
    generate_final_response_after_tool
)
from models import Interaction, User
from rag_service import get_rag_context
from scraper_service import consultar_adeudos_mock
from alerts_service import notify_critical_error

logger = logging.getLogger(__name__)


async def handle_incoming_message(
    platform: str,
    platform_id: str,
    text: str,
    response_func: Callable[..., Coroutine[Any, Any, Any]],
    image_urls: list[str] | None = None
):
    """
    Controlador principal / Cerebro.
    1. Verifica existencia de usuario.
    2. Modifica el estado según interacciones previas.
    3. Construye Historial.
    4. Llama RAG + LLM (Agente).
    5. Ejecuta Tools si es necesario (ej. Scraping).
    6. Guarda y envía.
    """
    with Session(engine) as session:
        user = session.exec(
            select(User)
            .where(User.platform == platform)
            .where(User.platform_id == platform_id)
        ).first()
        is_new_user = False

        # 1. Onboarding de Flujo Nuevo
        if not user:
            user = User(platform=platform, platform_id=platform_id)
            session.add(user)
            session.commit()
            session.refresh(user)
            is_new_user = True

        # Check if user was correctly created and has an ID
        if user.id is None:
            logger.error(
                "No se pudo crear o recuperar el ID del usuario para %s:%s",
                platform,
                platform_id,
            )
            return

        user_id: int = user.id  # narrowed: int (not None) from this point on

        if is_new_user:
            respuesta_bienvenida = (
                "🤖 ¡Hola! Soy AutoTrámite MX, tu asistente para multas, "
                "altas de placas y tenencias.\n\n"
                "Para poder darte requisitos legales precisos, dime: "
                "**¿En qué Estado habitas?** "
                "(Ej: *CDMX*, *Monterrey*, *Edomex*)."
            )
            await response_func(respuesta_bienvenida)
            _save_interaction(session, user_id, text, respuesta_bienvenida, "onboarding")
            return

        # 2. Configuración de Estado Pendiente
        if not user.default_state:
            texto_limpio = text.lower()
            estado_detectado = None

            for keyword, estado in ESTADO_KEYWORDS.items():
                if keyword in texto_limpio:
                    estado_detectado = estado
                    break

            if estado_detectado:
                user.default_state = estado_detectado.value
                session.add(user)
                session.commit()
                # NOTA: NO HACEMOS RETURN. Continuamos al Agente para que salude humanamente.
            elif not any(k in texto_limpio for k in ["hola", "buen", "hey", "tal"]):
                 # Solo pedir el estado si el mensaje NO es un saludo genérico
                 respuesta_estado = (
                    "⚠️ Me encantaría ayudarte, pero necesito saber en qué estado de México vives (CDMX, Edomex, Nuevo León, Jalisco o Chihuahua) "
                    "para darte información legal exacta."
                 )
                 await response_func(respuesta_estado)
                 _save_interaction(session, user_id, text, respuesta_estado, "set_state")
                 return

        # 3. Flujo Principal RAG y Agente
        historial: list[Interaction] = list(
            session.exec(
                select(Interaction)
                .where(Interaction.user_id == user_id)
                .order_by(desc(cast(Any, Interaction.id)))
                .limit(3)
            ).all()
        )[::-1]

        from models import Vehicle
        
        vehiculos = session.exec(select(Vehicle).where(Vehicle.user_id == user_id)).all()
        vehiculos_texto = ", ".join([v.placa for v in vehiculos]) if vehiculos else "Ninguno"
        
        # Buscar contexto RAG
        context_docs = get_rag_context(
            query=text, state_filter=user.default_state, top_k=2
        )
        
        # Añadimos la info del garage al contexto
        context_docs += f"\n\n[INFO DEL USUARIO] Vehículos guardados en su Garage: {vehiculos_texto}"

        # Consultar al Agente
        try:
            texto_llm, herramienta_solicitada = await generate_agent_response(
                user_message=text, 
                rag_context=context_docs, 
                history=historial,
                image_urls=image_urls
            )
        except Exception as e:
            logger.error("Error generando respuesta del agente: %s", e, exc_info=True)
            notify_critical_error(f"Falla crítica en LLM para usuario {platform_id}: {str(e)}")
            texto_llm = "Lo lamento, mis servidores están intermitentes. Intenta en unos minutos."
            herramienta_solicitada = None

        # --- BUCLE DEL AGENTE (EJECUCIÓN DE HERRAMIENTAS) ---
        filepath_to_send = None

        if herramienta_solicitada:
            if herramienta_solicitada["name"] == "consultar_adeudos":
                placa_raw = herramienta_solicitada["args"].get("placa", "").strip().upper()
                
                # Validación estricta: si no hay placa real, cancelamos
                if not placa_raw or len(placa_raw) < 3 or "PROPORCIONA" in placa_raw or placa_raw == "N/A":
                    texto_llm = "Claro, puedo ayudarte con eso. Solo indícame tu número de placa para realizar la consulta de multas."
                else:
                    placa = placa_raw.replace(" ", "").replace("-", "")

                    # Feedback si tarda
                    mensaje_carga = f"⚙️ *Consultando servidores de finanzas para la placa {placa}. Un momento...*"
                    await response_func(mensaje_carga)

                    # Guardar en Garage si no existe
                    vehiculo_existente = session.exec(select(Vehicle).where(Vehicle.user_id == user_id, Vehicle.placa == placa)).first()
                    if not vehiculo_existente:
                        nuevo_vehiculo = Vehicle(user_id=user_id, placa=placa)
                        session.add(nuevo_vehiculo)
                        session.commit()

                    # Ejecutar Scraping
                    resultados_scraper = await consultar_adeudos_mock(
                        estado=user.default_state or "CDMX", placa=placa
                    )

                    # Redactar resumen
                    texto_llm = await generate_final_response_after_tool(
                        tool_result=resultados_scraper
                    )


            elif herramienta_solicitada["name"] == "generar_checklist":
                from pdf_service import generate_pdf_checklist
                titulo = herramienta_solicitada["args"].get("titulo", "Trámite")
                requisitos = herramienta_solicitada["args"].get("requisitos", [])
                
                # Feedback inicial
                await response_func("🖨️ *Generando tu PDF con los requisitos...*")
                
                # Generar el PDF físicamente
                filepath_to_send = generate_pdf_checklist(titulo, requisitos)
                texto_llm = "¡Aquí tienes tu checklist lista para imprimir! Llévala contigo a tu cita. ¿En qué más te ayudo?"

            elif herramienta_solicitada["name"] == "buscar_modulos":
                from maps_service import get_modulos_por_estado
                estado_consultar = herramienta_solicitada["args"].get("estado") or user.default_state or "CDMX"
                modulos = get_modulos_por_estado(estado_consultar)
                
                if modulos:
                    lista_modulos = "\n\n".join([
                        f"📍 **{m['nombre']}**\n🏠 {m['direccion']}\n🔗 [Ver en Google Maps]({m['maps_url']})" 
                        for m in modulos
                    ])
                    texto_llm = (
                        f"¡Claro! Aquí tienes los módulos de atención más cercanos en **{estado_consultar.upper()}**:\n\n"
                        f"{lista_modulos}\n\n"
                        "Te recomendamos llegar 15 minutos antes de tu cita. ¿Necesitas algo más?"
                    )
                else:
                    texto_llm = (
                        f"Por el momento no tengo el mapa detallado de módulos para **{estado_consultar}**, "
                        "pero puedes consultarlos en el portal oficial de finanzas de tu estado. ¿Deseas que busque otra cosa?"
                    )

        # Envío y Persistencia final
        if texto_llm:
            await response_func(texto_llm, filepath=filepath_to_send)

            intent = "tool_execution" if herramienta_solicitada else "rag_query"
            _save_interaction(session, user_id, text, texto_llm, intent)


def _save_interaction(
    session: Session,
    user_id: int,
    user_message: str,
    bot_response: str,
    intent: str,
):
    """Helper para persistir una interacción de forma consistente."""
    log = Interaction(
        user_id=user_id,
        user_message=user_message,
        bot_response=bot_response,
        intent_detected=intent,
    )
    session.add(log)
    session.commit()
