"""
main.py - Pipeline principal, benchmarking y validación comparativa.
Responsable: Integrante B

Ejecuta el pipeline híbrido (Divide + Dijkstra + Floyd-Warshall + Mergesort)
y lo compara contra Floyd-Warshall aplicado a todo el grafo sin partición.
"""

import time
from typing import List, Dict, Any
from rutas.datos import RED_VIAL, CIUDADES_PUENTE, obtener_ciudades
from rutas.dividir import obtener_aristas_intersectoriales
from rutas.dijkstra import dijkstra
from rutas.floyd import floyd_warshall_matriz, reconstruir_camino_floyd
from rutas.ordenar import mergesort_rutas


def ejecutar_pipeline_hibrido(origen: str, destino: str):
    """
    1. Divide: Se enfoca en las conexiones del grafo reducido de ciudades puente.
    2. Goloso: Calcula accesos locales con Dijkstra.
    3. PD: Resuelve con Floyd-Warshall sobre V_reducido << V_total.
    4. Mergesort: Ordena opciones de itinerario.
    """
    inicio = time.perf_counter()

    # Paso 1: Grafo reducido con ciudades puente
    nodos_puente = CIUDADES_PUENTE
    aristas_reducidas = obtener_aristas_intersectoriales()

    # Paso 2: Floyd-Warshall únicamente sobre los nodos puente (PD)
    dist_puentes, next_puentes = floyd_warshall_matriz(nodos_puente, aristas_reducidas)

    # Paso 3: Conectar origen y destino a través de los puentes usando Dijkstra (Goloso)
    opciones_itinerarios: List[Dict[str, Any]] = []

    for p_ini in nodos_puente:
        costo_ini, camino_ini = dijkstra(origen, p_ini)
        if costo_ini == float('inf'):
            continue

        for p_fin in nodos_puente:
            costo_fin, camino_fin = dijkstra(p_fin, destino)
            if costo_fin == float('inf'):
                continue

            costo_inter = dist_puentes[p_ini][p_fin]
            if costo_inter == float('inf'):
                continue

            camino_inter = reconstruir_camino_floyd(p_ini, p_fin, next_puentes)
            
            # Combinación de la ruta completa evitando duplicar nodos de frontera
            ruta_completa = camino_ini[:-1] + camino_inter[:-1] + camino_fin
            costo_total = round(costo_ini + costo_inter + costo_fin, 2)
            
            opciones_itinerarios.append({
                "ruta": ruta_completa,
                "costo": costo_total,
                "puentes": (p_ini, p_fin)
            })

    # Paso 4: Ordenar rutas alternativas por costo usando Mergesort
    rutas_ordenadas = mergesort_rutas(opciones_itinerarios, criterio="costo")
    fin = time.perf_counter()
    tiempo_hibrido = fin - inicio

    return rutas_ordenadas, tiempo_hibrido


def ejecutar_floyd_global():
    """Ejecuta Floyd-Warshall clásico directamente sobre toda la red vial."""
    inicio = time.perf_counter()
    ciudades = obtener_ciudades()
    aristas = []
    for u in ciudades:
        for arista in RED_VIAL.get(u, []):
            aristas.append((u, arista.destino, arista.peso_efectivo))

    dist, next_node = floyd_warshall_matriz(ciudades, aristas)
    fin = time.perf_counter()
    return dist, (fin - inicio)


def main():
    print("=" * 60)
    print("  OPTIMIZADOR DE RUTAS TURÍSTICAS - SUR DEL PERÚ")
    print("  Enfoque Híbrido: Divide et Impera + Goloso + PD")
    print("=" * 60)

    origen = "Ilo"
    destino = "Ollantaytambo"
    print(f"\nCalculando itinerario óptimo: [{origen}] -> [{destino}]...\n")

    # 1. Ejecutar pipeline híbrido
    rutas, t_hibrido = ejecutar_pipeline_hibrido(origen, destino)

    print(f"--- Top de Rutas Encontradas (Ordenadas por Mergesort) ---")
    for i, r in enumerate(rutas[:3], 1):
        print(f" Opción {i}: {' -> '.join(r['ruta'])}")
        print(f"   Costo ponderado (tiempo/estado): {r['costo']} hrs eq.")

    # 2. Benchmarking contra Floyd-Warshall global
    _, t_global = ejecutar_floyd_global()

    print("\n" + "=" * 60)
    print("  COMPARATIVA DE COMPLEJIDAD Y TIEMPOS")
    print("=" * 60)
    print(f" Floyd-Warshall Global (V = {len(obtener_ciudades())}): {t_global * 1000:.4f} ms")
    print(f" Híbrido (Divide + Dijkstra + Floyd reducido V={len(CIUDADES_PUENTE)}): {t_hibrido * 1000:.4f} ms")
    print("=" * 60)


if __name__ == "__main__":
    main()
