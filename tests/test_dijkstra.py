"""
test_dijkstra.py - Casos de prueba de Dijkstra calculados a mano.
"""

from rutas.dijkstra import dijkstra


def test_dijkstra_ruta_directa():
    """Caso 1: Ruta directa entre ciudades contiguas (Arequipa - Mollendo)."""
    costo, ruta = dijkstra("Arequipa", "Mollendo")
    # 2.0 h con factor 'bueno' (1.1) = 2.2 h
    assert costo == 2.2
    assert ruta == ["Arequipa", "Mollendo"]


def test_dijkstra_ruta_intermedia():
    """Caso 2: Ruta con nodo intermedio (Arequipa - Ilo pasando por Moquegua)."""
    costo, ruta = dijkstra("Arequipa", "Ilo")
    # Arequipa -> Moquegua: 3.5 * 1.0 = 3.5
    # Moquegua -> Ilo: 1.3 * 1.0 = 1.3
    # Total esperado = 4.8 h
    assert costo == 4.8
    assert ruta == ["Arequipa", "Moquegua", "Ilo"]
