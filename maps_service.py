from typing import Dict, List, Optional

# Directorio de módulos principales mapeados por estado.
MODULOS_UBICACIONES: Dict[str, List[Dict[str, str]]] = {
    "CDMX": [
        {
            "nombre": "Módulo SEMOVI Central",
            "direccion": "Av. Insurgentes Sur 263, Roma Nte, Cuauhtémoc, 06700 CDMX",
            "maps_url": "https://maps.app.goo.gl/3fR9k6p5fPzZ2vR57"
        },
        {
            "nombre": "Tesorería Exprés (Plaza de las Estrellas)",
            "direccion": "Cto. Interior Melchor Ocampo 193, Verónica Anzúres, Miguel Hidalgo, 11300 CDMX",
            "maps_url": "https://maps.app.goo.gl/kX7R4V6p69fVnP869"
        }
    ],
    "CHIHUAHUA": [
        {
            "nombre": "Recaudación de Rentas (Pueblito Mexicano)",
            "direccion": "Av. Lincoln 1320, Margaritas, 32315 Cd Juárez, Chih.",
            "maps_url": "https://maps.app.goo.gl/j4Y8fPnP869kX7R4V"
        },
        {
            "nombre": "Módulo Recaudación (Galerías Tec)",
            "direccion": "Av. Tecnológico 1770, Fuentes del Valle, 32500 Cd Juárez, Chih.",
            "maps_url": "https://maps.app.goo.gl/VnP869kX7R4V3fR9k"
        }
    ],
    "NUEVO LEON": [
        {
            "nombre": "Instituto de Control Vehicular (Pabellón Ciudadano)",
            "direccion": "Washington 2000 Ote, Centro, 64000 Monterrey, N.L.",
            "maps_url": "https://maps.app.goo.gl/69fVnP869kX7R4V3f"
        }
    ],
    "JALISCO": [
        {
            "nombre": "Módulo de Licencias (Plaza las Torres)",
            "direccion": "Av. 8 de Julio 1897, Morelos, 44910 Guadalajara, Jal.",
            "maps_url": "https://maps.app.goo.gl/5fPzZ2vR57kX7R4V3"
        }
    ]
}

def get_modulos_por_estado(estado: str) -> Optional[List[Dict[str, str]]]:
    """Retorna la lista de módulos para el estado proporcionado."""
    estado_upper = estado.upper().strip()
    # Limpieza básica de nombres de estado
    if "CIUDAD DE MEXICO" in estado_upper or "CDMX" in estado_upper:
        return MODULOS_UBICACIONES.get("CDMX")
    if "CHIHUAHUA" in estado_upper or "JUAREZ" in estado_upper:
        return MODULOS_UBICACIONES.get("CHIHUAHUA")
    if "NUEVO LEON" in estado_upper or "MONTERREY" in estado_upper:
        return MODULOS_UBICACIONES.get("NUEVO LEON")
    if "JALISCO" in estado_upper or "GUADALAJARA" in estado_upper:
        return MODULOS_UBICACIONES.get("JALISCO")
    
    return None
