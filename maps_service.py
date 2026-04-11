from typing import Dict, List, Optional

# Directorio de módulos principales mapeados por estado.
MODULOS_UBICACIONES: Dict[str, List[Dict[str, str]]] = {
    "CDMX": [
        {
            "nombre": "Módulo SEMOVI Central",
            "direccion": "Av. Insurgentes Sur 263, Roma Nte, Cuauhtémoc, 06700 CDMX"
        },
        {
            "nombre": "Tesorería Exprés (Plaza de las Estrellas)",
            "direccion": "Cto. Interior Melchor Ocampo 193, Verónica Anzúres, Miguel Hidalgo, 11300 CDMX"
        }
    ],
    "CHIHUAHUA": [
        {
            "nombre": "Recaudación de Rentas (Pueblito Mexicano)",
            "direccion": "Av. Lincoln 1320, Margaritas, 32315 Cd Juárez, Chih."
        },
        {
            "nombre": "Módulo Recaudación (Galerías Tec)",
            "direccion": "Av. Tecnológico 1770, Fuentes del Valle, 32500 Cd Juárez, Chih."
        }
    ],
    "NUEVO LEON": [
        {
            "nombre": "Instituto de Control Vehicular (Pabellón Ciudadano)",
            "direccion": "Washington 2000 Ote, Centro, 64000 Monterrey, N.L."
        }
    ],
    "JALISCO": [
        {
            "nombre": "Módulo de Licencias (Plaza las Torres)",
            "direccion": "Av. 8 de Julio 1897, Morelos, 44910 Guadalajara, Jal."
        }
    ]
}

import urllib.parse

def _procesar_modulos(modulos: Optional[List[Dict[str, str]]]) -> Optional[List[Dict[str, str]]]:
    if not modulos:
        return None
    
    procesados = []
    for mod in modulos:
        mod_copy = dict(mod)
        query = urllib.parse.quote(mod_copy["direccion"])
        mod_copy["maps_url"] = f"https://www.google.com/maps/search/?api=1&query={query}"
        procesados.append(mod_copy)
    return procesados

def get_modulos_por_estado(estado: str) -> Optional[List[Dict[str, str]]]:
    """Retorna la lista de módulos para el estado proporcionado con URL de mapa correcta."""
    estado_upper = estado.upper().strip().replace("_", " ")
    # Limpieza básica de nombres de estado
    if "CIUDAD DE MEXICO" in estado_upper or "CDMX" in estado_upper or "EDOMEX" in estado_upper:
        return _procesar_modulos(MODULOS_UBICACIONES.get("CDMX"))
    if "CHIHUAHUA" in estado_upper or "JUAREZ" in estado_upper:
        return _procesar_modulos(MODULOS_UBICACIONES.get("CHIHUAHUA"))
    if "NUEVO LEON" in estado_upper or "MONTERREY" in estado_upper:
        return _procesar_modulos(MODULOS_UBICACIONES.get("NUEVO LEON"))
    if "JALISCO" in estado_upper or "GUADALAJARA" in estado_upper:
        return _procesar_modulos(MODULOS_UBICACIONES.get("JALISCO"))
    
    return None
