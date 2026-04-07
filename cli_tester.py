import asyncio
import logging

from chat_controller import handle_incoming_message
from database import create_db_and_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    print("===========================================")
    print(" WhatsApp Simulator - AutoTrámite MX (CLI)")
    print("===========================================")
    logger.info("Iniciando motores (RAG + SQLite + Gemini)...")
    create_db_and_tables()
    logger.info("¡Motores listos!")

    mi_numero = "whatsapp:+525551234567"
    print(f"\n📱 Eres el usuario con número: {mi_numero}")
    print("💡 Escribe 'salir' para terminar la simulación.\n")

    while True:
        try:
            mensaje = input("Tú (WhatsApp): ")
            if mensaje.lower() in ["salir", "exit", "quit"]:
                print("Cerrando simulador...")
                break

            async def reply_func(reply_text: str, filepath: str | None = None):
                # En el CLI simplemente imprimimos
                print(f"🤖 Bot: {reply_text}")
                if filepath:
                    print(f"📎 Archivo generado: {filepath}")

            # Pasamos el mensaje al cerebro como si hubiera llegado por Twilio
            await handle_incoming_message(
                platform="whatsapp",
                platform_id=mi_numero,
                text=mensaje,
                response_func=reply_func,
            )
            print("-" * 40)

        except KeyboardInterrupt:
            print("\nCerrando simulador...")
            break
        except Exception as e:
            logger.error("Error grave en simulador: %s", e, exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
