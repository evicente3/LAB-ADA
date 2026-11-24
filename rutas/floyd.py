"""
floyd.py - Algoritmo de Floyd-Warshall (Programación Dinámica).
Responsable: Integrante B
"""

from math import inf
from typing import Dict, List, Tuple, Optional

# (origen, destino, tiempo_base_h, factor_estado)
ARISTAS = [
    ("Arequipa", "Mollendo", 2.0, 1.1),  # 2.2 horas
    ("Arequipa", "Moquegua", 3.5, 1.0),  # 3.5 horas
    ("Moquegua", "Ilo", 1.3, 1.0),       # 1.3 horas
]


def _crear_grafo(lista_aristas=None):
    aristas_usar = lista_aristas if lista_aristas is not None else ARISTAS
    ciudades = sorted({
        ciudad
        for origen, destino, _, _ in aristas_usar
        for ciudad in (origen, destino)
    })
    indices = {ciudad: i for i, ciudad in enumerate(ciudades)}
    n = len(ciudades)

    distancias = [[inf] * n for _ in range(n)]
    siguiente = [[None] * n for _ in range(n)]

    for i in range(n):
        distancias[i][i] = 0.0
        siguiente[i][i] = i

    for origen, destino, tiempo, factor in aristas_usar:
        i = indices[origen]
        j = indices[destino]
        costo = round(tiempo * factor, 2)

        if costo < distancias[i][j]:
            distancias[i][j] = costo
            siguiente[i][j] = j

        if costo < distancias[j][i]:
            distancias[j][i] = costo
            siguiente[j][i] = i

    # Floyd–Warshall: O(V^3)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                nuevo_costo = distancias[i][k] + distancias[k][j]
                if nuevo_costo < distancias[i][j]:
                    distancias[i][j] = nuevo_costo
                    siguiente[i][j] = siguiente[i][k]

    return ciudades, indices, distancias, siguiente


def floyd_warshall(origen, destino, lista_aristas=None):
    """
    Retorna (costo, ruta) para el camino más corto entre dos ciudades.
    Retorna (inf, []) si no existe ruta.
    """
    ciudades, indices, distancias, siguiente = _crear_grafo(lista_aristas)

    if origen not in indices or destino not in indices:
        return inf, []

    i = indices[origen]
    j = indices[destino]

    if siguiente[i][j] is None:
        return inf, []

    ruta = [origen]
    actual = i

    while actual != j:
        actual = siguiente[actual][j]
        ruta.append(ciudades[actual])

    return round(distancias[i][j], 2), ruta


def floyd_warshall_matriz(nodos: List[str], aristas: List[Tuple]):
    """
    Calcula la matriz completa de distancias mínimas y transiciones.
    Retorna: (dist_dict, next_dict)
    """
    dist: Dict[str, Dict[str, float]] = {u: {v: float('inf') for v in nodos} for u in nodos}
    next_node: Dict[str, Dict[str, Optional[str]]] = {u: {v: None for v in nodos} for u in nodos}

    for u in nodos:
        dist[u][u] = 0.0
        next_node[u][u] = u

    for item in aristas:
        if len(item) == 4:
            u, v, tiempo, factor = item
            peso = round(tiempo * factor, 2)
        else:
            u, v, peso = item

        if u in dist and v in dist[u] and peso < dist[u][v]:
            dist[u][v] = peso
            next_node[u][v] = v
        if v in dist and u in dist[v] and peso < dist[v][u]:
            dist[v][u] = peso
            next_node[v][u] = u

    for k in nodos:
        for i in nodos:
            for j in nodos:
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next_node[i][j] = next_node[i][k]

    return dist, next_node


def reconstruir_camino_floyd(u: str, v: str, next_node: Dict[str, Dict[str, Optional[str]]]) -> List[str]:
    """Reconstruye el camino entre u y v."""
    if u not in next_node or v not in next_node[u] or next_node[u][v] is None:
        return []
    camino = [u]
    actual = u
    while actual != v:
        actual = next_node[actual][v]
        if actual is None:
            return []
        camino.append(actual)
    return camino
