from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    groq_api_key: str = ""
    openrouter_api_key: str = ""  # Mantener por compatibilidad si se desea volver
    llm_base_url: str = "https://api.groq.com/openai/v1"
    
    database_url: str = "sqlite:///./autotramite.db"
    
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = "whatsapp:+14155238886"
    
    discord_token: str = ""
    discord_public_key: str = ""
    
    sql_debug: bool = False
    llm_model: str = "llama-3.3-70b-versatile"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
