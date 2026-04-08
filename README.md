# AutoTrámite MX - AI Assistant (Startup V2.0) 🚗🤖

Este es un asistente inteligente omnicanal diseñado para automatizar la gestión de trámites vehiculares, multas y asesoría legal en México (CDMX, Chihuahua/Juárez, Nuevo León y Jalisco).

---

## 🧭 ¿Qué debe saber otra IA o Desarrollador sobre este proyecto?

Este proyecto ha evolucionado de un simple chatbot a una arquitectura de **Agente Autónomo** con capacidades multimodales.

### 1. Arquitectura del Cerebro
- **Motor de IA (LLM):** Utilizamos **Llama 3.3 70B** a través de **Groq** para una respuesta ultra-rápida.
- **Memoria Contextual (RAG):** El bot no inventa leyes. Consulta una base de datos vectorial (**ChromaDB**) que contiene fragmentos de los reglamentos de tránsito reales (archivos en `/data`).
- **Controlador Central:** Todo el flujo pasa por `chat_controller.py`. Este archivo decide si responder usando conocimiento (RAG), o si el usuario necesita invocar una herramienta (Scraping/PDF/Visión).

### 2. Capacidades Omni-Plataforma
- **Discord:** Un bot nativo (`discord_bot.py`) con interfaces premium (Embeds y Menús desplegables).
- **WhatsApp:** Un servidor **FastAPI** (`main.py`) que recibe webhooks de **Twilio**. Ambos comparten el controlador central para mantener la misma "personalidad" y memoria.

### 3. Funcionalidades Premium (Tools)
- **IA Visión:** Capacidad para procesar imágenes (`image_urls`) usando **Llama 3.2 Vision**. Puede extraer placas de fotos de tarjetas de circulación.
- **Real-Time Scraping:** Usa **Playwright** para navegar por portales de finanzas del gobierno y capturar adeudos reales. 
- **Generación de Documentos:** Crea archivos PDF al vuelo usando la librería `fpdf2`.
- **Sistema de Garage:** Base de datos relacional que permite a un usuario registrar múltiples vehículos (`models.Vehicle`).
- **Recordatorios:** Engine proactivo (`@tasks.loop`) que envía alertas de vencimientos de verificación o tenencia.

### 4. Despliegue y DevOps
- **Contenedores:** El proyecto está dockerizado. El `Dockerfile` pre-instala navegadores Chromium para que el scraping funcione en cualquier lugar.
- **Nube:** Está configurado para correr en **Amazon AWS (EC2)** usando **Docker Compose**.
- **Base de Datos:** Utiliza **SQLite** con **SQLModel** (SQLAlchemy) para una gestión de datos rápida y robusta.

---

## 🛠️ Cómo arrancar (Quick Start)

### En Local:
1. Asegúrate de tener un entorno virtual: `python -m venv venv`.
2. Instala dependencias: `pip install -r requirements.txt`.
3. Instala navegadores de Playwright: `playwright install chromium`.
4. Ejecuta: `python discord_bot.py` o `uvicorn main:app --reload`.

### En AWS (Producción):
1. Asegura tener abiertos los puertos 80, 443 y 22.
2. Comandos:
   ```bash
   git pull
   sudo docker compose up -d --build
   ```

---

## 📂 Estructura de Archivos Clave
- `chat_controller.py`: El cerebro que decide qué hacer.
- `llm_service.py`: Conexión con Groq y definición de herramientas (Prompt Engineering).
- `models.py`: Esquema de la base de datos (Usuarios, Vehículos, Recordatorios).
- `pdf_service.py`: Lógica de creación de checklists descargables.
- `scraper_service.py`: Extracción automatizada de multas en portales web.
- `seed_rag.py`: Script para cargar/actualizar las leyes en la base de datos vectorial.

---

### Mantenimiento por otra IA:
Si eres una IA trabajando en este proyecto, mantén siempre la consistencia en el `chat_controller.py` y asegúrate de que cualquier nueva ley sea añadida a un archivo `.txt` en `/data` y luego indexada con `seed_rag.py`. **No modifiques el flujo de Docker sin actualizar el Dockerfile de Playwright.**
