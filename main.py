from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.properties import BooleanProperty, StringProperty
from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.graphics import Color, Line, Triangle
from kivy.metrics import dp
import chess

from chess_manager import ChessManager
from puzzle_manager import PuzzleManager
import math

Window.size = (450, 800)

# Diseño KV purgado y estructurado sin errores de indentación en el parser
Builder.load_string("""
<Casilla>:
    ruta_fondo: ''
    ruta_pieza: ''
    origen_seleccionado: False
    destino_valido: False
    texto_fila: ''
    texto_col: ''

    # 1. Fondo base de la casilla
    canvas.before:
        Color:
            rgba: (1, 1, 1, 1)
        Rectangle:
            pos: 0, 0
            size: self.size
            source: root.ruta_fondo

        # Iluminación de selección (Amarillo suave)
        Color:
            rgba: (1, 1, 0, 0.4) if root.origen_seleccionado else (0, 0, 0, 0)
        Rectangle:
            pos: 0, 0
            size: self.size
    
    # 2. Círculo verde de movimiento válido (Radio = 1/8 del ancho)
    canvas.after:
        Color:
            rgba: (0, 0.7, 0, 0.8) if root.destino_valido else (0, 0, 0, 0)
        Ellipse:
            size: self.width / 4, self.height / 4
            pos: self.center_x - self.width / 8, self.center_y - self.height / 8

    # 3. Imagen de la pieza de ajedrez
    Image:
        source: root.ruta_pieza
        opacity: 1 if root.ruta_pieza else 0
        allow_stretch: True
        keep_ratio: True
        size_hint: 0.85, 0.85
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}

    # 4. Coordenadas numéricas (Fila)
    Label:
        text: root.texto_fila
        font_size: '12sp'
        bold: True
        color: 0.1, 0.1, 0.1, 0.8
        size_hint: None, None
        size: self.texture_size
        pos_hint: {'x': 0.05, 'top': 0.95}

    # 5. Coordenadas alfabéticas (Columna)
    Label:
        text: root.texto_col
        font_size: '12sp'
        bold: True
        color: 0.1, 0.1, 0.1, 0.8
        size_hint: None, None
        size: self.texture_size
        pos_hint: {'right': 0.95, 'y': 0.05}

<VistaTablero>:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(10)
    canvas.before:
        Color:
            # Fondo azul oscuro puro estilo Pygame
            rgba: 0.12, 0.29, 0.42, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        id: lbl_mision
        text: 'Puzzle ELO: --'
        font_size: '28sp'
        bold: True
        size_hint_y: 0.15
        color: 0.1, 0.8, 0.8, 1

    AnchorLayout:
        size_hint_y: 0.55
        BoxLayout:
            size_hint: None, None
            width: cuadricula_tablero.width + dp(4)
            height: cuadricula_tablero.height + dp(4)
            canvas.before:
                Color:
                    rgba: 0.8, 0.6, 0.1, 1
                Line:
                    width: 1.5
                    rectangle: self.x, self.y, self.width, self.height
            GridLayout:
                id: cuadricula_tablero
                cols: 8
                rows: 8
                size_hint: None, None
                width: min(root.width - dp(40), root.height * 0.55)
                height: self.width

    BoxLayout:
        id: panel_inferior
        orientation: 'vertical'
        size_hint_y: 0.35
        spacing: dp(8)
        
        Label:
            id: lbl_estado
            text: 'Esperando despliegue...'
            font_size: '22sp'
            bold: True
            markup: True
            color: 0.9, 0.9, 0.9, 1
            
        Label:
            id: lbl_info
            text: 'Nivel: --'
            font_size: '18sp'
            color: 0, 0.8, 0.7, 1
            bold: True
            
        Label:
            id: lbl_temas
            text: ''
            font_size: '14sp'
            color: 0.6, 0.6, 0.6, 1
            
        Button:
            id: btn_siguiente
            text: 'SIGUIENTE PUZZLE'
            size_hint_y: None
            height: dp(45)
            background_color: 0, 0.7, 0.5, 1
            on_press: root.cargar_siguiente_puzzle()
            
        Button:
            id: btn_volver
            text: 'Salir del juego'
            size_hint_y: None
            height: dp(45)
            background_color: 0.3, 0.3, 0.3, 1
            opacity: 0
            disabled: True
            on_press: root.salir_juego()
""")


