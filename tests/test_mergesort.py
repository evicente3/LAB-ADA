"""
test_mergesort.py - Pruebas unitarias de Mergesort.
Responsable: Integrante B
"""

from rutas.ordenar import mergesort_rutas


def test_mergesort_ordenamiento():
    """Valida que Mergesort ordene correctamente rutas según costo."""
    rutas = [
        {"ruta": ["Arequipa", "Puno"], "costo": 12.5},
        {"ruta": ["Arequipa", "Moquegua"], "costo": 3.5},
        {"ruta": ["Arequipa", "Cusco"], "costo": 18.2},
    ]
    ordenadas = mergesort_rutas(rutas, criterio="costo")
    costos = [r["costo"] for r in ordenadas]
    assert costos == [3.5, 12.5, 18.2]
