"""
dijkstra.py - Algoritmo Goloso para rutas más cortas locales.
Responsable: Integrante A

Implementa el algoritmo de Dijkstra utilizando una cola de prioridad (heapq)
para optimizar la búsqueda local de caminos mínimos dentro de cada sector.
"""

import heapq
from typing import Dict, List, Tuple, Optional
from rutas.datos import RED_VIAL, AristaCarretera


def dijkstra(origen: str, destino: str, subgrafo: Optional[Dict[str, List[AristaCarretera]]] = None) -> Tuple[float, List[str]]:
    """
    Encuentra el camino de menor costo entre dos ciudades.
    
    Retorna:
        Tuple[float, List[str]]: (costo_minimo, ruta_ciudades)
    """
    grafo = subgrafo if subgrafo is not None else RED_VIAL
    
    if origen not in grafo or destino not in grafo:
        return float('inf'), []

    distancias: Dict[str, float] = {nodo: float('inf') for nodo in grafo}
    padres: Dict[str, Optional[str]] = {nodo: None for nodo in grafo}
    distancias[origen] = 0.0

    # Heap: (costo_acumulado, nodo_actual)
    pq = [(0.0, origen)]

    while pq:
        dist_actual, nodo_actual = heapq.heappop(pq)

        if nodo_actual == destino:
            break

        if dist_actual > distancias[nodo_actual]:
            continue

        for arista in grafo.get(nodo_actual, []):
            vecino = arista.destino
            if vecino not in distancias:
                continue
                
            nuevo_costo = dist_actual + arista.peso_efectivo
            if nuevo_costo < distancias[vecino]:
                distancias[vecino] = nuevo_costo
                padres[vecino] = nodo_actual
                heapq.heappush(pq, (nuevo_costo, vecino))

    if distancias[destino] == float('inf'):
        return float('inf'), []

    # Reconstrucción de la ruta
    ruta = []
    actual = destino
    while actual is not None:
        ruta.append(actual)
        actual = padres[actual]
    ruta.reverse()

    return round(distancias[destino], 2), ruta
