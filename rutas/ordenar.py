"""
ordenar.py - Algoritmo Mergesort (Divide et Impera).
Responsable: Integrante B

Ordena listas de itinerarios o rutas alternativas según su costo/tiempo ponderado
garantizando una complejidad temporal de O(n log n) y estabilidad.
"""

from typing import List, Dict, Any


def mergesort_rutas(rutas: List[Dict[str, Any]], criterio: str = "costo") -> List[Dict[str, Any]]:
    """
    Ordena una lista de rutas (diccionarios con 'ruta' y 'costo') usando Mergesort.
    """
    if len(rutas) <= 1:
        return rutas

    medio = len(rutas) // 2
    izquierda = mergesort_rutas(rutas[:medio], criterio)
    derecha = mergesort_rutas(rutas[medio:], criterio)

    return _merge(izquierda, derecha, criterio)


def _merge(izq: List[Dict[str, Any]], der: List[Dict[str, Any]], criterio: str) -> List[Dict[str, Any]]:
    resultado = []
    i = j = 0

    while i < len(izq) and j < len(der):
        if izq[i][criterio] <= der[j][criterio]:
            resultado.append(izq[i])
            i += 1
        else:
            resultado.append(der[j])
            j += 1

    resultado.extend(izq[i:])
    resultado.extend(der[j:])
    return resultado
