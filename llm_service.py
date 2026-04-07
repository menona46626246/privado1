import json
import logging
from typing import Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from config import settings
from models import Interaction

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.groq_api_key or settings.openrouter_api_key,
)

MODEL = settings.llm_model

# Definimos nuestras herramientas del Agente (Function Calling)
TOOLS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "consultar_adeudos",
            "description": (
                "Busca directamente en las plataformas del gobierno si la placa "
                "proporcionada tiene multas vehiculares o adeudos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "placa": {
                        "type": "string",
                        "description": "El número de placa del vehículo.",
                    }
                },
                "required": ["placa"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generar_checklist",
            "description": (
                "Genera un archivo PDF con la lista de requisitos para que el usuario lo pueda imprimir. "
                "USA ESTA HERRAMIENTA si notas que el usuario pide explícitamente una lista, un PDF, o quiere ir al módulo preparado."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {
                        "type": "string",
                        "description": "El título del trámite (Ej. 'Alta de Placas Nuevo León').",
                    },
                    "requisitos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Un arreglo con cada uno de los requisitos y documentos necesarios.",
                    }
                },
                "required": ["titulo", "requisitos"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_modulos",
            "description": (
                "Obtiene las ubicaciones oficiales (dirección y Google Maps) de oficinas "
                "de trámites vehiculares, licencias y recaudación en un estado."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "estado": {
                        "type": "string",
                        "description": "El estado de México (CDMX, Chihuahua, Nuevo Leon, Jalisco).",
                    }
                },
                "required": [],
            },
        },
    }
]



async def generate_agent_response(
    user_message: str, rag_context: str, history: list[Interaction] | None = None, image_urls: list[str] | None = None
) -> tuple[Optional[str], Optional[dict]]:
    """
    Función central del Agente. Evalúa el RAG, el contexto y decide si responder
    directamente o invocar una herramienta.
    """
    system_prompt = (
        "Eres un agente legal experto en trámites vehiculares en México. "
        "Tu tarea principal es asistir al usuario usando SÓLO el conocimiento proporcionado. "
        "NO INVENTES LEYES NI COSTOS. "
        f"\n\n[CONOCIMIENTO OFICIAL]\n{rag_context}\n\n"
        "REGLAS:\n"
        "1. Usa las herramientas SÓLO cuando sea estrictamente necesario:\n"
        "   - Llama a `consultar_adeudos` SÓLO si el usuario indicó explícitamente pagar o consultar deudas, y tienes la placa. Y no la llames si ya la llamaste en este turno.\n"
        "   - PROHIBICIÓN: Si no tienes la placa, NO INVENTES una (ej. 'NOPROPORCIONADA'). Simplemente pide la placa al usuario en tu respuesta de texto.\n"
        "   - Llama a `generar_checklist` SÓLO y EXCLUSIVAMENTE cuando el usuario pide explícitamente una lista para imprimir, descargar, un PDF o una guía paso a paso para el módulo.\n"
        "   - Llama a `buscar_modulos` SI el usuario pregunta dónde ir, pide la dirección del módulo, horarios o cómo llegar a pagar/tramitar.\n"
        "2. Si el usuario envía una imagen, analízala con cuidado, extrae placas, folios de multa o detalles y actua conforme al trámite que pida.\n"
        "3. Si faltan datos (ej. el estado o la placa para una multa), pídeselos antes de usar herramientas.\n"
        "4. Tus respuestas deben ser MUY concisas y formateadas en Markdown."
    )

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": system_prompt}
    ]

    # Inyectar historial
    if history:
        for interaction in history:
            messages.append({"role": "user", "content": interaction.user_message})
            if interaction.bot_response:
                messages.append({"role": "assistant", "content": interaction.bot_response})

    # Mensaje actual (puede ser texto o texto + fotos)
    if image_urls:
        content_array = [{"type": "text", "text": user_message}]
        for url in image_urls:
            content_array.append({
                "type": "image_url",
                "image_url": {"url": url}
            })
        messages.append({"role": "user", "content": content_array})
        # Forzamos modelo de visión
        current_model = "llama-3.2-11b-vision-preview" 
    else:
        messages.append({"role": "user", "content": user_message})
        current_model = MODEL

    try:
        response = await client.chat.completions.create(
            model=current_model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.0
        )

        message = response.choices[0].message

        # Si el modelo determinó que la mejor acción es extraer datos en vivo
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            if tool_call.type == "function":
                function_args = json.loads(tool_call.function.arguments)
                logger.info("Tool call detectado: %s(%s)", tool_call.function.name, function_args)
                return None, {"name": tool_call.function.name, "args": function_args}

        return message.content, None

    except Exception as e:
        logger.error("Error evaluando el modelo: %s", e, exc_info=True)
        return "Lo lamento, mis servidores están intermitentes. Intenta en 5 minutos.", None


async def generate_final_response_after_tool(tool_result: dict) -> str:
    """Envía los datos json crudos del scraper y genera lenguaje natural para el usuario."""
    system_prompt = (
        "Eres AutoTramite MX. El sistema acaba de consultar las multas del usuario "
        "en la base de datos gubernamental y obtuvo este JSON. Transfórmalo a un "
        "mensaje amable y amigable nativo para WhatsApp (bullet points, emojis, "
        "monto total de adeudo si hay). "
        "SI EL JSON CONTIENE 'link_pago_oficial', incluye AL FINAL DE TU MENSAJE ese link hipervinculado pidiendo al usuario que puede pagarlo ahí directamente."
    )

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"El scraper arrojó estos resultados: {json.dumps(tool_result)}"
            ),
        },
    ]

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3
        )
        content = response.choices[0].message.content
        return content if content else "Lo siento, no pude procesar la respuesta."
    except Exception as e:
        logger.error("Error formateando resultado de herramienta: %s", e)
        return (
            f"Tus resultados llegaron pero no pude formatearlos bien. "
            f"El adeudo crudo es de: {tool_result.get('deuda_total_mxn')} MXN."
        )
