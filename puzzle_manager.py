import csv
import random
import json
import os


class GestorProgresionPop:
    """
    Motor lógico para la curva de dificultad basada en la popularidad.

    Implementa una máquina de estados que define rangos estrictos de popularidad.
    Evalúa las victorias y derrotas para ascender o descender, aislando esta
    burocracia de los controladores gráficos.
    """

    # La implacable escalera hacia el infierno táctico
    ESCALAS = [
        (100, 100), (98, 99), (96, 97), (94, 95), (92, 93), (90, 91),
        (88, 89), (86, 87), (84, 85), (82, 83), (80, 81), (78, 79),
        (76, 77), (74, 75), (72, 73), (70, 71), (60, 69)
    ]

    @staticmethod
    def calcular_siguiente_escala(escala_actual, victorias_100, victoria):
        """
        Calcula el nuevo estado de progresión tras resolver un puzle.

        Args:
            escala_actual (int): Índice actual en la lista ESCALAS.
            victorias_100 (int): Racha acumulada en el nivel inicial (0 a 3).
            victoria (bool): True si el jugador resolvió el puzle.

        Returns:
            tuple: (nueva_escala, nuevas_victorias_100) listas para persistir.
        """
        if victoria:
            if escala_actual == 0:
                victorias_100 += 1
                # Si llega a 3 aciertos acumulados, ¡despega hacia la escala 1!
                if victorias_100 >= 3:
                    return 1, 0
                return 0, victorias_100
            else:
                nueva_escala = min(escala_actual + 1, len(GestorProgresionPop.ESCALAS) - 1)
                return nueva_escala, 0
        else:
            if escala_actual == 0:
                # Los fallos no reinician los aciertos en la fosa del nivel 0
                return 0, victorias_100
            else:
                nueva_escala = max(escala_actual - 1, 0)
                return nueva_escala, 0


