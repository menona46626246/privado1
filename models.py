from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime, timezone


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str = Field(
        index=True, description="Plataforma de origen (whatsapp o discord)"
    )
    platform_id: str = Field(
        index=True, description="ID único de usuario en la plataforma"
    )
    default_state: Optional[str] = Field(
        default=None, description="Estado predeterminado del usuario, ej. CDMX"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Vehicle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    placa: str = Field(description="Placa del vehículo")
    alias: Optional[str] = Field(default=None, description="Ej. Mi Jetta, Moto")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))



class Interaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user_message: str
    bot_response: str
    intent_detected: Optional[str] = Field(
        default=None,
        description="La intención detectada por el LLM (ej. multas)"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

class Reminder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    placa: str
    fecha_aviso: str = Field(description="Ejemplo: '2026-05-01'")
    motivo: str = Field(description="Ejemplo: 'Verificación Vehicular', 'Pago de Tenencia'")
    enviado: bool = Field(default=False)
