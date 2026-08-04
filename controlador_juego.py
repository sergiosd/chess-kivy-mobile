# controlador_juego.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
import chess


class CasillaTablero(ButtonBehavior, FloatLayout):
    """Componente visual purgado de las inestables Properties de Kivy."""

    def __init__(self, nombre_casilla, controlador, **kwargs):
        super().__init__(**kwargs)
        self.nombre_casilla = nombre_casilla
        self.controlador = controlador

    def on_press(self):
        self.controlador.al_tocar_casilla(self.nombre_casilla)


class ControladorTablero(BoxLayout):
    def __init__(self, gestor_ajedrez, **kwargs):
        super().__init__(**kwargs)
        self.gestor_ajedrez = gestor_ajedrez
        self.diccionario_casillas = {}

        self.mapa_imagenes = {
            'P': 'assets/pieces/blanco_peon.png', 'p': 'assets/pieces/negro_peon.png',
            'N': 'assets/pieces/blanco_caballo.png', 'n': 'assets/pieces/negro_caballo.png',
            'B': 'assets/pieces/blanco_alfil.png', 'b': 'assets/pieces/negro_alfil.png',
            'R': 'assets/pieces/blanco_torre.png', 'r': 'assets/pieces/negro_torre.png',
            'Q': 'assets/pieces/blanco_reina.png', 'q': 'assets/pieces/negro_reina.png',
            'K': 'assets/pieces/blanco_rey.png', 'k': 'assets/pieces/negro_rey.png'
        }

        self.inicializar_tablero()

    def inicializar_tablero(self):
        cuadricula = self.ids.grid_tablero
        cuadricula.clear_widgets()

        for fila in range(7, -1, -1):
            for col in range(8):
                nombre_casilla = chess.square_name(chess.square(col, fila))
                casilla = CasillaTablero(nombre_casilla=nombre_casilla, controlador=self)

                es_clara = (fila + col) % 2 != 0
                ruta_limpia = "assets/squares/casilla_clara.png" if es_clara else "assets/squares/casilla_oscura.png"

                # INYECCIÓN DIRECTA: Nos saltamos la burocracia de las variables de Kivy
                casilla.ids.img_fondo.source = ruta_limpia
                casilla.ids.img_fondo.color = [1, 1, 1, 1]

                self.registrar_casilla(nombre_casilla, casilla)
                cuadricula.add_widget(casilla)

    def registrar_casilla(self, nombre_casilla, widget_casilla):
        self.diccionario_casillas[nombre_casilla] = widget_casilla

    def actualizar_piezas_visuales(self):
        tablero = self.gestor_ajedrez.board

        for nombre_casilla, widget in self.diccionario_casillas.items():
            indice_casilla = chess.parse_square(nombre_casilla)
            pieza = tablero.piece_at(indice_casilla)

            if pieza:
                widget.ids.img_pieza.source = self.mapa_imagenes.get(pieza.symbol(), '')
            else:
                widget.ids.img_pieza.source = ''

        if self.gestor_ajedrez.info_puzzle:
            self.ids.lbl_info.text = f"Nivel: {self.gestor_ajedrez.info_puzzle.get('rating', '--')} ELO"

    def al_tocar_casilla(self, nombre_casilla):
        gestor = self.gestor_ajedrez

        if gestor.casilla_seleccionada and nombre_casilla in gestor.movimientos_validos:
            exito = gestor.intentar_movimiento_jugador(nombre_casilla)

            self.limpiar_iluminacion()
            self.actualizar_piezas_visuales()

            if exito:
                if gestor.estado_puzzle == "VICTORIA":
                    self.ids.lbl_estado.text = "¡PUZZLE COMPLETADO!"
                    self.ids.lbl_estado.color = [0, 1, 0, 1]
                else:
                    self.ids.lbl_estado.text = "¡Excelente! Responde la IA..."
                    self.ids.lbl_estado.color = [1, 1, 0, 1]
                    Clock.schedule_once(self.procesar_respuesta_ia, 0.7)
            else:
                self.ids.lbl_estado.text = "¡MOVIMIENTO INCORRECTO!"
                self.ids.lbl_estado.color = [1, 0, 0, 1]

        else:
            gestor.seleccionar_casilla(nombre_casilla)
            self.iluminar_casillas()

    def procesar_respuesta_ia(self, dt):
        movimiento = self.gestor_ajedrez.ejecutar_movimiento_enemigo()

        if movimiento:
            self.actualizar_piezas_visuales()

            if self.gestor_ajedrez.estado_puzzle == "VICTORIA":
                self.ids.lbl_estado.text = "¡PUZZLE COMPLETADO!"
                self.ids.lbl_estado.color = [0, 1, 0, 1]
            else:
                self.ids.lbl_estado.text = "¡Tu turno! Continúa."
                self.ids.lbl_estado.color = [0.96, 0.96, 0.98, 1]

    def iluminar_casillas(self):
        self.limpiar_iluminacion()
        gestor = self.gestor_ajedrez

        if gestor.casilla_seleccionada:
            casilla_origen = self.diccionario_casillas.get(gestor.casilla_seleccionada)
            if casilla_origen:
                casilla_origen.ids.img_fondo.color = [1, 1, 0, 1]

            for destino in gestor.movimientos_validos:
                casilla_destino = self.diccionario_casillas.get(destino)
                if casilla_destino:
                    casilla_destino.ids.img_fondo.color = [0, 1, 0, 1]

    def limpiar_iluminacion(self):
        for widget in self.diccionario_casillas.values():
            widget.ids.img_fondo.color = [1, 1, 1, 1]