from rutas.floyd_warshall import floyd_warshall

costo, ruta = floyd_warshall("Arequipa", "Ilo")
assert costo == 4.8
assert ruta == ["Arequipa", "Moquegua", "Ilo"]
