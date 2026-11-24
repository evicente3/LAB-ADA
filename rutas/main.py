import json
import sys
import threading
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk
from tkinter import ttk

from rutas.datos import RED_VIAL, obtener_ciudades
from rutas.dijkstra import dijkstra
from rutas.floyd import floyd_warshall
from rutas.ordenar import mergeSort
from rutas.requestPeru import OUTPUT_PATH, TARGET_REGIONS, descargar_regiones

ANCHO = 900
ALTO = 620
MARGEN = 45

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

        self.geojson = None
        self.proyectar = lambda lon, lat: (0, 0)
        self.arestas = {}
        self.orden_arestas = []
        self.ruta = []
        self.costo = None
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
            values=("Dijkstra (local)", "Floyd-Warshall (global)"),
            state="readonly",
            width=24,
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
            ]
        ):
            ttk.Button(
                ejemplos,
                text=f"{origen} → {destino}",
                command=lambda o=origen, d=destino: self.usar_ejemplo(o, d),
            ).grid(row=0, column=indice, padx=4)

        cuerpo = ttk.Frame(self.root, padding=(10, 0, 10, 0))
        cuerpo.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(cuerpo, width=ANCHO, height=ALTO, bg="#fafafa")
        self.canvas.pack(side="left", fill="both", expand=True)

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
        if OUTPUT_PATH.exists():
            self._leer_mapa()
            return

        self.estado.set("Descargando mapa desde geoboundaries.org...")
        threading.Thread(target=self._descargar, daemon=True).start()

    def _descargar(self):
        try:
            descargar_regiones()
        except Exception as error:
            self.root.after(
                0, lambda: self.estado.set(f"No se pudo descargar el mapa: {error}")
            )
        else:
            self.root.after(0, self._leer_mapa)

    def _leer_mapa(self):
        try:
            with OUTPUT_PATH.open(encoding="utf-8") as archivo:
                self.geojson = json.load(archivo)
            cantidad = len(self.geojson.get("features", []))
            self.estado.set(f"Mapa cargado: {cantidad} regiones")
        except (OSError, ValueError) as error:
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

        if nombre.startswith("Dijkstra"):
            self.costo, self.ruta = dijkstra(origen, destino)
        else:
            self.costo, self.ruta = floyd_warshall(origen, destino)

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
            self.resultado.insert(
                "1.0",
                f"Algoritmo: {self.algoritmo_usado}\n"
                f"Costo: {self.costo:g} h\n"
                f"Ruta: {' → '.join(self.ruta) if self.ruta else 'sin ruta'}\n",
            )

        self.pesos.delete("1.0", "end")
        for posicion, (peso, origen, destino) in enumerate(self.orden_arestas, 1):
            self.pesos.insert(
                "end", f"{posicion:2}. {origen:<14} {destino:<14} {peso:>5.2f} h\n"
            )

    def _iter_geometria(self):
        if not self.geojson:
            return
        for caracteristica in self.geojson.get("features", []):
            geometria = caracteristica.get("geometry") or {}
            tipo = geometria.get("type")
            coordenadas = geometria.get("coordinates") or []
            if tipo == "Polygon":
                anillos = coordenadas
            elif tipo == "MultiPolygon":
                anillos = [
                    anillo for poligono in coordenadas for anillo in poligono
                ]
            else:
                continue
            yield caracteristica, anillos

    def _nombre_region(self, caracteristica):
        for valor in (caracteristica.get("properties") or {}).values():
            nombre = str(valor).strip()
            if nombre in TARGET_REGIONS:
                return nombre
        return ""

    def _actualizar_proyeccion(self):
        puntos = [(lon, lat) for lon, lat in CIUDADES.values()]
        for _, anillos in self._iter_geometria():
            for anillo in anillos:
                puntos.extend(anillo)

        if not puntos:
            self.proyectar = lambda lon, lat: (0, 0)
            return

        longitudes = [lon for lon, _ in puntos]
        latitudes = [lat for _, lat in puntos]
        min_lon, max_lon = min(longitudes), max(longitudes)
        min_lat, max_lat = min(latitudes), max(latitudes)
        ancho = max_lon - min_lon or 1
        alto = max_lat - min_lat or 1
        escala = min(
            (ANCHO - 2 * MARGEN) / ancho,
            (ALTO - 2 * MARGEN) / alto,
        )
        desplazamiento_x = (ANCHO - ancho * escala) / 2 - min_lon * escala
        desplazamiento_y = (ALTO - alto * escala) / 2 + min_lat * escala

        def proyectar(lon, lat):
            return (
                desplazamiento_x + lon * escala,
                ALTO - (desplazamiento_y + lat * escala),
            )

        self.proyectar = proyectar

    def dibujar(self):
        self.canvas.delete("all")
        self._actualizar_proyeccion()
        self._dibujar_regiones()
        self._dibujar_arestas()
        self._dibujar_ruta()
        self._dibujar_nodos()

    def _dibujar_regiones(self):
        for indice, (caracteristica, anillos) in enumerate(self._iter_geometria()):
            if not anillos:
                continue
            color = COLORES_REGIONES[indice % len(COLORES_REGIONES)]
            exterior = [
                coordenada
                for punto in anillos[0]
                for coordenada in self.proyectar(punto[0], punto[1])
            ]
            if len(exterior) >= 6:
                self.canvas.create_polygon(
                    exterior, fill=color, outline="#78909c", width=1, tags="mapa"
                )
            for anillo in anillos[1:]:
                hueco = [
                    coordenada
                    for punto in anillo
                    for coordenada in self.proyectar(punto[0], punto[1])
                ]
                if len(hueco) >= 6:
                    self.canvas.create_polygon(
                        hueco, fill="#fafafa", outline="#78909c", width=1, tags="mapa"
                    )

            nombre = self._nombre_region(caracteristica)
            if nombre:
                longitudes = [punto[0] for punto in anillos[0]]
                latitudes = [punto[1] for punto in anillos[0]]
                x, y = self.proyectar(
                    (min(longitudes) + max(longitudes)) / 2,
                    (min(latitudes) + max(latitudes)) / 2,
                )
                self.canvas.create_text(
                    x,
                    y,
                    text=nombre,
                    fill="#37474f",
                    font=("TkDefaultFont", 12, "bold"),
                    tags="mapa",
                )

    def _dibujar_arestas(self):
        total = max(1, len(self.orden_arestas) - 1)
        colores = {}
        for posicion, (_, origen, destino) in enumerate(self.orden_arestas):
            proporcion = posicion / total
            rojo = int(50 + 180 * proporcion)
            verde = int(150 - 90 * proporcion)
            colores[tuple(sorted((origen, destino)))] = f"#{rojo:02x}{verde:02x}{40:02x}"

        for (origen, destino), peso in self.arestas.items():
            x1, y1 = self.proyectar(*CIUDADES[origen])
            x2, y2 = self.proyectar(*CIUDADES[destino])
            self.canvas.create_line(
                x1, y1, x2, y2, fill=colores[(origen, destino)], width=2, tags="grafo"
            )

    def _dibujar_ruta(self):
        for origen, destino in zip(self.ruta, self.ruta[1:]):
            x1, y1 = self.proyectar(*CIUDADES[origen])
            x2, y2 = self.proyectar(*CIUDADES[destino])
            self.canvas.create_line(
                x1, y1, x2, y2, fill="#d32f2f", width=5, tags="ruta"
            )

    def _dibujar_nodos(self):
        for ciudad, coordenadas in CIUDADES.items():
            x, y = self.proyectar(*coordenadas)
            en_ruta = ciudad in self.ruta
            color = "#d32f2f" if en_ruta else "#1565c0"
            radio = 6 if en_ruta else 4
            self.canvas.create_oval(
                x - radio,
                y - radio,
                x + radio,
                y + radio,
                fill=color,
                outline="white",
                width=1,
                tags="nodo",
            )
            self.canvas.create_text(
                x + radio + 3,
                y - radio - 2,
                text=ciudad,
                anchor="sw",
                fill=color,
                font=("TkDefaultFont", 9, "bold"),
                tags="nodo",
            )


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


    root = tk.Tk()
    MapaRutasApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
