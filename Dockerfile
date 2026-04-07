# Usamos una imagen oficial de Python 3.12 slim como base
FROM python:3.12-slim

# Evita que Python escriba archivos .pyc en el disco y fuerza que el stdout y stderr no usen bufer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Configuramos el directorio de trabajo del contenedor
WORKDIR /app

# Instalamos dependencias básicas del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiamos primero el archivo de requerimientos para aprovechar el caché de Docker
COPY requirements.txt .

# Instalamos las dependencias del proyecto (incluye playwright)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Instalamos explícitamente los navegadores de Playwright del sistema junto con sus dependencias OS
RUN playwright install --with-deps chromium

# Copiamos el resto del código del bot dentro de la imagen
COPY . .

# Exponemos el puerto 8000 para la API (FastAPI webhook para WhatsApp)
EXPOSE 8000

# Creamos un pequeño script de inicio (entrypoint) que corra el discord_bot y main webhook si es necesario
# Por defecto lanzaremos el backend de FastAPI con Uvicorn (WhatsApp webhooks)
CMD ["python", "discord_bot.py"]
