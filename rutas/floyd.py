
# rutas/floyd_warshall.py

from math import inf

# (origin, destination, base travel time in hours, road-condition factor)
ARISTAS = [
    ("Arequipa", "Mollendo", 2.0, 1.1),  # 2.2 hours
    ("Arequipa", "Moquegua", 3.5, 1.0),  # 3.5 hours
    ("Moquegua", "Ilo", 1.3, 1.0),       # 1.3 hours
]


def _crear_grafo():
    ciudades = sorted({
        ciudad
        for origen, destino, _, _ in ARISTAS
        for ciudad in (origen, destino)
    })
    indices = {ciudad: i for i, ciudad in enumerate(ciudades)}
    n = len(ciudades)

    distancias = [[inf] * n for _ in range(n)]
    siguiente = [[None] * n for _ in range(n)]

    for i in range(n):
        distancias[i][i] = 0
        siguiente[i][i] = i

    for origen, destino, tiempo, factor in ARISTAS:
        i = indices[origen]
        j = indices[destino]
        costo = tiempo * factor

        # Treat each road as two-way. Remove this block if roads are one-way.
        if costo < distancias[i][j]:
            distancias[i][j] = costo
            siguiente[i][j] = j

        if costo < distancias[j][i]:
            distancias[j][i] = costo
            siguiente[j][i] = i

    # Floyd–Warshall: calculate shortest costs and retain next hops.
    for k in range(n):
        for i in range(n):
            for j in range(n):
                nuevo_costo = distancias[i][k] + distancias[k][j]
                if nuevo_costo < distancias[i][j]:
                    distancias[i][j] = nuevo_costo
                    siguiente[i][j] = siguiente[i][k]

    return ciudades, indices, distancias, siguiente


def floyd_warshall(origen, destino):
    """
    Return (cost, route) for the shortest route between two cities.
    Return (inf, []) if no route exists.
    """
    ciudades, indices, distancias, siguiente = _crear_grafo()

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

    return round(distancias[i][j], 10), ruta
