# controlador_juego.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
import chess


class CasillaInteractiva(ButtonBehavior, FloatLayout):
    """Componente visual de la casilla que detecta los toques del jugador."""

    def __init__(self, nombre_casilla, controlador, **kwargs):
        super().__init__(**kwargs)
        self.nombre_casilla = nombre_casilla
        self.controlador = controlador

    def on_press(self):
        # Escapamos del confuso sistema de eventos de Kivy delegando la acción
        self.controlador.al_tocar_casilla(self.nombre_casilla)


class ControladorTablero(BoxLayout):
    def __init__(self, gestor_ajedrez, **kwargs):
        super().__init__(**kwargs)
        self.gestor_ajedrez = gestor_ajedrez
        # Guardaremos las referencias a los widgets para actualizarlos rápido
        self.diccionario_casillas = {}

        # Mapa para traducir piezas de chess-python a rutas de imágenes
        self.mapa_imagenes = {
            'P': 'assets/pieces/blanco_peon.png', 'p': 'assets/pieces/negro_peon.png',
            'N': 'assets/pieces/blanco_caballo.png', 'n': 'assets/pieces/negro_caballo.png',
            'B': 'assets/pieces/blanco_alfil.png', 'b': 'assets/pieces/negro_alfil.png',
            'R': 'assets/pieces/blanco_torre.png', 'r': 'assets/pieces/negro_torre.png',
            'Q': 'assets/pieces/blanco_reina.png', 'q': 'assets/pieces/negro_reina.png',
            'K': 'assets/pieces/blanco_rey.png', 'k': 'assets/pieces/negro_rey.png'
        }

    def registrar_casilla(self, nombre_casilla, widget_casilla):
        """Almacena el widget en memoria al crearlo para no depender de ids internos de Kivy."""
        self.diccionario_casillas[nombre_casilla] = widget_casilla

    def actualizar_piezas_visuales(self):
        """Lee el tablero lógico y sincroniza las imágenes en pantalla."""
        tablero = self.gestor_ajedrez.board

        for nombre_casilla, widget in self.diccionario_casillas.items():
            indice_casilla = chess.parse_square(nombre_casilla)
            pieza = tablero.piece_at(indice_casilla)

            if pieza:
                # Extraemos el símbolo (ej: 'P' para peón blanco) y asignamos su PNG
                simbolo = pieza.symbol()
                widget.ids.img_pieza.source = self.mapa_imagenes.get(simbolo, '')
            else:
                # Vaciamos la imagen si no hay pieza
                widget.ids.img_pieza.source = ''