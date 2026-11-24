import sys
import time
from pathlib import Path
from typing import Any, Dict, List

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd
import matplotlib
import tkinter as tk
from tkinter import ttk

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from rutas.datos import RED_VIAL, CIUDADES_PUENTE, SECTORES, obtener_ciudades
from rutas.dividir import obtener_aristas_intersectoriales, obtener_subgrafo_sector
from rutas.dijkstra import dijkstra
from rutas.floyd import (
    floyd_warshall,
    floyd_warshall_matriz,
    reconstruir_camino_floyd,
)
from rutas.ordenar import mergeSort, mergesort_rutas
from rutas.requestPeru import OUTPUT_PATH, descargar_regiones

CIUDADES = {
    "Arequipa": (-71.5375, -16.4090),
    "Mollendo": (-72.0150, -17.0250),
    "Moquegua": (-70.9160, -17.1930),
    "Ilo": (-71.3320, -17.6410),
    "Juliaca": (-70.1290, -15.4930),
    "Puno": (-70.0200, -15.8400),
    "Ilave": (-69.6260, -16.0920),
    "Desaguadero": (-69.0410, -16.4350),
    "Sicuani": (-71.2410, -14.2730),
    "Cusco": (-71.9700, -13.5320),
    "Urubamba": (-72.0000, -13.3090),
    "Ollantaytambo": (-72.2600, -13.2580),
}

COLORES_REGIONES = ["#c8e6c9", "#bbdefb", "#ffe0b2", "#e1bee7"]


class MapaRutasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rutas turísticas del sur del Perú")
        self.root.geometry("1240x720")

        self.gdf = None
        self.fig = Figure(figsize=(9, 6.2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.lienzo = None
        self.arestas = {}
        self.orden_arestas = []
        self.ruta = []
        self.costo = None
        self.detalles = None
        self.algoritmo_usado = ""
        self.estado = tk.StringVar(value="Cargando mapa...")

        self.origen = tk.StringVar(value="Arequipa")
        self.destino = tk.StringVar(value="Ilo")
        self.algoritmo = tk.StringVar(value="Dijkstra (local)")

        self._construir_interfaz()
        self._preparar_arestas()
        self._cargar_mapa()
        self.dibujar()
        self.mostrar_resultados()

    def _construir_interfaz(self):
        controles = ttk.Frame(self.root, padding=10)
        controles.pack(side="top", fill="x")

        ttk.Label(controles, text="Origen:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            controles,
            textvariable=self.origen,
            values=obtener_ciudades(),
            state="readonly",
            width=18,
        ).grid(row=0, column=1, padx=(4, 14))

        ttk.Label(controles, text="Destino:").grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            controles,
            textvariable=self.destino,
            values=obtener_ciudades(),
            state="readonly",
            width=18,
        ).grid(row=0, column=3, padx=(4, 14))

        ttk.Label(controles, text="Algoritmo:").grid(row=0, column=4, sticky="w")
        ttk.Combobox(
            controles,
            textvariable=self.algoritmo,
            values=(
                "Dijkstra (local)",
                "Floyd-Warshall (global)",
                "Híbrido (Merge+Dijkstra+Floyd)",
            ),
            state="readonly",
            width=30,
        ).grid(row=0, column=5, padx=(4, 14))

        ttk.Button(controles, text="Calcular ruta", command=self.calcular).grid(
            row=0, column=6
        )

        ejemplos = ttk.LabelFrame(self.root, text="Puntos de ejemplo", padding=6)
        ejemplos.pack(side="top", fill="x", padx=10)
        for indice, (origen, destino) in enumerate(
            [
                ("Arequipa", "Ilo"),
                ("Mollendo", "Moquegua"),
                ("Arequipa", "Cusco"),
                ("Ilo", "Ollantaytambo"),
            ]
        ):
            ttk.Button(
                ejemplos,
                text=f"{origen} → {destino}",
                command=lambda o=origen, d=destino: self.usar_ejemplo(o, d),
            ).grid(row=0, column=indice, padx=4)

        cuerpo = ttk.Frame(self.root, padding=(10, 0, 10, 0))
        cuerpo.pack(side="top", fill="both", expand=True)

        self.lienzo = FigureCanvasTkAgg(self.fig, master=cuerpo)
        self.lienzo.get_tk_widget().pack(side="left", fill="both", expand=True)

        panel = ttk.Frame(cuerpo, width=300)
        panel.pack(side="right", fill="y", padx=(10, 0))
        panel.pack_propagate(False)

        ttk.Label(panel, text="Resultado", font=("TkDefaultFont", 11, "bold")).pack(
            anchor="w"
        )
        self.resultado = tk.Text(panel, width=38, height=16, wrap="word")
        self.resultado.pack(fill="both", expand=True, pady=(4, 8))

        ttk.Label(
            panel, text="Pesos ordenados (mergeSort)", font=("TkDefaultFont", 11, "bold")
        ).pack(anchor="w")
        self.pesos = tk.Text(panel, width=38, height=14, wrap="none")
        self.pesos.pack(fill="both", expand=True)

        ttk.Label(self.root, textvariable=self.estado, padding=(10, 6)).pack(
            side="bottom", fill="x"
        )

    def _cargar_mapa(self):
        if not OUTPUT_PATH.exists():
            self.estado.set("No hay mapa descargado; revisa la conexión")
            return
        self._leer_mapa()

    def _leer_mapa(self):
        try:
            self.gdf = gpd.read_file(OUTPUT_PATH)
            self.estado.set(f"Mapa GeoPandas: {len(self.gdf)} regiones")
        except Exception as error:
            self.gdf = None
            self.estado.set(f"No se pudo leer el mapa: {error}")
        self.dibujar()

    def _preparar_arestas(self):
        vistas = set()
        for origen, destinos in RED_VIAL.items():
            for arista in destinos:
                par = tuple(sorted((origen, arista.destino)))
                if par in vistas:
                    continue
                vistas.add(par)
                self.arestas[par] = arista.peso_efectivo
        self.orden_arestas = mergeSort(
            [(peso, par[0], par[1]) for par, peso in self.arestas.items()]
        )

    def usar_ejemplo(self, origen, destino):
        self.origen.set(origen)
        self.destino.set(destino)
        self.calcular()

    def calcular(self):
        origen = self.origen.get()
        destino = self.destino.get()
        nombre = self.algoritmo.get()

        self.detalles = None
        if nombre.startswith("Dijkstra"):
            self.costo, self.ruta = dijkstra(origen, destino)
        elif nombre.startswith("Floyd"):
            self.costo, self.ruta = floyd_warshall(origen, destino)
        else:
            self.costo, self.ruta, self.detalles = buscar_mejor_ruta_hibrida(
                origen, destino
            )

        self.algoritmo_usado = nombre
        if self.ruta:
            self.estado.set(
                f"{nombre}: {origen} → {destino} en {self.costo:g} h "
                f"({len(self.ruta) - 1} tramos)"
            )
        else:
            self.estado.set(f"{nombre}: sin ruta entre {origen} y {destino}")

        self.dibujar()
        self.mostrar_resultados()

    def mostrar_resultados(self):
        self.resultado.delete("1.0", "end")
        if not self.algoritmo_usado:
            self.resultado.insert(
                "1.0", "Elige origen, destino y algoritmo, luego pulsa 'Calcular ruta'."
            )
        else:
            texto = (
                f"Algoritmo: {self.algoritmo_usado}\n"
                f"Costo: {self.costo:g} h\n"
                f"Ruta: {' → '.join(self.ruta) if self.ruta else 'sin ruta'}\n"
            )
            if self.detalles:
                texto += (
                    f"\nMergeSort → Dijkstra → Floyd ({self.detalles['tiempo_ms']:.3f} ms)\n"
                    f"Grupos: {', '.join(self.detalles['grupos'])}\n"
                    f"Nodos reducidos: {self.detalles['nodos']}\n"
                    f"Sub-rutas ordenadas (top 3):\n"
                )
                for sub in self.detalles["sub_rutas"][:3]:
                    texto += (
                        f"  {sub['inicio']}→{sub['fin']} "
                        f"({sub['costo']:g} h): {' → '.join(sub['camino'])}\n"
                    )
            self.resultado.insert("1.0", texto)

        self.pesos.delete("1.0", "end")
        for posicion, (peso, origen, destino) in enumerate(self.orden_arestas, 1):
            self.pesos.insert(
                "end", f"{posicion:2}. {origen:<14} {destino:<14} {peso:>5.2f} h\n"
            )

    def dibujar(self):
        self.ax.clear()
        self.ax.set_facecolor("#fafafa")
        self.fig.patch.set_facecolor("#fafafa")

        if self.gdf is not None:
            colores = [
                COLORES_REGIONES[indice % len(COLORES_REGIONES)]
                for indice in range(len(self.gdf))
            ]
            self.gdf.plot(
                ax=self.ax,
                color=colores,
                edgecolor="#546e7a",
                linewidth=0.8,
                alpha=0.7,
                zorder=1,
            )
            for _, fila in self.gdf.iterrows():
                punto = fila.geometry.representative_point()
                self.ax.text(
                    punto.x,
                    punto.y,
                    fila["shapeName"],
                    ha="center",
                    fontsize=9,
                    fontweight="bold",
                    color="#37474f",
                    zorder=2,
                )

        self._dibujar_arestas()
        self._dibujar_ruta()
        self._dibujar_nodos()
        self._ajustar_limits()
        self.ax.set_axis_off()
        self.fig.tight_layout()
        self.lienzo.draw_idle()

    def _dibujar_arestas(self):
        total = max(1, len(self.orden_arestas) - 1)
        colores = {}
        for posicion, (_, origen, destino) in enumerate(self.orden_arestas):
            proporcion = posicion / total
            rojo = int(50 + 180 * proporcion)
            verde = int(150 - 90 * proporcion)
            colores[tuple(sorted((origen, destino)))] = f"#{rojo:02x}{verde:02x}{40:02x}"

        for origen, destino in self.arestas:
            self.ax.plot(
                [CIUDADES[origen][0], CIUDADES[destino][0]],
                [CIUDADES[origen][1], CIUDADES[destino][1]],
                color=colores[(origen, destino)],
                linewidth=1.8,
                zorder=3,
            )

    def _dibujar_ruta(self):
        for origen, destino in zip(self.ruta, self.ruta[1:]):
            self.ax.plot(
                [CIUDADES[origen][0], CIUDADES[destino][0]],
                [CIUDADES[origen][1], CIUDADES[destino][1]],
                color="#d32f2f",
                linewidth=4,
                zorder=4,
            )

    def _dibujar_nodos(self):
        for ciudad, (lon, lat) in CIUDADES.items():
            en_ruta = ciudad in self.ruta
            color = "#d32f2f" if en_ruta else "#1565c0"
            self.ax.scatter(
                lon,
                lat,
                s=75 if en_ruta else 38,
                color=color,
                edgecolors="white",
                linewidths=0.8,
                zorder=5,
            )
            self.ax.annotate(
                ciudad,
                (lon, lat),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
                fontweight="bold",
                color=color,
                zorder=6,
            )

    def _ajustar_limits(self):
        longitudes = [lon for lon, _ in CIUDADES.values()]
        latitudes = [lat for _, lat in CIUDADES.values()]
        if self.gdf is not None:
            minx, miny, maxx, maxy = self.gdf.total_bounds
            longitudes.extend([minx, maxx])
            latitudes.extend([miny, maxy])

        min_lon, max_lon = min(longitudes), max(longitudes)
        min_lat, max_lat = min(latitudes), max(latitudes)
        margen_lon = (max_lon - min_lon or 1) * 0.08
        margen_lat = (max_lat - min_lat or 1) * 0.08
        self.ax.set_xlim(min_lon - margen_lon, max_lon + margen_lon)
        self.ax.set_ylim(min_lat - margen_lat, max_lat + margen_lat)
        self.ax.set_aspect("equal", adjustable="box")


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


def _peso_directo(origen: str, destino: str) -> float:
    for arista in RED_VIAL.get(origen, []):
        if arista.destino == destino:
            return arista.peso_efectivo
    return float("inf")


def buscar_mejor_ruta_hibrida(origen: str, destino: str):
    inicio = time.perf_counter()
    detalles: Dict[str, Any] = {
        "grupos": [],
        "sub_rutas": [],
        "nodos": 0,
        "tiempo_ms": 0.0,
    }

    if origen not in RED_VIAL or destino not in RED_VIAL:
        return float("inf"), [], detalles

    nodos = sorted(set(CIUDADES_PUENTE) | {origen, destino})
    subrutas: List[Dict[str, Any]] = []
    grupos_usados: List[str] = []
    relevantes = set(CIUDADES_PUENTE) | {origen, destino}

    for nombre_sector, ciudades in SECTORES.items():
        subgrafo = obtener_subgrafo_sector(nombre_sector)
        puntos = sorted(relevantes & set(ciudades) & set(subgrafo))
        if len(puntos) < 2:
            continue
        grupos_usados.append(nombre_sector)

        for indice, inicio_sub in enumerate(puntos):
            for fin_sub in puntos[indice + 1:]:
                costo, camino = dijkstra(inicio_sub, fin_sub, subgrafo)
                if camino:
                    subrutas.append(
                        {
                            "grupo": nombre_sector,
                            "inicio": inicio_sub,
                            "fin": fin_sub,
                            "costo": costo,
                            "camino": camino,
                        }
                    )

    subrutas_ordenadas = mergesort_rutas(subrutas, criterio="costo")
    mejores = {}
    for sub in subrutas_ordenadas:
        clave = (sub["inicio"], sub["fin"])
        if clave not in mejores:
            mejores[clave] = sub

    aristas_globales = [
        (inicio_sub, fin_sub, sub["costo"])
        for (inicio_sub, fin_sub), sub in mejores.items()
    ]
    aristas_globales.extend(obtener_aristas_intersectoriales())

    _, siguiente = floyd_warshall_matriz(nodos, aristas_globales)
    camino_reducido = reconstruir_camino_floyd(origen, destino, siguiente)
    if not camino_reducido:
        detalles.update(
            {
                "grupos": grupos_usados,
                "sub_rutas": subrutas_ordenadas,
                "nodos": len(nodos),
                "tiempo_ms": (time.perf_counter() - inicio) * 1000,
            }
        )
        return float("inf"), [], detalles

    ruta: List[str] = []
    for actual, siguiente_nodo in zip(camino_reducido, camino_reducido[1:]):
        if (actual, siguiente_nodo) in mejores:
            tramo = mejores[(actual, siguiente_nodo)]["camino"]
        elif (siguiente_nodo, actual) in mejores:
            tramo = list(reversed(mejores[(siguiente_nodo, actual)]["camino"]))
        else:
            tramo = [actual, siguiente_nodo]

        if not ruta:
            ruta.extend(tramo)
        else:
            ruta.extend(tramo[1:])

    costo_total = sum(_peso_directo(a, b) for a, b in zip(ruta, ruta[1:]))
    detalles.update(
        {
            "grupos": grupos_usados,
            "sub_rutas": subrutas_ordenadas,
            "nodos": len(nodos),
            "tiempo_ms": (time.perf_counter() - inicio) * 1000,
        }
    )
    return round(costo_total, 2), ruta, detalles


def main():
    print("=" * 60)
    print("  OPTIMIZADOR DE RUTAS TURÍSTICAS - SUR DEL PERÚ")
    print("  Enfoque Híbrido: Divide et Impera + Goloso + PD")
    print("=" * 60)

    try:
        descargar_regiones()
    except Exception as error:
        print(f"No se pudo descargar el mapa: {error}")
        if not OUTPUT_PATH.exists():
            print("No hay copia local del GeoJSON; el mapa se mostrará vacío.")

    origen = "Ilo"
    destino = "Ollantaytambo"
    print(f"\nCalculando itinerario óptimo: [{origen}] -> [{destino}]...\n")

    mejor_costo, mejor_ruta, detalles = buscar_mejor_ruta_hibrida(origen, destino)
    print("--- MEJOR RUTA HÍBRIDA (MergeSort + Dijkstra + Floyd) ---")
    print(f" {' -> '.join(mejor_ruta)} | {mejor_costo:g} h")
    print(
        f" Grupos: {', '.join(detalles['grupos'])} | "
        f"nodos reducidos: {detalles['nodos']}"
    )
    for sub in detalles["sub_rutas"][:3]:
        print(
            f"   sub-ruta {sub['inicio']}->{sub['fin']}: "
            f"{' -> '.join(sub['camino'])} ({sub['costo']:g} h)"
        )
    print()

    rutas, t_hibrido = ejecutar_pipeline_hibrido(origen, destino)

    print(f"--- Top de Rutas Encontradas (Ordenadas por Mergesort) ---")
    for i, r in enumerate(rutas[:3], 1):
        print(f" Opción {i}: {' -> '.join(r['ruta'])}")
        print(f"   Costo ponderado (tiempo/estado): {r['costo']} hrs eq.")

    _, t_global = ejecutar_floyd_global()

    print("\n" + "=" * 60)
    print("  COMPARATIVA DE COMPLEJIDAD Y TIEMPOS")
    print("=" * 60)
    print(f" Floyd-Warshall Global (V = {len(obtener_ciudades())}): {t_global * 1000:.4f} ms")
    print(f" Pipeline base (V={len(CIUDADES_PUENTE)}): {t_hibrido * 1000:.4f} ms")
    print(f" Híbrido avanzado (Merge+Dijkstra+Floyd): {detalles['tiempo_ms']:.4f} ms")
    print("=" * 60)


    root = tk.Tk()
    MapaRutasApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