class PuzzleManager:
    """
    Gestor de la base de datos de puzles con búsqueda expansiva.

    Implementa un sistema de memoria dual (JSON + perfiles) para cachear tácticas
    en función del ELO del usuario (desde 0) y su popularidad dinámica, evitando
    la repetición de tácticas mediante un registro global[cite: 10].
    """

    def __init__(self, ruta_csv="lichess_db_puzzle.csv",
                 ruta_memoria="memoria_puzzles_global.json"):
        """
        Inicializa el gestor y prepara la caché RAM.

        Args:
            ruta_csv (str): Ruta a la asquerosa base de datos CSV[cite: 10].
            ruta_memoria (str): Ruta al inestable archivo JSON de memoria global[cite: 10].
        """
        self.ruta_csv = ruta_csv
        self.ruta_memoria = ruta_memoria

        # Diccionario para almacenar tácticas en memoria RAM clasificadas[cite: 10]
        self.cache_puzzles = {}
        # Carga del disco los IDs de los puzles que ya han salido alguna vez[cite: 10]
        self.puzzles_vistos_global = self.cargar_memoria_global()
        print("Iniciando Gestor de Puzzles Premium con Búsqueda Concéntrica...")

    def cargar_memoria_global(self):
        """
        Recupera el set de IDs jugados desde el JSON local.

        Returns:
            set: Conjunto de IDs ya jugados globalmente[cite: 10].
        """
        if os.path.exists(self.ruta_memoria):
            with open(self.ruta_memoria, "r", encoding="utf-8") as f:
                try:
                    return set(json.load(f))
                except json.JSONDecodeError:
                    return set()
        return set()

    def guardar_memoria_global(self):
        """Persiste el set actual de IDs jugados volcándolo a JSON[cite: 10]."""
        with open(self.ruta_memoria, "w", encoding="utf-8") as f:
            json.dump(list(self.puzzles_vistos_global), f)

    def registrar_puzzle_global(self, id_puzzle):
        """
        Añade un ID completado al registro y actualiza el archivo en disco.

        Args:
            id_puzzle (str): El identificador único del puzle resuelto[cite: 10].
        """
        self.puzzles_vistos_global.add(id_puzzle)
        self.guardar_memoria_global()

    def cargar_puzzles_por_elo(self, elo_objetivo, ids_locales, cantidad=20, pop_min=100,
                               pop_max=100, temas_prohibidos=None):
        """
        Busca puzles aplicando una expansión concéntrica de ELO, purgados de temas aburridos.

        Filtra rígidamente por popularidad y excluye los temas tácticos mediocres
        (como mates en pasillo) definidos en la lista negra. Si el deficiente
        archivo CSV no tiene puzles en +/- 50 de ELO, el algoritmo agrupa los
        puzles en anillos de distancia hacia afuera.

        Args:
            elo_objetivo (int): Puntuación del usuario (partiendo desde 0 absoluto).
            ids_locales (set): Puzles ya resueltos por el perfil activo[cite: 10].
            cantidad (int): Tácticas a extraer para la caché en RAM[cite: 10].
            pop_min (int): Límite inferior de la asquerosa popularidad.
            pop_max (int): Límite superior de popularidad.
            temas_prohibidos (list, optional): Lista de strings con temas a excluir (ej. ['backRankMate']).
        """
        if temas_prohibidos is None:
            # Lista negra por defecto dictada por el maestro arquitecto
            temas_prohibidos = ['backRankMate'] #, 'mateIn1', 'short']

        elo_real = max(0, elo_objetivo)
        clave_rango = f"elo_{elo_real}_pop_{pop_min}_{pop_max}"

        if clave_rango not in self.cache_puzzles:
            self.cache_puzzles[clave_rango] = []
        elif len(self.cache_puzzles[clave_rango]) >= cantidad:
            return

        print(
            f"Buscando concéntricamente (ELO Objetivo {elo_real}, Pop {pop_min}-{pop_max}) purgado de basura...")

        anillos_distancia = {}
        ids_en_cache = {p["id"] for p in self.cache_puzzles[clave_rango]}

        try:
            with open(self.ruta_csv, mode='r', encoding='utf-8') as archivo:
                lector_csv = csv.reader(archivo)
                next(lector_csv, None)  # Saltar las inútiles cabeceras[cite: 10]

                for fila in lector_csv:
                    if len(fila) < 8: continue

                    id_puzzle = fila[0]
                    try:
                        rating = int(fila[3])
                        pop = int(fila[5])
                        temas_csv = fila[7].split(
                            " ")  # Extraemos la lista de temas del CSV[cite: 10]

                        # El filtro sagrado de popularidad
                        if pop_min <= pop <= pop_max:
                            if id_puzzle in ids_locales or id_puzzle in ids_en_cache:
                                continue

                            # ¡La guillotina táctica! Si tiene algún tema prohibido, a la basura va
                            if any(tema_basura in temas_csv for tema_basura in temas_prohibidos):
                                continue

                            distancia_elo = abs(rating - elo_real)
                            anillo = (distancia_elo // 50) * 50

                            puzzle_dict = {
                                "id": id_puzzle, "fen": fila[1], "moves": fila[2].split(" "),
                                "rating": rating, "popularity": pop, "themes": fila[7]
                            }

                            if anillo not in anillos_distancia:
                                anillos_distancia[anillo] = []
                            anillos_distancia[anillo].append(puzzle_dict)

                    except ValueError:
                        continue

        except FileNotFoundError:
            print(
                f"ERROR: ¡Por el kernel panic de Linux! No encuentro la base de datos {self.ruta_csv}.")

        for anillo in sorted(anillos_distancia.keys()):
            candidatos = anillos_distancia[anillo]
            import random
            random.shuffle(candidatos)

            self.cache_puzzles[clave_rango].extend(candidatos[:cantidad])
            if len(self.cache_puzzles[clave_rango]) >= cantidad:
                break

    def obtener_puzzle_aleatorio(self, elo_objetivo, ids_locales, pop_min=100, pop_max=100):
        """
        Extrae de la caché en RAM un puzle aleatorio apropiado y purificado.

        Propaga los límites de popularidad hacia el motor de búsqueda
        concéntrica para mantener la curva de dificultad intacta y blindada.

        Args:
            elo_objetivo (int): Puntuación actual del usuario.
            ids_locales (set): Puzles ya resueltos por el perfil activo[cite: 10].
            pop_min (int): Límite inferior de la popularidad.
            pop_max (int): Límite superior de la popularidad.

        Returns:
            dict o None: El diccionario con la información del puzle escogido[cite: 10].
        """
        elo_real = max(0, elo_objetivo)
        clave_rango = f"elo_{elo_real}_pop_{pop_min}_{pop_max}"

        # Invocamos la fuerza bruta concéntrica (que ahora viene con lista negra de serie)
        self.cargar_puzzles_por_elo(
            elo_objetivo=elo_real,
            ids_locales=ids_locales,
            pop_min=pop_min,
            pop_max=pop_max
        )

        if clave_rango not in self.cache_puzzles or not self.cache_puzzles[clave_rango]:
            return None

        import random
        puzzle_elegido = random.choice(self.cache_puzzles[clave_rango])
        self.cache_puzzles[clave_rango].remove(puzzle_elegido)

        self.registrar_puzzle_global(puzzle_elegido["id"])

        return puzzle_elegido

    def obtener_puzzle_por_id(self, id_buscado: str) -> dict:
        """
        Busca y extrae un puzle específico directamente por su identificador único.

        Ignora los filtros de popularidad, ELO o temas. Realiza una búsqueda
        lineal en el archivo CSV para localizar el ID exacto y devuelve el
        diccionario formateado, ideal para test de integración o depuración[cite: 5].

        Args:
            id_buscado (str): El identificador único del puzle (ej. '1qC2F').

        Returns:
            dict: Diccionario con los datos del puzle ('id', 'fen', 'moves', etc.).
                  Devuelve un diccionario vacío si no se encuentra el ID o hay un error.
        """
        try:
            # Abrimos el infernal y pesado archivo CSV[cite: 5]
            with open(self.ruta_csv, mode='r', encoding='utf-8') as archivo:
                lector_csv = csv.reader(archivo)
                next(lector_csv, None)  # Nos saltamos las inútiles cabeceras

                for fila in lector_csv:
                    # Validamos que la fila no esté corrupta[cite: 5]
                    if len(fila) < 8:
                        continue

                    # ¡Bingo! Encontramos la aguja en el pajar de texto
                    if fila[0] == id_buscado:
                        return {
                            "id": fila[0],
                            "fen": fila[1],
                            "moves": fila[2].split(" "),
                            "rating": int(fila[3]),
                            "popularity": int(fila[5]),
                            "themes": fila[7]
                        }
        except FileNotFoundError:
            print(
                f"ERROR: ¡Por la sandalia de un romano! No encuentro la base de datos {self.ruta_csv}.")

        return {}

    def obtener_puzzle_practica(self, id_leccion: str, archivo_csv: str,
                                perfil_usuario: dict) -> dict:
        """
        Extrae un puzle aleatorio de la base de datos local asociada a la lección.

        Aplica teoría de conjuntos para purgar los ejercicios consumidos. Corrige
        el enrutamiento al directorio 'databases' y separa conceptualmente
        la ausencia física del archivo del agotamiento matemático de puzles.

        Args:
            id_leccion (str): Identificador único de la lección (ej. 'tac_02').
            archivo_csv (str): Nombre del archivo físico que contiene los puzles.
            perfil_usuario (dict): Estado actual del jugador cargado en memoria.

        Returns:
            dict: Metadatos y FEN del puzle formateados para el motor.
            Devuelve un diccionario vacío {} si el archivo no existe o está corrupto.
            Devuelve None EXCLUSIVAMENTE si el jugador ha resuelto todos los puzles.
        """
        import os
        import csv
        import random

        # Enrutamos estrictamente al directorio de bases de datos masivas
        ruta_completa = os.path.join('databases', archivo_csv)

        if not os.path.exists(ruta_completa):
            print(f"ERROR CRÍTICO: No se encuentra el CSV de tácticas en {ruta_completa}")
            return {}

        datos_leccion = perfil_usuario.get("practica_lecciones", {}).get(id_leccion, {})
        ids_excluidos = set(datos_leccion.get("resueltos", [])) | set(
            datos_leccion.get("fallados", []))

        puzzles_disponibles = []

        try:
            with open(ruta_completa, mode='r', encoding='utf-8') as archivo:
                lector_csv = csv.reader(archivo)
                next(lector_csv, None)  # Purgamos la cabecera

                for fila in lector_csv:
                    if len(fila) < 8:
                        continue

                    id_puzzle = fila[0]
                    if id_puzzle not in ids_excluidos:
                        puzzles_disponibles.append({
                            "id": id_puzzle,
                            "fen": fila[1],
                            "moves": fila[2].split(" "),
                            "rating": int(fila[3]) if fila[3].isdigit() else 1000,
                            "popularity": int(fila[5]) if fila[5].isdigit() else 100,
                            "themes": fila[7]
                        })
        except Exception as e:
            print(f"ERROR: Fallo al leer el CSV de práctica: {e}")
            return {}

        if not puzzles_disponibles:
            return None

        return random.choice(puzzles_disponibles)