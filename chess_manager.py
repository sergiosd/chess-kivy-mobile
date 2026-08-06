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

        # Rastrea en qué movimiento de la solución nos encontramos[cite: 1]
        self.paso_actual = 0

        # Estados posibles: "ESPERANDO", "JUGANDO", "VICTORIA", "DERROTA"[cite: 1]
        self.estado_puzzle = "ESPERANDO"
        self.movimiento_fallado = ""

        # Almacena el diccionario completo con los metadatos del puzle (ELO, popularidad, temas)[cite: 1]
        self.info_puzzle = None

    def cargar_puzzle(self, puzzle):
        """
        Carga la notación FEN en el tablero y ejecuta el movimiento de preparación del rival.

        Args:
            puzzle (dict): Diccionario que contiene 'fen' y la lista de movimientos 'moves'.
        """
        self.board.set_fen(puzzle['fen'])
        self.solucion = puzzle['moves']
        self.info_puzzle = puzzle

        # EL TRUCO MAGISTRAL: El primer movimiento de la lista siempre es del enemigo.
        # Al aplicarlo, dejamos el tablero listo para que el jugador responda[cite: 1].
        if len(self.solucion) > 0:
            movimiento_rival = chess.Move.from_uci(self.solucion[0])
            self.board.push(movimiento_rival)
            # El jugador empieza a interactuar a partir del índice 1 (su primer turno)[cite: 1]
            self.paso_actual = 1
        else:
            self.paso_actual = 0

        self.casilla_seleccionada = None
        self.movimientos_validos = []
        self.estado_puzzle = "JUGANDO"
        self.movimiento_fallado = ""

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

    def intentar_movimiento_jugador(self, casilla_destino_str):
        """
        Intenta mover la pieza seleccionada a la casilla de destino y comprueba
        si coincide con el movimiento exigido por el puzle.

        Args:
            casilla_destino_str (str): Coordenada del destino (ej. "e4").

        Returns:
            bool: True si el movimiento era correcto, False si fue erróneo.
        """
        if not self.casilla_seleccionada or self.estado_puzzle != "JUGANDO": return False

        origen_idx = chess.parse_square(self.casilla_seleccionada)
        destino_idx = chess.parse_square(casilla_destino_str)
        move = chess.Move(origen_idx, destino_idx)

        # Promoción automática a Reina si el movimiento base no es legal pero coronando sí lo es[cite: 1]
        if move not in self.board.legal_moves:
            move = chess.Move(origen_idx, destino_idx, promotion=chess.QUEEN)

        if move in self.board.legal_moves:
            movimiento_uci = move.uci()
            movimiento_esperado = self.solucion[self.paso_actual]

            if movimiento_uci == movimiento_esperado:
                self.board.push(move)
                self.paso_actual += 1
                self.casilla_seleccionada = None
                self.movimientos_validos = []

                # Comprobamos si el jugador dio el golpe final del puzle[cite: 1]
                if self.paso_actual >= len(self.solucion):
                    self.estado_puzzle = "VICTORIA"
                return True
            else:
                # El movimiento era legal en ajedrez, pero incorrecto para resolver el puzle[cite: 1]
                self.estado_puzzle = "DERROTA"
                self.movimiento_fallado = movimiento_esperado
                self.casilla_seleccionada = None
                self.movimientos_validos = []
                return False
        return False