"""
ordenar.py - Algoritmo Mergesort (Divide et Impera).
Responsable: Integrante B
"""

from typing import List, Dict, Any, Callable, Optional


def mergeSort(arr: list, key: Optional[Callable] = None) -> list:
    """
    Ordena una lista de elementos usando Mergesort.
    Soporta lista simple o lista de diccionarios con funcion key.
    """
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    leftHalf = arr[:mid]
    rightHalf = arr[mid:]

    sortedLeft = mergeSort(leftHalf, key)
    sortedRight = mergeSort(rightHalf, key)

    return _merge(sortedLeft, sortedRight, key)


def _merge(left: list, right: list, key: Optional[Callable] = None) -> list:
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        val_l = key(left[i]) if key else left[i]
        val_r = key(right[j]) if key else right[j]

        if val_l <= val_r:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


def mergesort_rutas(rutas: List[Dict[str, Any]], criterio: str = "costo") -> List[Dict[str, Any]]:
    """Función de conveniencia para ordenar rutas por un criterio ('costo')."""
    return mergeSort(rutas, key=lambda x: x[criterio])
