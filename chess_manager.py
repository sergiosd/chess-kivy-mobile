import chess


class ChessManager:
    def __init__(self):
        self.board = chess.Board()
        self.casilla_seleccionada = None
        self.movimientos_validos = []
        self.solucion = []
        self.paso_actual = 0
        self.estado_puzzle = "ESPERANDO"
        self.movimiento_fallado = ""
        self.info_puzzle = None  # NUEVO: Variable para guardar toda la información

    def cargar_puzzle(self, puzzle):
        """Carga el FEN y prepara el tablero ejecutando el movimiento inicial del rival."""
        self.board.set_fen(puzzle['fen'])
        self.solucion = puzzle['moves']
        self.info_puzzle = puzzle

        # EL TRUCO MAGISTRAL: El primer movimiento de la lista es del enemigo
        if len(self.solucion) > 0:
            movimiento_rival = chess.Move.from_uci(self.solucion[0])
            self.board.push(movimiento_rival)
            # El jugador empieza a interactuar a partir del paso 1
            self.paso_actual = 1
        else:
            self.paso_actual = 0

        self.casilla_seleccionada = None
        self.movimientos_validos = []
        self.estado_puzzle = "JUGANDO"
        self.movimiento_fallado = ""

    def ejecutar_movimiento_enemigo(self):
        if self.estado_puzzle != "JUGANDO" or self.paso_actual >= len(self.solucion):
            return None

        mov = self.solucion[self.paso_actual]
        move = chess.Move.from_uci(mov)
        if move in self.board.legal_moves:
            self.board.push(move)
            self.paso_actual += 1
            if self.paso_actual >= len(self.solucion):
                self.estado_puzzle = "VICTORIA"
        return mov

    def seleccionar_casilla(self, casilla_str):
        if self.estado_puzzle != "JUGANDO": return
        casilla_idx = chess.parse_square(casilla_str)
        pieza = self.board.piece_at(casilla_idx)

        if pieza and pieza.color == self.board.turn:
            self.casilla_seleccionada = casilla_str
            movimientos = list(self.board.legal_moves)
            self.movimientos_validos = [
                chess.square_name(m.to_square) for m in movimientos if m.from_square == casilla_idx
            ]
        else:
            self.casilla_seleccionada = None
            self.movimientos_validos = []

    def intentar_movimiento_jugador(self, casilla_destino_str):
        if not self.casilla_seleccionada or self.estado_puzzle != "JUGANDO": return False

        origen_idx = chess.parse_square(self.casilla_seleccionada)
        destino_idx = chess.parse_square(casilla_destino_str)
        move = chess.Move(origen_idx, destino_idx)

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

                if self.paso_actual >= len(self.solucion):
                    self.estado_puzzle = "VICTORIA"
                return True
            else:
                self.estado_puzzle = "DERROTA"
                self.movimiento_fallado = movimiento_esperado
                self.casilla_seleccionada = None
                self.movimientos_validos = []
                return False
        return False