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
                "USA ESTA HERRAMIENTA SOLO si el usuario pregunta explícitamente dónde ir, "
                "pide la dirección de un módulo, horarios o cómo llegar. "
                "NO LA USES para saludar ni para dar información general."
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
    },
    {
        "type": "function",
        "function": {
            "name": "investigar_en_web",
            "description": (
                "USA ESTA HERRAMIENTA si el usuario pregunta algo sobre trámites, leyes, "
                "costos actuales o noticias de gobierno que NO estén en tu conocimiento oficial. "
                "Te permite buscar en Google/Internet en tiempo real."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La búsqueda específica (Ej: 'costo refrendo CDMX 2026').",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "leer_pagina_web",
            "description": (
                "USA ESTA HERRAMIENTA si tienes una URL específica de un portal de gobierno "
                "o noticia y necesitas leer su contenido completo para dar una respuesta precisa."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "La URL completa de la página a leer.",
                    }
                },
                "required": ["url"],
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
    system_prompt_template = (
        "Eres AutoTrámite MX, un asistente inteligente y amigable experto en procesos vehiculares en México. "
        "Tu prioridad es ser útil, pero también humano. SALUDA siempre amablemente y ten una conversación natural ante todo."
        "\n\nREGLAS DE TONO:\n"
        "- Sé empático y servicial. Puedes hacer 'small talk' (charlar un poco) antes de dar datos técnicos.\n"
        "- Si el usuario solo dice 'Hola', responde con un saludo cálido y pregúntale cómo ha estado su día o en qué puedes servirle.\n"
        "\n\n[CONOCIMIENTO OFICIAL]\n{rag_context}\n\n"
        "### REGLAS DE VISIÓN (OCR):\n"
        "1. Si envían foto de Tarjeta de Circulación, extrae PLACA, MARCA, MODELO y VIN.\n"
        "2. Confirma los datos con alegría: '¡Perfecto! Ya leí tus placas: [PLACA]'.\n\n"
        "### REGLAS DE AGENTE:\n"
        "1. NO uses herramientas de inmediato si el usuario solo está saludando.\n"
        "2. Llama a `consultar_adeudos` solo si el usuario quiere saber sus deudas.\n"
        "3. Llama a `generar_checklist` o `buscar_modulos` cuando haya un trámite en curso.\n"
        "4. Llama a `investigar_en_web` SI el usuario te pregunta por algo que no conoces, como "
        "costos específicos de 2026, nuevas leyes o noticias de gobierno locales.\n"
        "5. Formatea con Markdown y emojis para que el chat se vea profesional pero cercano."
    )
    system_prompt = system_prompt_template.format(rag_context=rag_context)

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
        content_array: list[dict] = [{"type": "text", "text": user_message}]
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
