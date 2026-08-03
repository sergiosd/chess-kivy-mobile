# puzzle_manager.py
import csv
import random
import json
import os


class PuzzleManager:
    def __init__(self, ruta_csv="lichess_db_puzzle.csv",
                 ruta_memoria="memoria_puzzles_global.json"):
        self.ruta_csv = ruta_csv
        self.ruta_memoria = ruta_memoria
        self.cache_puzzles = {}
        self.puzzles_vistos_global = self.cargar_memoria_global()
        print("Iniciando Gestor de Puzzles Premium con Memoria Dual...")

    def cargar_memoria_global(self):
        if os.path.exists(self.ruta_memoria):
            with open(self.ruta_memoria, "r") as f:
                try:
                    return set(json.load(f))
                except json.JSONDecodeError:
                    return set()
        return set()

    def guardar_memoria_global(self):
        with open(self.ruta_memoria, "w") as f:
            json.dump(list(self.puzzles_vistos_global), f)

    def registrar_puzzle_global(self, id_puzzle):
        self.puzzles_vistos_global.add(id_puzzle)
        self.guardar_memoria_global()

    # POPULARIDAD MINIMA BAJADA A 0 PARA MÁS VARIEDAD Y SE RECIBEN LOS IDS LOCALES DE LA PARTIDA
    def cargar_puzzles_por_elo(self, elo_objetivo, ids_locales, margen=50, cantidad=20, pop_min=0):
        elo_real = max(600, elo_objetivo)
        rango_min = elo_real - margen
        rango_max = elo_real + margen
        clave_rango = f"{rango_min}-{rango_max}"

        if clave_rango not in self.cache_puzzles:
            self.cache_puzzles[clave_rango] = []
        elif len(self.cache_puzzles[clave_rango]) >= cantidad:
            return

        print(f"Cargando tácticas (ELO {rango_min}-{rango_max}, Pop > {pop_min})...")

        candidatos_nuevos = []
        candidatos_reciclados = []

        # --- Extraemos los IDs que ya tenemos cargados en la recámara ---
        ids_en_cache = {p["id"] for p in self.cache_puzzles[clave_rango]}

        try:
            with open(self.ruta_csv, mode='r', encoding='utf-8') as archivo:
                lector_csv = csv.reader(archivo)
                next(lector_csv, None)

                for fila in lector_csv:
                    if len(fila) < 8: continue

                    id_puzzle = fila[0]
                    try:
                        rating = int(fila[3])
                        pop = int(fila[5])

                        if (rango_min <= rating <= rango_max) and (pop >= pop_min):
                            # --- CORRECCIÓN: Ignoramos si ya lo jugamos o si YA ESTÁ EN LA RECÁMARA ---
                            if id_puzzle in ids_locales or id_puzzle in ids_en_cache:
                                continue

                            puzzle_dict = {
                                "id": id_puzzle, "fen": fila[1], "moves": fila[2].split(" "),
                                "rating": rating, "popularity": pop, "themes": fila[7]
                            }

                            if id_puzzle in self.puzzles_vistos_global:
                                candidatos_reciclados.append(puzzle_dict)
                            else:
                                candidatos_nuevos.append(puzzle_dict)
                                if len(candidatos_nuevos) >= cantidad:
                                    break
                    except ValueError:
                        continue
        except FileNotFoundError:
            print(f"ERROR: No se encuentra la base de datos {self.ruta_csv}.")

        # Si hay puzzles totalmente nuevos en la base de datos, los usamos
        if len(candidatos_nuevos) > 0:
            self.cache_puzzles[clave_rango].extend(candidatos_nuevos)

        # Si la BD se ha quedado sin nuevos para este rango, RECICLAMOS los del fichero global
        elif len(candidatos_reciclados) > 0:
            print(
                f"Memoria global agotada para ELO {rango_min}-{rango_max}. Reciclando {len(candidatos_reciclados)} puzzles...")
            for p in candidatos_reciclados[:cantidad]:
                self.puzzles_vistos_global.discard(p["id"])
            self.guardar_memoria_global()
            self.cache_puzzles[clave_rango].extend(candidatos_reciclados[:cantidad])

        if len(self.cache_puzzles[clave_rango]) == 0:
            print(f"AVISO CRÍTICO: No existe ningún puzle para el rango {rango_min}-{rango_max}.")

    def obtener_puzzle_aleatorio(self, elo_objetivo, ids_locales):
        elo_real = max(600, elo_objetivo)
        rango_min = elo_real - 50
        rango_max = elo_real + 50
        clave_rango = f"{rango_min}-{rango_max}"

        self.cargar_puzzles_por_elo(elo_real, ids_locales)

        if clave_rango not in self.cache_puzzles or not self.cache_puzzles[clave_rango]:
            return None

        puzzle_elegido = random.choice(self.cache_puzzles[clave_rango])
        self.cache_puzzles[clave_rango].remove(puzzle_elegido)

        # Al elegirlo, lo registramos para que otros mapas lo ignoren en el futuro
        self.registrar_puzzle_global(puzzle_elegido["id"])

        return puzzle_elegido