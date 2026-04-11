"""Constantes centralizadas para AutoTrámite MX."""

from enum import Enum


class Estado(str, Enum):
    """Estados soportados por el sistema. El valor se usa como clave en ChromaDB y la BD."""
    CDMX = "CDMX"
    CHIHUAHUA = "Chihuahua"
    NUEVO_LEON = "Nuevo_Leon"
    JALISCO = "Jalisco"


# Mapeo de palabras clave a estados para el onboarding
ESTADO_KEYWORDS: dict[str, Estado] = {
    "cdmx": Estado.CDMX,
    "mexico": Estado.CDMX,
    "ciudad de": Estado.CDMX,
    "edomex": Estado.CDMX,
    "estado de mexico": Estado.CDMX,
    "chihuahua": Estado.CHIHUAHUA,
    "juarez": Estado.CHIHUAHUA,
    "juárez": Estado.CHIHUAHUA,
    "monterrey": Estado.NUEVO_LEON,
    "nuevo leon": Estado.NUEVO_LEON,
    "nuevo león": Estado.NUEVO_LEON,
    "jalisco": Estado.JALISCO,
    "guadalajara": Estado.JALISCO,
    "zapopan": Estado.JALISCO,
}

# Mensajes de confirmación por estado
ESTADO_CONFIRMACIONES: dict[Estado, str] = {
    Estado.CDMX: (
        "✅ ¡Listo! He configurado 'CDMX' en tu perfil. "
        "¿Sobre qué trámite vehicular oficial te gustaría consultar hoy?"
    ),
    Estado.CHIHUAHUA: (
        "✅ ¡Listo! He configurado 'Chihuahua / Cd. Juárez' en tu perfil. "
        "¿De qué trámite vehicular te gustaría conocer los costos y requisitos oficiales?"
    ),
    Estado.NUEVO_LEON: (
        "✅ ¡Listo! He configurado 'Nuevo León / Monterrey' en tu perfil. "
        "¿Qué trámite te interesa consultar al ICV (Instituto de Control Vehicular)?"
    ),
    Estado.JALISCO: (
        "✅ ¡Listo! He configurado 'Jalisco / Guadalajara' en tu perfil. "
        "¿En qué te asesoro el día de hoy?"
    ),
}
