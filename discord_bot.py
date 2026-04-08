import discord
from discord.ext import tasks
import logging
from config import settings
from chat_controller import handle_incoming_message
from database import create_db_and_tables

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configuración de Intents (Permisos)
intents = discord.Intents.default()
intents.message_content = True  # Requerido para leer el texto de los mensajes

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    logger.info("==========================================")
    logger.info(" AutoTrámite MX - Discord Bot is ONLINE")
    logger.info(" Logged as: %s", client.user)
    logger.info("==========================================")
    # Aseguramos que las tablas existan
    create_db_and_tables()
    
    # Iniciar los recordatorios automáticos
    if not daily_reminders.is_running():
        daily_reminders.start()

@tasks.loop(hours=24)
async def daily_reminders():
    # En un entorno real, aquí se consultaría la base de datos `Reminder`
    # y se enviarían DMs a los usuarios whose `fecha_aviso` is today.
    logger.info("[Reminders] Ejecutando verificación de recordatorios...")
    pass

@client.event
async def on_message(message: discord.Message):
    # Ignorar mensajes del propio bot
    if message.author == client.user:
        return

    # Solo responder a mensajes directos (DM) o cuando mencionan al bot
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mention = client.user in message.mentions

    if is_dm or is_mention:
        logger.info(
            "[Discord] Mensaje de %s (ID: %s): %s",
            message.author.name,
            message.author.id,
            message.content[:50],
        )

        # Definimos la función de respuesta específica para Discord
        async def discord_reply(text: str, filepath: str | None = None):
            # Crear un Embed premium para la respuesta
            embed = discord.Embed(
                description=text[:4000],
                color=discord.Color.blue()
            )
            embed.set_author(name="AutoTrámite MX", icon_url=client.user.avatar.url if client.user and client.user.avatar else None)
            
            view = None
            file = None
            
            if filepath:
                file = discord.File(filepath)
            
            # Si es el onboarding o pide el estado, mostrar menú desplegable
            if "¿En qué Estado habitas?" in text or "indica tu estado" in text:
                view = discord.ui.View()
                select: discord.ui.Select = discord.ui.Select(
                    placeholder="Elige tu Estado...",
                    options=[
                        discord.SelectOption(label="CDMX", description="Ciudad de México", emoji="🏙️"),
                        discord.SelectOption(label="Monterrey", description="Nuevo León", emoji="⛰️"),
                        discord.SelectOption(label="Juárez", description="Cd. Juárez / Chihuahua", emoji="🏜️"),
                        discord.SelectOption(label="Jalisco", description="Guadalajara y municipios", emoji="🤠"),
                    ]
                )
                
                async def select_callback(interaction: discord.Interaction):
                    await interaction.response.send_message(f"Hecho. Has seleccionado {select.values[0]}.", ephemeral=True)
                    # Simular el envío del mensaje por parte del usuario para que el controlador lo atrape
                    await handle_incoming_message(
                        platform="discord",
                        platform_id=str(interaction.user.id),
                        text=select.values[0],
                        response_func=discord_reply,
                    )
                    
                select.callback = select_callback # type: ignore[method-assign]
                view.add_item(select)

            # Enviar el embed con la vista (si aplica) y el archivo (PDF)
            if len(text) > 4000:
                # Si excede el límite del embed, fallback a mensajes normales
                chunks = [text[i:i + 1950] for i in range(0, len(text), 1950)]
                for idx, chunk in enumerate(chunks):
                    send_kwargs = {"content": chunk}
                    if file and idx == 0:
                        send_kwargs["file"] = file
                    await message.channel.send(**send_kwargs)
            else:
                send_kwargs = {"embed": embed}
                if view:
                    send_kwargs["view"] = view
                if file:
                    send_kwargs["file"] = file
                await message.channel.send(**send_kwargs)


        # Limpiar el texto si es mención
        clean_text = message.content
        if is_mention and client.user:
            clean_text = clean_text.replace(f"<@{client.user.id}>", "").strip()
            clean_text = clean_text.replace(f"<@!{client.user.id}>", "").strip()

        # Extraer URLs de imágenes
        image_urls = [attachment.url for attachment in message.attachments if attachment.content_type and attachment.content_type.startswith("image/")]

        # Enviar al cerebro procesador
        try:
            await handle_incoming_message(
                platform="discord",
                platform_id=str(message.author.id),
                text=clean_text or "hola",
                response_func=discord_reply,
                image_urls=image_urls if image_urls else None
            )
        except Exception as e:
            logger.error("Error procesando mensaje en Discord: %s", e, exc_info=True)
            await message.channel.send(
                "❌ Lo siento, tuve un error interno. Intenta de nuevo más tarde."
            )


if __name__ == "__main__":
    if not settings.discord_token:
        logger.error("No se encontró DISCORD_TOKEN en la configuración.")
    else:
        client.run(settings.discord_token)
