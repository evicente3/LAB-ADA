# Práctica 07: Rutas Turísticas Inteligentes del Sur del Perú
**Análisis y Diseño de Algoritmos (ADA) - UNSA**

Optimización de itinerarios turísticos multimodales conectando las regiones de **Arequipa, Moquegua, Puno y Cusco** mediante un enfoque híbrido que combina paradigmas algorítmicos para minimizar tiempo, costo y complejidad computacional.

---

## 🚀 Paradigmas Integrados

1. **Divide et Impera (`dividir.py`):** Descomposición de la red vial interregional en subredes (sectores o corredores regionales) identificando nodos frontera / ciudades puente.
2. **Algoritmo Goloso (`dijkstra.py`):** Búsqueda local de caminos mínimos y rutas directas óptimas intra-sector mediante Dijkstra con cola de prioridad (`heapq`).
3. **Programación Dinámica (`floyd.py`):** Optimización intersectorial sobre el grafo reducido de ciudades puente mediante Floyd-Warshall.
4. **Ordenamiento Divide et Impera (`ordenar.py`):** Clasificación y ranking de rutas alternativas mediante Mergesort garantizado en $O(n \log n)$.

---

## 📂 Estructura del Proyecto

```text
LAB-ADA/
├── rutas/
│   ├── __init__.py
│   ├── datos.py       # Modelo de ciudades, tramos viales y factores de carretera [Integrante A]
│   ├── dividir.py     # Descomposición en subredes y detección de puentes [Integrante A]
│   ├── dijkstra.py    # Dijkstra local optimizado con heapq [Integrante A]
│   ├── floyd.py       # Floyd-Warshall sobre grafo interregional reducido [Integrante B]
│   ├── ordenar.py     # Mergesort para clasificar alternativas de ruta [Integrante B]
│   └── main.py        # Pipeline de ejecución, benchmarking y gráficas [Integrante B]
├── tests/
│   ├── __init__.py
│   └── test_algoritmos.py # Pruebas unitarias con pytest [Ambos]
├── .gitignore
└── README.md
```

---

## 💻 Ejecución

```bash
# Ejecutar pipeline principal y benchmark
python -m rutas.main

# Ejecutar pruebas unitarias
pytest
```
