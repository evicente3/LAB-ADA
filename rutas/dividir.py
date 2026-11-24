"""
dividir.py - Estrategia Divide et Impera para partición de la red vial.
Divide la red en subredes independientes (sectores) y extrae las conexiones
entre nodos frontera (ciudades puente) para reducir la complejidad global.
"""

from typing import Dict, List
from rutas.datos import SECTORES, CIUDADES_PUENTE, RED_VIAL, AristaCarretera


def obtener_subgrafo_sector(nombre_sector: str) -> Dict[str, List[AristaCarretera]]:
    """
    Extrae el subgrafo correspondiente a un sector geográfico específico.
    Solo incluye aristas cuyos destinos permanezcan dentro del mismo sector.
    """
    ciudades_sector = set(SECTORES.get(nombre_sector, []))
    subgrafo = {}
    
    for ciudad in ciudades_sector:
        if ciudad in RED_VIAL:
            aristas_internas = [
                arista for arista in RED_VIAL[ciudad]
                if arista.destino in ciudades_sector
            ]
            subgrafo[ciudad] = aristas_internas
            
    return subgrafo


def obtener_aristas_intersectoriales() -> List[tuple]:
    """
    Identifica las carreteras que conectan ciudades puente entre distintos sectores.
    Retorna lista de tuplas: (origen, destino, peso_efectivo)
    """
    conexiones = []
    puentes_set = set(CIUDADES_PUENTE)
    
    for origen in puentes_set:
        for arista in RED_VIAL.get(origen, []):
            if arista.destino in puentes_set:
                conexiones.append((origen, arista.destino, arista.peso_efectivo))
                
    return conexiones
