import csv
import random
import json
import os


class PuzzleManager:
    """
    Gestor de la base de datos de puzles.
    Implementa un sistema de memoria dual (JSON + perfiles) para cachear tácticas
    en función del ELO del usuario y evitar repeticiones a nivel global.
    """

    def __init__(self, ruta_csv="lichess_db_puzzle.csv",
                 ruta_memoria="memoria_puzzles_global.json"):
        self.ruta_csv = ruta_csv
        self.ruta_memoria = ruta_memoria

        # Diccionario para almacenar tácticas en memoria RAM clasificadas por rangos de ELO[cite: 5]
        self.cache_puzzles = {}
        # Carga del disco los IDs de los puzles que ya han salido alguna vez[cite: 5]
        self.puzzles_vistos_global = self.cargar_memoria_global()
        print("Iniciando Gestor de Puzzles Premium con Memoria Dual...")

    def cargar_memoria_global(self):
        """Recupera el set de IDs jugados desde el JSON local[cite: 5]."""
        if os.path.exists(self.ruta_memoria):
            with open(self.ruta_memoria, "r") as f:
                try:
                    return set(json.load(f))
                except json.JSONDecodeError:
                    return set()
        return set()

    def guardar_memoria_global(self):
        """Persiste el set actual de IDs jugados volcándolo a JSON[cite: 5]."""
        with open(self.ruta_memoria, "w") as f:
            json.dump(list(self.puzzles_vistos_global), f)

    def registrar_puzzle_global(self, id_puzzle):
        """Añade un ID completado al registro y actualiza el archivo[cite: 5]."""
        self.puzzles_vistos_global.add(id_puzzle)
        self.guardar_memoria_global()

    def cargar_puzzles_por_elo(self, elo_objetivo, ids_locales, margen=50, cantidad=20, pop_min=0):
        """
        Lee el CSV para extraer un lote de puzles que se ajusten al ELO del jugador.
        Ignora puzles con popularidad baja y los que ya existen en el registro local del usuario.

        Args:
            elo_objetivo (int): Puntuación actual del usuario.
            ids_locales (set): Lista de puzles resueltos por el perfil activo[cite: 5].
            margen (int): Rango de tolerancia ELO (arriba y abajo).
            cantidad (int): Tácticas a precargar en la RAM.
            pop_min (int): Popularidad mínima requerida del puzle.
        """
        elo_real = max(600, elo_objetivo)
        rango_min = elo_real - margen
        rango_max = elo_real + margen
        clave_rango = f"{rango_min}-{rango_max}"

        # Evitamos buscar en el CSV si ya tenemos suficientes puzles en caché[cite: 5]
        if clave_rango not in self.cache_puzzles:
            self.cache_puzzles[clave_rango] = []
        elif len(self.cache_puzzles[clave_rango]) >= cantidad:
            return

        print(f"Cargando tácticas (ELO {rango_min}-{rango_max}, Pop > {pop_min})...")

        candidatos_nuevos = []
        candidatos_reciclados = []
        ids_en_cache = {p["id"] for p in self.cache_puzzles[clave_rango]}

        try:
            with open(self.ruta_csv, mode='r', encoding='utf-8') as archivo:
                lector_csv = csv.reader(archivo)
                next(lector_csv, None)  # Saltar cabeceras

                for fila in lector_csv:
                    if len(fila) < 8: continue

                    id_puzzle = fila[0]
                    try:
                        rating = int(fila[3])
                        pop = int(fila[5])

                        if (rango_min <= rating <= rango_max) and (pop >= pop_min):
                            # Si el usuario ya lo completó o ya lo tenemos precargado, lo saltamos[cite: 5]
                            if id_puzzle in ids_locales or id_puzzle in ids_en_cache:
                                continue

                            # Empaquetamos la metadata en un diccionario manejable[cite: 5]
                            puzzle_dict = {
                                "id": id_puzzle, "fen": fila[1], "moves": fila[2].split(" "),
                                "rating": rating, "popularity": pop, "themes": fila[7]
                            }

                            # Clasificamos según si ya se jugó globalmente (por otros perfiles) o es nuevo[cite: 5]
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

        # Priorizamos inyectar a la caché puzles totalmente inéditos[cite: 5]
        if len(candidatos_nuevos) > 0:
            self.cache_puzzles[clave_rango].extend(candidatos_nuevos)
        # Reciclamos puzles globales si la base de datos se agota para este nivel ELO[cite: 5]
        elif len(candidatos_reciclados) > 0:
            print(f"Memoria global agotada para ELO {rango_min}-{rango_max}. Reciclando...")
            for p in candidatos_reciclados[:cantidad]:
                self.puzzles_vistos_global.discard(p["id"])
            self.guardar_memoria_global()
            self.cache_puzzles[clave_rango].extend(candidatos_reciclados[:cantidad])

    def obtener_puzzle_aleatorio(self, elo_objetivo, ids_locales):
        """
        Extrae de la caché en RAM un puzle aleatorio apropiado para el jugador.

        Returns:
            dict: El diccionario con la información del puzle escogido.
        """
        elo_real = max(600, elo_objetivo)
        clave_rango = f"{elo_real - 50}-{elo_real + 50}"

        # Alimentamos la caché antes de intentar sacar un elemento[cite: 5]
        self.cargar_puzzles_por_elo(elo_real, ids_locales)

        if clave_rango not in self.cache_puzzles or not self.cache_puzzles[clave_rango]:
            return None

        puzzle_elegido = random.choice(self.cache_puzzles[clave_rango])
        # Lo retiramos de la recámara para no repetirlo de forma inminente[cite: 5]
        self.cache_puzzles[clave_rango].remove(puzzle_elegido)
        # Lo fichamos en la memoria global[cite: 5]
        self.registrar_puzzle_global(puzzle_elegido["id"])

        return puzzle_elegido