class Casilla(ButtonBehavior, RelativeLayout):
    ruta_fondo = StringProperty('')
    ruta_pieza = StringProperty('')
    origen_seleccionado = BooleanProperty(False)
    destino_valido = BooleanProperty(False)
    texto_fila = StringProperty('')
    texto_col = StringProperty('')


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
        self.gestor_puzzles = gestor_puzzles
        self.diccionario_casillas = {}

        self.sonido_seleccionar = SoundLoader.load('assets/sounds/select.wav')
        self.sonido_mover = SoundLoader.load('assets/sounds/move.wav')
        self.sonido_ganar = SoundLoader.load('assets/sounds/win.wav')
        self.sonido_perder = SoundLoader.load('assets/sounds/lose.wav')

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

        juega_blancas = self.gestor_ajedrez.board.turn
        filas = list(range(7, -1, -1)) if juega_blancas else list(range(8))
        columnas = list(range(8)) if juega_blancas else list(range(7, -1, -1))

        for fila in filas:
            for col in columnas:
                nombre_casilla = chess.square_name(chess.square(col, fila))
                casilla = Casilla(nombre_casilla=nombre_casilla, controlador=self)

                es_clara = (fila + col) % 2 != 0
                casilla.ruta_fondo = "assets/squares/casilla_clara.png" if es_clara else "assets/squares/casilla_oscura.png"

                if col == columnas[0]:
                    casilla.texto_fila = nombre_casilla[1]
                if fila == filas[-1]:
                    casilla.texto_col = nombre_casilla[0]

                self.diccionario_casillas[nombre_casilla] = casilla
                cuadricula.add_widget(casilla)

    def cargar_siguiente_puzzle(self):
        self.limpiar_flecha()
        nuevo_puzzle = self.gestor_puzzles.obtener_puzzle_aleatorio(1000, set())
        if nuevo_puzzle:
            self.gestor_ajedrez.cargar_puzzle(nuevo_puzzle)
            self.inicializar_tablero()
            self.actualizar_piezas_visuales()

            es_blancas = self.gestor_ajedrez.board.turn == chess.WHITE
            color_turno = "[color=#ffffff]BLANCAS[/color]" if es_blancas else "[color=#ff6b6b]NEGRAS[/color]"
            self.ids.lbl_estado.text = f"Tu turno: {color_turno}"

            self.ids.lbl_temas.text = ""
            self.ids.btn_siguiente.text = "SIGUIENTE PUZZLE"
            self.ids.btn_volver.opacity = 0
            self.ids.btn_volver.disabled = True

    def actualizar_piezas_visuales(self):
        tablero = self.gestor_ajedrez.board
        for nombre_casilla, widget in self.diccionario_casillas.items():
            indice_casilla = chess.parse_square(nombre_casilla)
            pieza = tablero.piece_at(indice_casilla)
            widget.ruta_pieza = self.mapa_imagenes.get(pieza.symbol(), '') if pieza else ''

        info = self.gestor_ajedrez.info_puzzle
        if info:
            self.ids.lbl_mision.text = f"Puzzle ELO: {info.get('rating', '--')}"
            self.ids.lbl_info.text = f"Popularidad: {info.get('popularity', '--')}% | ID: {info.get('id', '--')}"

            es_blancas = tablero.turn == chess.WHITE
            color_turno = "[color=#ff6b6b]NEGRAS[/color]" if not es_blancas else "[color=#ffffff]BLANCAS[/color]"

            if self.gestor_ajedrez.estado_puzzle == "JUGANDO":
                self.ids.lbl_estado.text = f"Tu turno: {color_turno}"

    def al_tocar_casilla(self, nombre_casilla):
        gestor = self.gestor_ajedrez

        if gestor.casilla_seleccionada and nombre_casilla in gestor.movimientos_validos:
            origen = gestor.casilla_seleccionada
            indice_origen = chess.parse_square(origen)
            pieza = gestor.board.piece_at(indice_origen)
            simbolo = pieza.symbol() if pieza else ''

            exito = gestor.intentar_movimiento_jugador(nombre_casilla)
            self.limpiar_iluminacion()

            if exito:
                if self.sonido_mover: self.sonido_mover.play()

                self.actualizar_piezas_visuales()
                self.diccionario_casillas[nombre_casilla].ruta_pieza = ''

                def terminar_vuelo():
                    self.diccionario_casillas[nombre_casilla].ruta_pieza = self.mapa_imagenes.get(
                        simbolo, '')
                    if gestor.estado_puzzle == "VICTORIA":
                        if self.sonido_ganar:
                            self.sonido_ganar.play()
                        self.ids.lbl_estado.text = "¡PUZZLE COMPLETADO!"
                        self.ids.lbl_estado.color = [0, 1, 0, 1]
                        self.ids.btn_volver.opacity = 1
                        self.ids.btn_volver.disabled = False
                    else:
                        self.ids.lbl_estado.text = "¡Excelente! Responde la IA..."
                        self.ids.lbl_estado.color = [1, 1, 0, 1]
                        Clock.schedule_once(self.procesar_respuesta_ia, 0.4)

                self.animar_pieza(origen, nombre_casilla, simbolo, terminar_vuelo)
            else:
                self.actualizar_piezas_visuales()
                if self.sonido_perder:
                    self.sonido_perder.play()
                mov_erroneo = gestor.movimiento_fallado
                if mov_erroneo:
                    mov_formateado = f"{mov_erroneo[:2].upper()}-{mov_erroneo[2:4].upper()}"
                    self.ids.lbl_estado.text = f"Debiste jugar: {mov_formateado}"
                    self.mostrar_flecha_error(mov_erroneo)

                self.ids.lbl_estado.color = [1, 0.4, 0.4, 1]

                info = gestor.info_puzzle
                if info:
                    temas = info.get('themes', '').replace(' ', ' • ')
                    self.ids.lbl_temas.text = temas
                    self.ids.lbl_info.text = f"Nivel: {info.get('rating')} (-22)"

                self.ids.btn_siguiente.text = "Siguiente Misión"
                self.ids.btn_volver.opacity = 1
                self.ids.btn_volver.disabled = False
        else:
            gestor.seleccionar_casilla(nombre_casilla)
            self.iluminar_casillas()
            if gestor.casilla_seleccionada and self.sonido_seleccionar:
                self.sonido_seleccionar.play()

    def evaluar_estado_jugador(self):
        # ¡Magia! La animación terminó, devolvemos la visibilidad a la pieza
        self.actualizar_piezas_visuales()

        gestor = self.gestor_ajedrez
        if gestor.estado_puzzle == "VICTORIA":
            self.ids.lbl_estado.text = "¡PUZZLE COMPLETADO!"
            self.ids.lbl_estado.color = [0, 1, 0, 1]
        else:
            self.ids.lbl_estado.text = "¡Excelente! Responde la IA..."
            self.ids.lbl_estado.color = [1, 1, 0, 1]
            Clock.schedule_once(self.procesar_respuesta_ia, 0.3)

    def procesar_respuesta_ia(self, dt):
        mov = self.gestor_ajedrez.ejecutar_movimiento_enemigo()
        if mov:
            origen = mov[:2]
            destino = mov[2:4]

            # La pieza ya está lógicamente en el destino
            indice_destino = chess.parse_square(destino)
            pieza = self.gestor_ajedrez.board.piece_at(indice_destino)
            simbolo = pieza.symbol() if pieza else ''

            # Escondemos la pieza de origen en la vista
            self.diccionario_casillas[origen].ruta_pieza = ''

            def terminar_animacion_ia():
                self.actualizar_piezas_visuales()
                if self.sonido_mover: self.sonido_mover.play()
                if self.gestor_ajedrez.estado_puzzle == "VICTORIA":
                    self.ids.lbl_estado.text = "¡PUZZLE COMPLETADO!"
                    self.ids.lbl_estado.color = [0, 1, 0, 1]
                    self.ids.btn_volver.opacity = 1
                    self.ids.btn_volver.disabled = False
                else:
                    self.ids.lbl_estado.text = "¡Tu turno! Continúa."
                    self.ids.lbl_estado.color = [0.9, 0.9, 0.9, 1]

            self.animar_pieza(origen, destino, simbolo, terminar_animacion_ia)

    def finalizar_turno_ia(self):
        # Restauramos el tablero tras el movimiento enemigo
        self.actualizar_piezas_visuales()
        if self.sonido_mover: self.sonido_mover.play()

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
                casilla_origen.origen_seleccionado = True

            for destino in gestor.movimientos_validos:
                casilla_destino = self.diccionario_casillas.get(destino)
                if casilla_destino:
                    casilla_destino.destino_valido = True

    def limpiar_iluminacion(self):
        for widget in self.diccionario_casillas.values():
            widget.origen_seleccionado = False
            widget.destino_valido = False

    def animar_pieza(self, origen, destino, simbolo, callback):

        c_origen = self.diccionario_casillas[origen]
        c_destino = self.diccionario_casillas[destino]

        pos_ini = c_origen.parent.to_window(c_origen.x, c_origen.y)
        pos_fin = c_destino.parent.to_window(c_destino.x, c_destino.y)

        fantasma = Image(
            source=self.mapa_imagenes.get(simbolo, ''),
            size_hint=(None, None),
            size=c_origen.size,
            pos=pos_ini
        )
        Window.add_widget(fantasma)

        anim = Animation(pos=pos_fin, d=0.3, t='in_out_expo')

        def limpiar(*args):
            Window.remove_widget(fantasma)
            callback()

        anim.bind(on_complete=limpiar)
        anim.start(fantasma)

    def mostrar_flecha_error(self, mov_correcto):
        origen = mov_correcto[:2]
        destino = mov_correcto[2:4]

        c_origen = self.diccionario_casillas.get(origen)
        c_destino = self.diccionario_casillas.get(destino)

        if not c_origen or not c_destino:
            return

        x1 = c_origen.x + c_origen.width / 2
        y1 = c_origen.y + c_origen.height / 2
        x2 = c_destino.x + c_destino.width / 2
        y2 = c_destino.y + c_destino.height / 2

        with self.ids.cuadricula_tablero.canvas.after:
            Color(0.4, 0.8, 0.4, 0.7)
            self.linea_error = Line(points=[x1, y1, x2, y2], width=dp(4))

            angulo = math.atan2(y2 - y1, x2 - x1)
            l = dp(16)
            p1 = (x2, y2)
            p2 = (x2 - l * math.cos(angulo - math.pi / 6), y2 - l * math.sin(angulo - math.pi / 6))
            p3 = (x2 - l * math.cos(angulo + math.pi / 6), y2 - l * math.sin(angulo + math.pi / 6))

            self.triangulo_error = Triangle(points=[p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]])

    def limpiar_flecha(self):
        if hasattr(self, 'linea_error'):
            self.ids.cuadricula_tablero.canvas.after.remove(self.linea_error)
            self.ids.cuadricula_tablero.canvas.after.remove(self.triangulo_error)
            del self.linea_error
            del self.triangulo_error

    def salir_juego(self):
        App.get_running_app().stop()


class ChessApp(App):
    def build(self):
        gestor_ajedrez = ChessManager()
        gestor_puzzles = PuzzleManager()

        puzzle = gestor_puzzles.obtener_puzzle_aleatorio(1000, set())
        if puzzle:
            gestor_ajedrez.cargar_puzzle(puzzle)

        return VistaTablero(gestor_ajedrez=gestor_ajedrez, gestor_puzzles=gestor_puzzles)


if __name__ == '__main__':
    ChessApp().run()