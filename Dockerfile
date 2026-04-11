FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias del sistema necesarias para PostgreSQL y Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar los navegadores de Playwright (solo Chromium) y sus dependencias de sistema
RUN python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache/pip

# Copiar el resto del código
COPY . .

EXPOSE 8000
CMD ["python", "discord_bot.py"]
