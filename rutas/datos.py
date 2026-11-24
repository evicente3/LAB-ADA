"""
datos.py - Definición de la red vial turística del Sur del Perú.
Responsable: Integrante A

Modela las ciudades principales, nodos intermedios y carreteras que conectan
Arequipa, Puno, Cusco y Moquegua, considerando distancia (km), tiempo base (h)
y factor de estado de la vía (asfaltado, afirmado, en mantenimiento).
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class AristaCarretera:
    destino: str
    distancia_km: float
    tiempo_h: float
    estado: str  # 'excelente' (1.0), 'bueno' (1.1), 'regular' (1.3), 'malo' (1.6)

    @property
    def peso_efectivo(self) -> float:
        """Calcula el costo ponderado considerando el estado de la carretera."""
        factores = {
            'excelente': 1.0,
            'bueno': 1.1,
            'regular': 1.3,
            'malo': 1.6
        }
        factor = factores.get(self.estado, 1.2)
        # Costo combinado: tiempo_h ponderado por el estado de la vía
        return round(self.tiempo_h * factor, 2)


# Definición de sectores geográficos (Divide et Impera)
SECTORES = {
    "Sector_Costa_Sur": ["Arequipa", "Mollendo", "Moquegua", "Ilo"],
    "Sector_Altiplano": ["Juliaca", "Puno", "Ilave", "Desaguadero"],
    "Sector_Valle_Sagrado": ["Cusco", "Urubamba", "Ollantaytambo", "Sicuani"]
}

# Nodos frontera / ciudades puente que conectan los sectores
CIUDADES_PUENTE = ["Arequipa", "Puno", "Juliaca", "Sicuani", "Moquegua"]

# Grafo detallado interconectado
RED_VIAL: Dict[str, List[AristaCarretera]] = {
    # Sector Costa Sur
    "Arequipa": [
        AristaCarretera("Mollendo", 126, 2.0, "bueno"),
        AristaCarretera("Moquegua", 220, 3.5, "excelente"),
        AristaCarretera("Juliaca", 270, 5.0, "regular"),  # Conexión intersectorial
    ],
    "Mollendo": [
        AristaCarretera("Arequipa", 126, 2.0, "bueno"),
        AristaCarretera("Ilo", 120, 1.8, "excelente"),
    ],
    "Moquegua": [
        AristaCarretera("Arequipa", 220, 3.5, "excelente"),
        AristaCarretera("Ilo", 95, 1.3, "excelente"),
        AristaCarretera("Puno", 260, 4.5, "regular"),     # Conexión intersectorial
    ],
    "Ilo": [
        AristaCarretera("Mollendo", 120, 1.8, "excelente"),
        AristaCarretera("Moquegua", 95, 1.3, "excelente"),
    ],

    # Sector Altiplano
    "Puno": [
        AristaCarretera("Moquegua", 260, 4.5, "regular"),
        AristaCarretera("Juliaca", 45, 0.8, "bueno"),
        AristaCarretera("Ilave", 55, 1.0, "bueno"),
    ],
    "Juliaca": [
        AristaCarretera("Arequipa", 270, 5.0, "regular"),
        AristaCarretera("Puno", 45, 0.8, "bueno"),
        AristaCarretera("Sicuani", 195, 3.2, "bueno"),   # Conexión intersectorial hacia Cusco
    ],
    "Ilave": [
        AristaCarretera("Puno", 55, 1.0, "bueno"),
        AristaCarretera("Desaguadero", 90, 1.4, "bueno"),
    ],
    "Desaguadero": [
        AristaCarretera("Ilave", 90, 1.4, "bueno"),
    ],

    # Sector Valle Sagrado
    "Sicuani": [
        AristaCarretera("Juliaca", 195, 3.2, "bueno"),
        AristaCarretera("Cusco", 140, 2.8, "excelente"),
    ],
    "Cusco": [
        AristaCarretera("Sicuani", 140, 2.8, "excelente"),
        AristaCarretera("Urubamba", 53, 1.2, "bueno"),
        AristaCarretera("Ollantaytambo", 72, 1.7, "excelente"),
    ],
    "Urubamba": [
        AristaCarretera("Cusco", 53, 1.2, "bueno"),
        AristaCarretera("Ollantaytambo", 20, 0.4, "excelente"),
    ],
    "Ollantaytambo": [
        AristaCarretera("Cusco", 72, 1.7, "excelente"),
        AristaCarretera("Urubamba", 20, 0.4, "excelente"),
    ],
}


def obtener_ciudades() -> List[str]:
    """Retorna la lista de todas las ciudades registradas."""
    return sorted(list(RED_VIAL.keys()))
