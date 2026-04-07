# AutoTrámite MX

Chatbot especializado en trámites vehiculares en México utilizando tecnología RAG (Retrieval-Augmented Generation) y web scraping para proporcionar respuestas precisas y confiables en WhatsApp.

## Requisitos Previos
- **Python 3.9+** instalado en el sistema.

---

## 🛠️ Guía Rápida de Instalación (Windows PowerShell)

Sigue estos pasos en tu terminal (asegúrate de estar dentro de la carpeta `AutoTrámiteMx`):

### 1. Crear el Entorno Virtual
```powershell
python -m venv venv
```

### 2. Activar el Entorno Virtual
Para activar el entorno donde se instalarán las librerías, ejecuta:
```powershell
.\venv\Scripts\Activate.ps1
```
*(Nota: Sabrás que funcionó porque aparecerá un `(venv)` al inicio de tu línea de comandos).*

### 3. Instalar las Dependencias
Todo nuestro stack de IA (ChromaDB) y Backend (FastAPI, SQLModel) se instala con:
```powershell
pip install -r requirements.txt
```

---

## 🚀 Cómo Probar el Proyecto

Tenemos dos partes fundamentales que hemos construido hasta ahora para probar:

### Prueba A: Ejecutar el Cerebro RAG (Motor de Búsqueda Semántica)
Para probar que la Base de Datos Vectorial lee los requerimientos gubernamentales correctamente y evita alucinaciones, ejecuta:
```powershell
python rag_poc.py
```
**¿Qué hace esto?** 
Agarra el texto escrito en `data/cdmx_tramites_dummy.txt`, lo convierte en vectores y te mostrará la respuesta exacta ante preguntas como *"¿Cuánto cuesta dar de alta placas?"*.

### Prueba B: Simulador CLI (Consola)
Si quieres probar el bot sin configurar Twilio ni Discord, usa el simulador interactivo:
```powershell
python cli_tester.py
```

### Prueba C: Ejecutar el Servidor API (WhatsApp/Twilio)
Levanta el backend para recibir webhooks de Twilio:
```powershell
fastapi dev main.py
```
Accede a `http://127.0.0.1:8000/docs` para la documentación Swagger.

### Prueba D: Ejecutar el Bot de Discord
Si ya configuraste tu `DISCORD_TOKEN` en el archivo `.env`, inicia el bot:
```powershell
python discord_bot.py
```
**Nota:** Asegúrate de que tu bot tenga activado el Intent de **Message Content** en el [Discord Developer Portal](https://discord.com/developers/applications).
