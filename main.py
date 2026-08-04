from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
from kivy.clock import Clock
import chess

from chess_manager import ChessManager
from puzzle_manager import PuzzleManager

Window.size = (450, 800)

Builder.load_string("""
<Casilla>:
    ruta_fondo: ''
    ruta_pieza: ''
    color_tinte: 1, 1, 1, 1

    Image:
        source: root.ruta_fondo
        color: root.color_tinte
        allow_stretch: True
        keep_ratio: False

    Image:
        source: root.ruta_pieza
        opacity: 1 if root.ruta_pieza else 0
        allow_stretch: True
        keep_ratio: True
        size_hint: 0.85, 0.85
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}

<VistaTablero>:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: 0.1, 0.15, 0.2, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: 'SALA DE MANDO'
        font_size: '28sp'
        bold: True
        size_hint_y: 0.15
        color: 0, 0.9, 0.8, 1

    AnchorLayout:
        size_hint_y: 0.55
        GridLayout:
            id: cuadricula_tablero
            cols: 8
            rows: 8
            size_hint: None, None
            width: min(root.width - dp(40), root.height * 0.55)
            height: self.width

    BoxLayout:
        orientation: 'vertical'
        size_hint_y: 0.30
        spacing: dp(10)
        Label:
            id: lbl_estado
            text: 'Esperando despliegue...'
            font_size: '20sp'
            bold: True
            color: 0.9, 0.9, 0.9, 1
        Label:
            id: lbl_info
            text: 'Nivel: -- | ID: --'
            font_size: '16sp'
            color: 0.7, 0.7, 0.8, 1
        Button:
            text: 'SIGUIENTE PUZZLE'
            size_hint_y: None
            height: dp(50)
            background_color: 0.2, 0.6, 0.8, 1
            # Llamamos al método directamente desde la interfaz
            on_press: root.cargar_siguiente_puzzle()
""")


class Casilla(ButtonBehavior, RelativeLayout):
    def __init__(self, nombre_casilla, controlador, **kwargs):
        super().__init__(**kwargs)
        self.nombre_casilla = nombre_casilla
        self.controlador = controlador

    def on_press(self):
        self.controlador.al_tocar_casilla(self.nombre_casilla)


class VistaTablero(BoxLayout):
    def __init__(self, gestor_ajedrez, gestor_puzzles, **kwargs):
        super().__init__(**kwargs)
        self.gestor_ajedrez = gestor_ajedrez
        self.gestor_puzzles = gestor_puzzles  # Inyectamos el gestor de puzzles aquí
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
        self.actualizar_piezas_visuales()

    def inicializar_tablero(self):
        cuadricula = self.ids.cuadricula_tablero
        cuadricula.clear_widgets()
        self.diccionario_casillas.clear()

        # Descubrimos de qué color jugamos tras el movimiento inicial de la IA
        juega_blancas = self.gestor_ajedrez.board.turn

        # Rotación matemática del tablero
        filas = range(7, -1, -1) if juega_blancas else range(8)
        columnas = range(8) if juega_blancas else range(7, -1, -1)

        for fila in filas:
            for col in columnas:
                nombre_casilla = chess.square_name(chess.square(col, fila))
                casilla = Casilla(nombre_casilla=nombre_casilla, controlador=self)

                es_clara = (fila + col) % 2 != 0
                casilla.ruta_fondo = "assets/squares/casilla_clara.png" if es_clara else "assets/squares/casilla_oscura.png"

                self.diccionario_casillas[nombre_casilla] = casilla
                cuadricula.add_widget(casilla)

    def cargar_siguiente_puzzle(self):
        """Solicita un puzzle nuevo, lo inyecta en el cerebro y repinta la vista."""
        nuevo_puzzle = self.gestor_puzzles.obtener_puzzle_aleatorio(1000, set())
        if nuevo_puzzle:
            self.gestor_ajedrez.cargar_puzzle(nuevo_puzzle)
            # Reconstruimos las casillas por si el nuevo puzzle cambia nuestro color
            self.inicializar_tablero()
            self.actualizar_piezas_visuales()
            self.ids.lbl_estado.text = "¡NUEVO DESPLIEGUE!"
            self.ids.lbl_estado.color = [0.9, 0.9, 0.9, 1]

    def actualizar_piezas_visuales(self):
        tablero = self.gestor_ajedrez.board

        for nombre_casilla, widget in self.diccionario_casillas.items():
            indice_casilla = chess.parse_square(nombre_casilla)
            pieza = tablero.piece_at(indice_casilla)

            if pieza:
                widget.ruta_pieza = self.mapa_imagenes.get(pieza.symbol(), '')
            else:
                widget.ruta_pieza = ''

        info = self.gestor_ajedrez.info_puzzle
        if info:
            self.ids.lbl_info.text = f"Nivel: {info.get('rating', '--')} | ID: {info.get('id', '--')}"

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
                self.ids.lbl_estado.color = [0.9, 0.9, 0.9, 1]

    def iluminar_casillas(self):
        self.limpiar_iluminacion()
        gestor = self.gestor_ajedrez

        if gestor.casilla_seleccionada:
            casilla_origen = self.diccionario_casillas.get(gestor.casilla_seleccionada)
            if casilla_origen:
                casilla_origen.color_tinte = [1, 1, 0, 1]

            for destino in gestor.movimientos_validos:
                casilla_destino = self.diccionario_casillas.get(destino)
                if casilla_destino:
                    casilla_destino.color_tinte = [0, 1, 0, 1]

    def limpiar_iluminacion(self):
        for widget in self.diccionario_casillas.values():
            widget.color_tinte = [1, 1, 1, 1]


class ChessApp(App):
    def build(self):
        gestor_ajedrez = ChessManager()
        gestor_puzzles = PuzzleManager()

        puzzle = gestor_puzzles.obtener_puzzle_aleatorio(1000, set())
        if puzzle:
            gestor_ajedrez.cargar_puzzle(puzzle)

        # Pasamos ambos gestores a la vista para el patrón MVC
        vista = VistaTablero(gestor_ajedrez=gestor_ajedrez, gestor_puzzles=gestor_puzzles)
        return vista


if __name__ == '__main__':
    ChessApp().run()