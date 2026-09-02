import chess


class ChessManager:
    """
    Gestor central de la lógica de ajedrez y validación de puzles.
    Actúa como el 'Modelo' en el patrón MVC, manteniendo el estado puro del tablero
    sin interferir con la representación gráfica.
    """

    def __init__(self):
        # Instancia del tablero oficial de ajedrez[cite: 1]
        self.board = chess.Board()
        self.casilla_seleccionada = None
        self.movimientos_validos = []
        self.solucion = []
        self.color_jugador = None

        # Rastrea en qué movimiento de la solución nos encontramos[cite: 1]
        self.paso_actual = 0

        # Estados posibles: "ESPERANDO", "JUGANDO", "VICTORIA", "DERROTA"[cite: 1]
        self.estado_puzzle = "ESPERANDO"
        self.movimiento_fallado = ""

        # Almacena el diccionario completo con los metadatos del puzle (ELO, popularidad, temas)[cite: 1]
        self.info_puzzle = None

    def cargar_puzzle(self, puzzle: dict) -> None:
        """
        Carga la notación FEN en el tablero y prepara la máquina de estados.

        Discrimina automáticamente entre puzles estándar (que exigen forzar el
        movimiento trágico del rival) y las lecciones interactivas (donde el FEN
        ya posiciona al jugador en su turno de ataque).

        Args:
            puzzle (dict): Estructura de datos que contiene 'fen', la secuencia
                           ganadora 'moves' y metadatos identificativos como 'id'.
        """
        self.board.set_fen(puzzle['fen'])
        self.solucion = puzzle['moves']
        self.info_puzzle = puzzle

        # ¡El escudo lógico! Verificamos el pasaporte del puzle
        es_leccion_teorica = puzzle.get('id') == 'Leccion'

        # Si viene de Lichess y tiene movimientos, la máquina usurpa el primer turno
        if not es_leccion_teorica and len(self.solucion) > 0:
            movimiento_rival = chess.Move.from_uci(self.solucion[0])
            self.board.push(movimiento_rival)
            self.paso_actual = 1
        else:
            # En la Escuela, el tablero está congelado esperando tu genialidad
            self.paso_actual = 0

        self.color_jugador = self.board.turn
        self.casilla_seleccionada = None
        self.movimientos_validos = []
        self.estado_puzzle = "JUGANDO"
        self.movimiento_fallado = ""

    def obtener_pieza_movimiento_esperado_jugador(self) -> chess.Piece | None:
        """Devuelve la pieza que debe mover el jugador en el paso actual.

        Returns:
            chess.Piece | None: Pieza situada en la casilla de origen del
                siguiente movimiento esperado, o None si no es el turno del
                jugador o el puzzle ya no está activo.
        """
        if (
            self.estado_puzzle != "JUGANDO"
            or self.paso_actual >= len(self.solucion)
            or self.color_jugador is None
            or self.board.turn != self.color_jugador
        ):
            return None

        try:
            movimiento = chess.Move.from_uci(self.solucion[self.paso_actual])
        except (ValueError, TypeError):
            return None

        if movimiento not in self.board.legal_moves:
            return None

        pieza = self.board.piece_at(movimiento.from_square)
        if pieza is None or pieza.color != self.color_jugador:
            return None

        return pieza

    def ejecutar_movimiento_enemigo(self):
        """
        Ejecuta el movimiento de la IA (el rival) basándose en la lista de soluciones.
        Avanza el estado del puzle si este movimiento concluye la táctica.

        Returns:
            str o None: El movimiento UCI ejecutado, o None si el juego terminó.
        """
        if self.estado_puzzle != "JUGANDO" or self.paso_actual >= len(self.solucion):
            return None

        mov = self.solucion[self.paso_actual]
        move = chess.Move.from_uci(mov)

        if move in self.board.legal_moves:
            self.board.push(move)
            self.paso_actual += 1
            # Si tras mover la IA ya no hay más pasos, el puzle se ha completado con éxito[cite: 1]
            if self.paso_actual >= len(self.solucion):
                self.estado_puzzle = "VICTORIA"
        return mov

    def seleccionar_casilla(self, casilla_str):
        """
        Selecciona una casilla y calcula todos los movimientos legales desde ella.

        Args:
            casilla_str (str): Coordenada de la casilla en texto (ej. "e2").
        """
        if self.estado_puzzle != "JUGANDO": return
        casilla_idx = chess.parse_square(casilla_str)
        pieza = self.board.piece_at(casilla_idx)

        # Solo permitimos seleccionar si hay una pieza y pertenece al jugador del turno actual[cite: 1]
        if pieza and pieza.color == self.board.turn:
            self.casilla_seleccionada = casilla_str
            movimientos = list(self.board.legal_moves)
            # Filtramos los movimientos legales para mostrar solo los destinos válidos desde el origen[cite: 1]
            self.movimientos_validos = [
                chess.square_name(m.to_square) for m in movimientos if m.from_square == casilla_idx
            ]
        else:
            self.casilla_seleccionada = None
            self.movimientos_validos = []

    def intentar_movimiento_jugador(self, casilla_destino_str: str) -> bool:
        """
        Valida y ejecuta el intento de movimiento del usuario cruzándolo con la solución.

        Este método compara las coordenadas de origen (previamente seleccionadas) y
        destino (argumento) con el siguiente movimiento exigido por el puzle.
        Gestiona explícitamente la coronación de peones inyectando la pieza
        promocionada según lo dicta la notación UCI de la solución.

        Args:
            casilla_destino_str (str): Cadena de texto que representa la coordenada
                                       de destino en notación algebraica (ej. 'e1').

        Returns:
            bool: True si el movimiento era correcto y se ejecutó en el tablero,
                  False si el movimiento fue incorrecto, ilegal o no hay selección.
        """
        # Verificamos que haya una pieza seleccionada y el juego esté activo[cite: 2]
        if not self.casilla_seleccionada or self.estado_puzzle != "JUGANDO":
            return False

        # Convertimos las coordenadas alfanuméricas a índices numéricos de chess-python[cite: 2]
        origen_idx = chess.parse_square(self.casilla_seleccionada)
        destino_idx = chess.parse_square(casilla_destino_str)

        # Extraemos el movimiento correcto esperado en el paso actual[cite: 2]
        movimiento_esperado = self.solucion[self.paso_actual]
        esperado_origen = chess.parse_square(movimiento_esperado[:2])
        esperado_destino = chess.parse_square(movimiento_esperado[2:4])

        # Verificamos si el origen y destino coinciden con la solución del puzle
        if origen_idx == esperado_origen and destino_idx == esperado_destino:
            # Si el movimiento esperado tiene 5 caracteres (ej. 'e2e1q'), es una coronación[cite: 2]
            if len(movimiento_esperado) == 5:
                pieza_promocion = chess.PIECE_SYMBOLS.index(movimiento_esperado[4])
                move = chess.Move(origen_idx, destino_idx, promotion=pieza_promocion)
            else:
                move = chess.Move(origen_idx, destino_idx)

            # Si el movimiento construido es legal, lo aplicamos al tablero oficial[cite: 2]
            if move in self.board.legal_moves:
                self.board.push(move)
                self.paso_actual += 1
                self.casilla_seleccionada = None
                self.movimientos_validos = []

                # Si hemos agotado la lista de la solución, el jugador gana el puzle[cite: 2]
                if self.paso_actual >= len(self.solucion):
                    self.estado_puzzle = "VICTORIA"
                return True

        # Si no era la solución correcta, debemos evaluar si fue un error legal
        move_test = chess.Move(origen_idx, destino_idx)

        # Si el movimiento falla por ser coronación omitida, probamos forzando a Reina[cite: 2]
        if move_test not in self.board.legal_moves:
            move_test = chess.Move(origen_idx, destino_idx, promotion=chess.QUEEN)

        # Si el movimiento erróneo es al menos legal en ajedrez, se penaliza como DERROTA[cite: 2]
        if move_test in self.board.legal_moves:
            self.estado_puzzle = "DERROTA"
            self.movimiento_fallado = movimiento_esperado
            self.casilla_seleccionada = None
            self.movimientos_validos = []
            return False

        # Si el movimiento ni siquiera es legal, lo ignoramos silenciosamente[cite: 2]
        return False