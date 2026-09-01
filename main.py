"""
Módulo principal de la aplicación Kivy para Mind Chess.

Este archivo actúa como el núcleo de la Vista en el patrón MVC, orquestando
la interfaz gráfica, las animaciones asíncronas de Kivy, el motor de audio y
la interacción directa con los controladores lógicos (ajedrez, perfiles y puzles)[cite: 3].
"""
"""
Módulo de configuración previa y arranque de la aplicación.

Aplica configuraciones críticas al entorno de Kivy antes de cargar la 
interfaz gráfica (Vista) para asegurar una experiencia de usuario limpia.
"""
from kivy.config import Config

# ¡Por los registros desbordados del procesador! Aniquilamos la basura multitáctil.
# Esto evita que el clic derecho del ratón genere puntos rojos persistentes en PC.
Config.set('input', 'mouse', 'mouse,disable_multitouch')

import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.text import Label as CoreLabel, LabelBase, DEFAULT_FONT
from kivy.properties import BooleanProperty, StringProperty, ListProperty, NumericProperty
from kivy.animation import Animation
from kivy.graphics import Color, Line, Triangle
from kivy.metrics import dp, sp
from kivy.utils import platform
import chess
import math
from typing import Callable
import os


# Importación de nuestros robustos módulos lógicos[cite: 3]
from chess_manager import ChessManager
from puzzle_manager import PuzzleManager, GestorProgresionPop
from perfil_manager import PerfilManager
from utilidades import CalculadorElo
from escuela_controladores import PantallaEscuelaTemas, PantallaEscuelaUnidades, PantallaVisorUnidad
from escuela_controladores import PantallaVisorUnidad
from utilidades_log import configurar_logger, LOG_DEBUG

# Inicializa el espía a nivel de módulo
log = configurar_logger("VistaLeccion")

# Diccionario maestro para purgar el inglés del CSV
DICCIONARIO_TEMAS = {
    'mate': 'Mate', 'mateIn1': 'Mate en 1', 'mateIn2': 'Mate en 2',
    'mateIn3': 'Mate en 3', 'mateIn4': 'Mate en 4', 'mateIn5': 'Mate en 5',
    'short': 'Corto', 'long': 'Largo', 'veryLong': 'Muy largo',
    'advantage': 'Ventaja', 'fork': 'Ataque Doble', 'pin': 'Clavada',
    'skewer': 'Enfilada', 'endgame': 'Final', 'middlegame': 'Medio juego',
    'opening': 'Apertura', 'defensiveMove': 'Defensa', 'sacrifice': 'Sacrificio',
    'discoveredAttack': 'Descubierta', 'crushing': 'Aplastante',
    'kingsideAttack': 'Ataque Rey', 'queensideAttack': 'Ataque Dama',
    'advancedPawn': 'Peon avanzado', 'passedPawn': 'Peon pasado',
    'attraction': 'Atraccion', 'clearance': 'Despeje', 'deflection': 'Desviacion',
    'zugzwang': 'Zugzwang', 'quietMove': 'Jugada tranquila',
    'hangingPiece': 'Pieza colgada', 'trappedPiece': 'Pieza atrapada',
    'xRayAttack': 'Rayos X', 'capturingDefender': 'Captura del defensor',
    'promotion': 'Coronacion', 'interference': 'Interferencia',
    'doubleCheck': 'Jaque doble', 'enPassant': 'Al paso',
    'castling': 'Enroque'
}
if platform != 'android' and platform != 'ios':
    Window.size = (450, 800)

# Diseño KV purgado y estructurado sin errores de indentación en el parser[cite: 3]
# Builder.load_file('interfaz.kv')
# Builder.load_file('escuela.kv')

from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.metrics import dp


class BotonTextoAdaptativo(Button):
    """Ajusta el texto al espacio real del botón sin depender de la plataforma."""

    font_size_min = NumericProperty(sp(8))
    font_size_max = NumericProperty(sp(18))
    proporcion_altura_fuente = NumericProperty(0.38)
    margen_horizontal = NumericProperty(dp(12))
    margen_vertical = NumericProperty(dp(8))

    def __init__(self, **kwargs) -> None:
        """Configura el reajuste cuando cambian el texto o las dimensiones."""
        super().__init__(**kwargs)
        self._evento_ajuste = None
        self.bind(
            size=self._programar_ajuste,
            text=self._programar_ajuste,
            font_name=self._programar_ajuste,
            bold=self._programar_ajuste,
            italic=self._programar_ajuste,
            font_size_min=self._programar_ajuste,
            font_size_max=self._programar_ajuste,
            proporcion_altura_fuente=self._programar_ajuste,
            margen_horizontal=self._programar_ajuste,
            margen_vertical=self._programar_ajuste,
        )
        self._programar_ajuste()

    def _programar_ajuste(self, *_args) -> None:
        """Agrupa cambios de layout y recalcula como máximo una vez por frame."""
        if self._evento_ajuste is not None:
            self._evento_ajuste.cancel()
        self._evento_ajuste = Clock.schedule_once(self._ajustar_fuente, 0)

    def _medir_texto(self, tamano_fuente: float) -> tuple[float, float]:
        """Devuelve el tamaño natural del texto para una fuente concreta."""
        etiqueta = CoreLabel(
            text=self.text,
            font_name=self.font_name,
            font_size=tamano_fuente,
            bold=self.bold,
            italic=self.italic,
        )
        etiqueta.refresh()
        return etiqueta.texture.size

    def _ajustar_fuente(self, _dt: float) -> None:
        """Busca el mayor tamaño que respeta el ancho y alto disponibles."""
        self._evento_ajuste = None
        if not self.text or self.width <= 0 or self.height <= 0:
            return

        ancho_disponible = max(1.0, self.width - (2 * self.margen_horizontal))
        alto_disponible = max(1.0, self.height - (2 * self.margen_vertical))

        limite_altura = self.height * self.proporcion_altura_fuente
        maximo = max(
            self.font_size_min,
            min(self.font_size_max, limite_altura),
        )
        minimo = min(self.font_size_min, maximo)

        ancho, alto = self._medir_texto(maximo)
        if ancho <= ancho_disponible and alto <= alto_disponible:
            self.font_size = maximo
            return

        ancho_minimo, alto_minimo = self._medir_texto(minimo)
        bajo = minimo
        if ancho_minimo > ancho_disponible or alto_minimo > alto_disponible:
            bajo = 1.0

        mejor = bajo
        alto_busqueda = maximo

        for _ in range(10):
            candidato = (bajo + alto_busqueda) / 2.0
            ancho, alto = self._medir_texto(candidato)

            if ancho <= ancho_disponible and alto <= alto_disponible:
                mejor = candidato
                bajo = candidato
            else:
                alto_busqueda = candidato

        self.font_size = mejor


class PantallaCambiarUsuario(Screen):
    """
    Vista para alternar entre los perfiles existentes.
    """

    def __init__(self, gestor_perfiles, al_seleccionar, **kwargs):
        super().__init__(**kwargs)
        self.gestor_perfiles = gestor_perfiles
        self.al_seleccionar = al_seleccionar
        self.poblar_perfiles()

    def poblar_perfiles(self):
        self.ids.grid_perfiles.clear_widgets()
        usuarios = self.gestor_perfiles.obtener_lista_usuarios()

        for u in usuarios:
            btn = BotonTextoAdaptativo(
                text=f"Jugar como {u}",
                size_hint_y=None,
                height=dp(55),
                font_size_max=sp(16),
                background_color=(0, 0.7, 0.5, 1),
                bold=True
            )
            # Pasamos el nombre al callback para cargar el perfil
            btn.bind(on_press=lambda instance, nombre=u: self.al_seleccionar(nombre))
            self.ids.grid_perfiles.add_widget(btn)

    def on_pre_enter(self, *args):
        # Refresca la lista cada vez que la pantalla se va a mostrar
        self.poblar_perfiles()

    def volver(self):
        from kivy.app import App
        App.get_running_app().sm.current = 'menu_principal'

class Casilla(ButtonBehavior, RelativeLayout):
    """
    Componente visual que representa una única casilla en el tablero de ajedrez.

    Hereda de ButtonBehavior para detectar toques del usuario, y de RelativeLayout
    para posicionar la textura del escaque, la pieza y las coordenadas de forma
    independiente. Enlaza variables visuales fuertemente tipadas de Kivy[cite: 3].
    """

    # Declaración del infierno de Properties de Kivy que hemos domado con maestría[cite: 3]
    ruta_fondo = StringProperty('')
    ruta_pieza = StringProperty('')
    origen_seleccionado = BooleanProperty(False)
    destino_valido = BooleanProperty(False)
    texto_fila = StringProperty('')
    texto_col = StringProperty('')

    def __init__(self, nombre_casilla, controlador, **kwargs):
        """
        Inicializa la casilla lógica y visualmente.

        Args:
            nombre_casilla (str): ID de la casilla según la notación algebraica (ej. 'e4')[cite: 3].
            controlador (VistaTablero): Referencia al contenedor padre para despachar eventos[cite: 3].
            **kwargs: Parámetros adicionales para las entrañas de Kivy[cite: 3].
        """
        super().__init__(**kwargs)
        self.nombre_casilla = nombre_casilla
        self.controlador = controlador

    def on_press(self):
        """
        Intercepta la pulsación física en la pantalla y la delega.

        Evitamos procesar la lógica aquí; se la enviamos directamente
        al controlador maestro para que él decida qué hacer con el toque[cite: 3].
        """
        self.controlador.al_tocar_casilla(self.nombre_casilla)


class VistaTablero(BoxLayout):
    """
    Controlador gráfico supremo que orquesta toda la experiencia de usuario.

    Conecta la cuadrícula interactiva (Vista) con el motor de ajedrez y los
    gestores de persistencia (Modelos). También maneja las animaciones asíncronas
    y el motor de audio de Kivy[cite: 3].
    """

    def __init__(self, gestor_ajedrez, gestor_puzzles, perfil_actual, gestor_perfiles, habilitar_visor_solucion: bool = True, **kwargs):
        """
        Configura la vista inyectándole todos los módulos lógicos requeridos.

        Args:
            gestor_ajedrez (ChessManager): Motor de reglas y estado de la partida[cite: 3].
            gestor_puzzles (PuzzleManager): Surtidor de nuevas tácticas[cite: 3].
            perfil_actual (dict): Datos del jugador actualmente en sesión[cite: 3].
            gestor_perfiles (PerfilManager): Interfaz con el disco duro JSON[cite: 3].
            **kwargs: Atributos visuales que Kivy traga silenciosamente[cite: 3].
        """
        super().__init__(**kwargs)
        self.gestor_ajedrez = gestor_ajedrez
        self.gestor_puzzles = gestor_puzzles
        self.perfil_actual = perfil_actual
        self.gestor_perfiles = gestor_perfiles
        self.diccionario_casillas = {}
        self._habilitar_visor_solucion = habilitar_visor_solucion
        self._modo_solucion_general = False
        self._tablero_revision_general: chess.Board | None = None
        self._movimientos_revision_general: list[str] = []
        self._indice_revision_general = 0
        self._animacion_solucion_general_activa = False

        # Inyección de rutas absolutas para someter al sistema de archivos de Android
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ruta_select = os.path.join(BASE_DIR, 'assets', 'sounds', 'select.wav')
        ruta_move = os.path.join(BASE_DIR, 'assets', 'sounds', 'move.wav')
        ruta_win = os.path.join(BASE_DIR, 'assets', 'sounds', 'win.wav')
        ruta_lose = os.path.join(BASE_DIR, 'assets', 'sounds', 'lose.wav')

        self.sonido_seleccionar = SoundLoader.load(ruta_select)
        self.sonido_mover = SoundLoader.load(ruta_move)
        self.sonido_ganar = SoundLoader.load(ruta_win)
        self.sonido_perder = SoundLoader.load(ruta_lose)

        # Mapa de sprites para asociar la notación FEN con nuestros PNGs[cite: 3]
        self.mapa_imagenes = {
            'P': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_peon.png'),
            'p': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_peon.png'),
            'N': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_caballo.png'),
            'n': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_caballo.png'),
            'B': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_alfil.png'),
            'b': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_alfil.png'),
            'R': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_torre.png'),
            'r': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_torre.png'),
            'Q': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_reina.png'),
            'q': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_reina.png'),
            'K': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_rey.png'),
            'k': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_rey.png')
        }
        self.inicializar_tablero()
        self.actualizar_piezas_visuales()
        if self._habilitar_visor_solucion:
            self._configurar_controles_solucion_general()


    def _configurar_controles_solucion_general(self) -> None:
        """Prepara los controles de solución para el modo de puzzles global."""
        panel = self.ids.panel_inferior
        indice_original = panel.children.index(self.ids.btn_siguiente)

        # Conservamos una referencia fuerte al sacar el botón del árbol de widgets.
        self._btn_siguiente_general = panel.children[indice_original]
        panel.remove_widget(self._btn_siguiente_general)

        self._fila_acciones_general = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60),
            spacing=0,
        )
        self._btn_mostrar_solucion_general = BotonTextoAdaptativo(
            text="MOSTRAR SOLUCION",
            size_hint_x=None,
            width=0,
            opacity=0,
            disabled=True,
            font_size_max=sp(16),
            margen_horizontal=dp(6),
            background_color=(1, 1, 1, 1),
            background_normal="assets/ui/button.png",
            background_down="assets/ui/button_down.png",
            border=(0, 0, 0, 0),
            bold=True,
        )
        self._btn_mostrar_solucion_general.bind(
            on_release=self.mostrar_solucion_general
        )

        self._btn_siguiente_general.size_hint_x = 1
        self._fila_acciones_general.add_widget(self._btn_mostrar_solucion_general)
        self._fila_acciones_general.add_widget(self._btn_siguiente_general)
        panel.add_widget(self._fila_acciones_general, index=indice_original)

        self._fila_navegacion_general = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )
        self._btn_solucion_anterior_general = Button(
            text="<",
            size_hint_x=0.25,
            background_color=(1, 1, 1, 1),
            background_normal="assets/ui/button.png",
            background_down="assets/ui/button_down.png",
            border=(0, 0, 0, 0),
            bold=True,
        )
        self._btn_solucion_anterior_general.bind(
            on_release=self.retroceder_solucion_general
        )

        self._lbl_paso_solucion_general = Label(
            text="INICIO",
            size_hint_x=0.5,
            font_size="16sp",
            bold=True,
            color=(0.95, 0.95, 0.95, 1),
            halign="center",
            valign="middle",
        )
        self._lbl_paso_solucion_general.bind(
            size=lambda instance, size: setattr(instance, "text_size", size)
        )

        self._btn_solucion_siguiente_general = Button(
            text=">",
            size_hint_x=0.25,
            background_color=(1, 1, 1, 1),
            background_normal="assets/ui/button.png",
            background_down="assets/ui/button_down.png",
            border=(0, 0, 0, 0),
            bold=True,
        )
        self._btn_solucion_siguiente_general.bind(
            on_release=self.avanzar_solucion_general
        )

        self._fila_navegacion_general.add_widget(
            self._btn_solucion_anterior_general
        )
        self._fila_navegacion_general.add_widget(
            self._lbl_paso_solucion_general
        )
        self._fila_navegacion_general.add_widget(
            self._btn_solucion_siguiente_general
        )

    def _mostrar_acciones_fallo_general(self) -> None:
        """Muestra el acceso a la solución junto a Siguiente puzzle."""
        if not self._habilitar_visor_solucion:
            return

        self._fila_acciones_general.spacing = dp(8)
        self._btn_mostrar_solucion_general.size_hint_x = 1
        self._btn_mostrar_solucion_general.opacity = 1
        self._btn_mostrar_solucion_general.disabled = False
        self._btn_siguiente_general.size_hint_x = 1
        self._btn_siguiente_general.text = "SIGUIENTE PUZZLE"

    def _ocultar_boton_solucion_general(self) -> None:
        """Oculta el botón Mostrar solución."""
        if not self._habilitar_visor_solucion:
            return

        self._fila_acciones_general.spacing = 0
        self._btn_mostrar_solucion_general.size_hint_x = None
        self._btn_mostrar_solucion_general.width = 0
        self._btn_mostrar_solucion_general.opacity = 0
        self._btn_mostrar_solucion_general.disabled = True
        self._btn_siguiente_general.size_hint_x = 1

    def _restablecer_panel_solucion_general(self) -> None:
        """Abandona la revisión y restaura el panel normal de puzzles."""
        if not self._habilitar_visor_solucion:
            return

        self._modo_solucion_general = False
        self._tablero_revision_general = None
        self._movimientos_revision_general = []
        self._indice_revision_general = 0
        self._animacion_solucion_general_activa = False

        if self._fila_navegacion_general.parent is not None:
            self._fila_navegacion_general.parent.remove_widget(
                self._fila_navegacion_general
            )

        for etiqueta in (self.ids.lbl_info, self.ids.lbl_temas):
            etiqueta.size_hint_y = 1
            etiqueta.opacity = 1

        self._ocultar_boton_solucion_general()
        self._btn_siguiente_general.disabled = False
        self._btn_siguiente_general.text = "SIGUIENTE PUZZLE"
        self.ids.btn_volver.disabled = False

    def mostrar_solucion_general(self, *_args) -> None:
        """Inicia la reproducción manual de la solución del puzzle fallado."""
        if (
            not self._habilitar_visor_solucion
            or self.gestor_ajedrez.estado_puzzle != "DERROTA"
        ):
            return

        info = self.gestor_ajedrez.info_puzzle or {}
        fen = info.get("fen")
        movimientos = list(info.get("moves", []))
        if not fen or not movimientos:
            return

        tablero_revision = chess.Board(fen)
        primer_movimiento = chess.Move.from_uci(movimientos[0])
        if primer_movimiento not in tablero_revision.legal_moves:
            return

        self._modo_solucion_general = True
        self._tablero_revision_general = tablero_revision
        self._movimientos_revision_general = movimientos
        self._indice_revision_general = 0
        self._animacion_solucion_general_activa = False

        self.limpiar_iluminacion()
        self.limpiar_flecha()
        self._ocultar_boton_solucion_general()

        panel = self.ids.panel_inferior
        if self._fila_navegacion_general.parent is None:
            indice = panel.children.index(self._fila_acciones_general) + 1
            panel.add_widget(self._fila_navegacion_general, index=indice)

        for etiqueta in (self.ids.lbl_info, self.ids.lbl_temas):
            etiqueta.size_hint_y = None
            etiqueta.height = 0
            etiqueta.opacity = 0

        self.ids.lbl_estado.text = "REVISION DE LA SOLUCION"
        self.ids.lbl_estado.color = [0.1, 0.8, 0.8, 1]
        self._btn_siguiente_general.text = "SIGUIENTE PUZZLE"

        self._renderizar_tablero_revision_general()
        self._actualizar_navegacion_solucion_general()

        # Se muestra también la primera jugada de la IA desde el FEN original.
        self.avanzar_solucion_general()

    def avanzar_solucion_general(self, *_args) -> None:
        """Anima y avanza un movimiento dentro de la solución."""
        tablero = self._tablero_revision_general
        if (
            not self._modo_solucion_general
            or tablero is None
            or self._animacion_solucion_general_activa
            or self._indice_revision_general
            >= len(self._movimientos_revision_general)
        ):
            return

        movimiento_uci = self._movimientos_revision_general[
            self._indice_revision_general
        ]
        movimiento = chess.Move.from_uci(movimiento_uci)
        if movimiento not in tablero.legal_moves:
            self._btn_solucion_siguiente_general.disabled = True
            self._lbl_paso_solucion_general.text = "ERROR"
            return

        origen = movimiento_uci[:2]
        destino = movimiento_uci[2:4]
        pieza = tablero.piece_at(movimiento.from_square)
        simbolo = pieza.symbol() if pieza else ""
        if not simbolo:
            return

        self.limpiar_flecha()
        self._bloquear_controles_revision_general(True)
        self.diccionario_casillas[origen].ruta_pieza = ""

        def terminar_animacion() -> None:
            """Consolida el movimiento al terminar su animación."""
            if (
                not self._modo_solucion_general
                or self._tablero_revision_general is not tablero
            ):
                return

            tablero.push(movimiento)
            self._indice_revision_general += 1
            self._renderizar_tablero_revision_general()

            if self.sonido_mover:
                self.sonido_mover.play()

            self.mostrar_flecha_error(movimiento_uci)
            self._bloquear_controles_revision_general(False)
            self._actualizar_navegacion_solucion_general()

        self.animar_pieza(origen, destino, simbolo, terminar_animacion)

    def retroceder_solucion_general(self, *_args) -> None:
        """Anima hacia atrás el último movimiento mostrado."""
        tablero = self._tablero_revision_general
        if (
            not self._modo_solucion_general
            or tablero is None
            or self._animacion_solucion_general_activa
            or self._indice_revision_general <= 0
        ):
            return

        movimiento_uci = self._movimientos_revision_general[
            self._indice_revision_general - 1
        ]
        movimiento = chess.Move.from_uci(movimiento_uci)
        origen = movimiento_uci[:2]
        destino = movimiento_uci[2:4]

        pieza = tablero.piece_at(movimiento.to_square)
        simbolo = pieza.symbol() if pieza else ""
        if not simbolo:
            return

        self.limpiar_flecha()
        self._bloquear_controles_revision_general(True)
        self.diccionario_casillas[destino].ruta_pieza = ""

        def terminar_animacion() -> None:
            """Restaura la posición anterior al terminar la animación inversa."""
            if (
                not self._modo_solucion_general
                or self._tablero_revision_general is not tablero
            ):
                return

            tablero.pop()
            self._indice_revision_general -= 1
            self._renderizar_tablero_revision_general()

            if self.sonido_mover:
                self.sonido_mover.play()

            if self._indice_revision_general > 0:
                movimiento_anterior = self._movimientos_revision_general[
                    self._indice_revision_general - 1
                ]
                self.mostrar_flecha_error(movimiento_anterior)

            self._bloquear_controles_revision_general(False)
            self._actualizar_navegacion_solucion_general()

        self.animar_pieza(destino, origen, simbolo, terminar_animacion)

    def _bloquear_controles_revision_general(self, bloqueados: bool) -> None:
        """Bloquea controles mientras una pieza está en movimiento."""
        self._animacion_solucion_general_activa = bloqueados
        self._btn_siguiente_general.disabled = bloqueados
        self.ids.btn_volver.disabled = bloqueados

        if bloqueados:
            self._btn_solucion_anterior_general.disabled = True
            self._btn_solucion_siguiente_general.disabled = True

    def _renderizar_tablero_revision_general(self) -> None:
        """Pinta el tablero aislado sin modificar ChessManager."""
        if self._tablero_revision_general is None:
            return

        for nombre_casilla, widget in self.diccionario_casillas.items():
            indice_casilla = chess.parse_square(nombre_casilla)
            pieza = self._tablero_revision_general.piece_at(indice_casilla)
            widget.ruta_pieza = (
                self.mapa_imagenes.get(pieza.symbol(), "") if pieza else ""
            )

    def _actualizar_navegacion_solucion_general(self) -> None:
        """Actualiza contador y límites de navegación."""
        total = len(self._movimientos_revision_general)
        if self._indice_revision_general == 0:
            self._lbl_paso_solucion_general.text = "INICIO"
        else:
            self._lbl_paso_solucion_general.text = (
                f"{self._indice_revision_general} / {total}"
            )

        if not self._animacion_solucion_general_activa:
            self._btn_solucion_anterior_general.disabled = (
                self._indice_revision_general == 0
            )
            self._btn_solucion_siguiente_general.disabled = (
                self._indice_revision_general >= total
            )

    def inicializar_tablero(self):
        """
        Dibuja dinámicamente las 64 casillas orientadas según el color del turno.

        Limpia la cuadrícula de Kivy y crea instancias de `Casilla` alternando
        texturas para generar el clásico patrón claro/oscuro. Inyecta también
        las coordenadas alfanuméricas en los bordes[cite: 3].
        """
        cuadricula = self.ids.cuadricula_tablero
        cuadricula.clear_widgets()
        self.diccionario_casillas.clear()

        # ¡Magia pura! Rotamos el tablero visual si le toca jugar a las negras[cite: 3]
        juega_blancas = self.gestor_ajedrez.board.turn
        filas = list(range(7, -1, -1)) if juega_blancas else list(range(8))
        columnas = list(range(8)) if juega_blancas else list(range(7, -1, -1))

        for fila in filas:
            for col in columnas:
                nombre_casilla = chess.square_name(chess.square(col, fila))
                casilla = Casilla(nombre_casilla=nombre_casilla, controlador=self)

                es_clara = (fila + col) % 2 != 0
                casilla.ruta_fondo = "assets/squares/casilla_clara.png" if es_clara else "assets/squares/casilla_oscura.png"

                # Añadimos etiquetas de coordenadas sólo en los bordes correspondientes[cite: 3]
                if col == columnas[0]:
                    casilla.texto_fila = nombre_casilla[1]
                if fila == filas[-1]:
                    casilla.texto_col = nombre_casilla[0]

                self.diccionario_casillas[nombre_casilla] = casilla
                cuadricula.add_widget(casilla)

    def cargar_siguiente_puzzle(self):
        """
        Pide al gestor de puzles un nuevo desafío y lo despliega en el tablero.

        Resetea la interfaz (limpiando flechas de error y textos), actualiza el
        motor lógico y solicita la re-renderización visual[cite: 3].
        """
        app = App.get_running_app()
        if getattr(app, 'modo_leccion', False):
            app.modo_leccion = False
            visor = app.sm.get_screen('escuela_visor')
            if visor.indice_pagina < len(visor.paginas) - 1:
                visor.indice_pagina += 1
                visor.mostrar_pagina()
            app.sm.current = 'escuela_visor'
            return
        self._restablecer_panel_solucion_general()
        self.limpiar_flecha()
        elo_jugador = self.perfil_actual.get("elo", 600)
        historial_resueltos = set(self.perfil_actual.get("resueltos", []))
        escala_actual = self.perfil_actual.get("escala_pop", 0)
        pop_min, pop_max = GestorProgresionPop.ESCALAS[escala_actual]

        nuevo_puzzle = self.gestor_puzzles.obtener_puzzle_aleatorio(
            elo_objetivo=self.perfil_actual["elo"],
            ids_locales=set(self.perfil_actual["resueltos"]),
            pop_min=pop_min,
            pop_max=pop_max
        )
        if nuevo_puzzle:
            self.gestor_ajedrez.cargar_puzzle(nuevo_puzzle)
            self.inicializar_tablero()
            self.actualizar_piezas_visuales()

            es_blancas = self.gestor_ajedrez.board.turn == chess.WHITE
            color_turno = "[color=#ffffff]BLANCAS[/color]" if es_blancas else "[color=#ff6b6b]NEGRAS[/color]"
            self.ids.lbl_estado.text = f"Tu turno: {color_turno}"

            # Limpieza de metadatos de la misión anterior[cite: 3]
            self.ids.lbl_temas.text = ""
            self.ids.btn_siguiente.text = "SIGUIENTE PUZZLE"
            # self.ids.btn_volver.opacity = 0
            # self.ids.btn_volver.disabled = True

    def actualizar_piezas_visuales(self):
        """
        Sincroniza las texturas de los widgets (PNGs) con la matriz lógica subyacente.

        También refresca los componentes del panel informativo (ELO del puzle,
        popularidad e ID) para que el jugador sepa a qué se enfrenta[cite: 3].
        """
        tablero = self.gestor_ajedrez.board
        for nombre_casilla, widget in self.diccionario_casillas.items():
            indice_casilla = chess.parse_square(nombre_casilla)
            pieza = tablero.piece_at(indice_casilla)
            widget.ruta_pieza = self.mapa_imagenes.get(pieza.symbol(), '') if pieza else ''

        info = self.gestor_ajedrez.info_puzzle
        if info:
            elo_jugador_entero = int(self.perfil_actual.get("elo", 600))
            self.ids.lbl_mision.text = f"Tu ELO: {elo_jugador_entero} | Puzzle ELO: {info.get('rating', '--')}"
            self.ids.lbl_info.text = f"Popularidad: {info.get('popularity', '--')}%\nID: {info.get('id', '--')}"

            es_blancas = tablero.turn == chess.WHITE
            color_turno = "[color=#ff6b6b]NEGRAS[/color]" if not es_blancas else "[color=#ffffff]BLANCAS[/color]"

            if self.gestor_ajedrez.estado_puzzle == "JUGANDO":
                self.ids.lbl_estado.text = f"Tu turno: {color_turno}"

    def formatear_resultado_puzzle(self, victoria: bool, variacion: float,
                                  nueva_puntuacion: float) -> str:
        """Genera el texto de resultado para el sistema global de ELO."""
        if victoria:
            return (
                f"¡CORRECTO!, nuevo ELO = {nueva_puntuacion} "
                f"(+{variacion})"
            )
        return f"¡INCORRECTO! nuevo ELO = {nueva_puntuacion} ({variacion})"

    def formatear_info_resultado(self, info: dict) -> str:
        """Genera los metadatos visibles tras finalizar un puzzle global."""
        return f"Nivel: {info.get('rating')} ELO | ID: {info.get('id', '--')}"

    def al_tocar_casilla(self, nombre_casilla: str) -> None:
        """
        Procesa la lógica gráfica y de estado al pulsar una coordenada táctil.

        Este método gestiona la interacción del usuario. Valida selecciones de
        origen y destino. En caso de realizar un movimiento correcto, calcula la
        textura resultante (crucial para capturar la metamorfosis visual de la
        coronación) y lanza la animación. Mantiene intacta la llamada a la
        traducción de temas tácticos al finalizar el puzle, tal y como solicitaste.

        Args:
            nombre_casilla (str): Identificador alfanumérico estándar de la casilla
                                  pulsada por el usuario (ej. 'e1').

        Returns:
            None
        """
        if self._modo_solucion_general:
            return

        gestor = self.gestor_ajedrez

        # Verificamos si ya hay origen seleccionado y el destino es legal[cite: 3]
        if gestor.casilla_seleccionada and nombre_casilla in gestor.movimientos_validos:
            origen = gestor.casilla_seleccionada
            indice_origen = chess.parse_square(origen)

            # Capturamos la pieza ANTES de mover para la textura que volará en pantalla
            pieza_antes = gestor.board.piece_at(indice_origen)
            simbolo_vuelo = pieza_antes.symbol() if pieza_antes else ''

            # Delegamos la validación lógica al Modelo (ChessManager)[cite: 3]
            exito = gestor.intentar_movimiento_jugador(nombre_casilla)
            self.limpiar_iluminacion()

            if exito:
                # Reproducimos sonido de éxito[cite: 3]
                if self.sonido_mover: self.sonido_mover.play()

                # CRÍTICO: Capturamos la pieza DESPUÉS del movimiento para mostrar la coronación
                indice_destino = chess.parse_square(nombre_casilla)
                pieza_despues = gestor.board.piece_at(indice_destino)
                simbolo_final = pieza_despues.symbol() if pieza_despues else simbolo_vuelo

                self.actualizar_piezas_visuales()

                # Vaciamos la textura de la casilla destino temporalmente para la animación[cite: 3]
                self.diccionario_casillas[nombre_casilla].ruta_pieza = ''

                def terminar_vuelo() -> None:
                    """
                    Callback ejecutado automáticamente al finalizar la animación Kivy.
                    Inyecta la textura final y evalúa si el puzle ha concluido.
                    """
                    # Asignamos la textura de la pieza resultante (ej. Reina en vez de Peón)
                    self.diccionario_casillas[nombre_casilla].ruta_pieza = self.mapa_imagenes.get(
                        simbolo_final, '')

                    if gestor.estado_puzzle == "VICTORIA":
                        if self.sonido_ganar: self.sonido_ganar.play()

                        # Cálculo de ELO persistente[cite: 3]
                        variacion, nuevo_elo = self.registrar_resultado_puzzle(True)
                        self.ids.lbl_estado.text = self.formatear_resultado_puzzle(True, variacion, nuevo_elo)
                        self.ids.lbl_estado.color = [0, 1, 0, 1]

                        # Inyectamos el conocimiento traducido al saborear la victoria (¡Respetado!)
                        self.mostrar_temas_traducidos()

                        self.ids.btn_volver.opacity = 1
                        self.ids.btn_volver.disabled = False
                    else:
                        # Si no es victoria aún, preparamos la respuesta de la IA enemiga[cite: 3]
                        self.ids.lbl_estado.text = "¡Excelente! Responde la IA..."
                        self.ids.lbl_estado.color = [1, 1, 0, 1]
                        Clock.schedule_once(self.procesar_respuesta_ia, 0.4)

                # Disparamos la animación flotante sobre el tablero[cite: 3]
                self.animar_pieza(origen, nombre_casilla, simbolo_vuelo, terminar_vuelo)

            else:
                # Caso de movimiento erróneo (Derrota)[cite: 3]
                self.actualizar_piezas_visuales()
                if self.sonido_perder: self.sonido_perder.play()

                # Penalización de ELO[cite: 3]
                variacion, nuevo_elo = self.registrar_resultado_puzzle(False)
                self.ids.lbl_estado.text = self.formatear_resultado_puzzle(False, variacion, nuevo_elo)
                self.ids.lbl_estado.color = [1, 0.4, 0.4, 1]

                # Dibujamos vectores indicando la jugada que debió hacerse[cite: 3]
                mov_erroneo = gestor.movimiento_fallado
                if mov_erroneo:
                    self.mostrar_flecha_error(mov_erroneo)

                info = gestor.info_puzzle
                if info:
                    # Inyectamos el conocimiento traducido en la derrota (¡Respetado!)
                    self.mostrar_temas_traducidos()
                    self.ids.lbl_info.text = self.formatear_info_resultado(info)

                self.ids.btn_siguiente.text = "Siguiente Puzzle"
                self.ids.btn_volver.opacity = 1
                self.ids.btn_volver.disabled = False
                self._mostrar_acciones_fallo_general()
        else:
            # Seleccionar nueva pieza si no estábamos intentando mover[cite: 3]
            gestor.seleccionar_casilla(nombre_casilla)
            self.iluminar_casillas()
            if gestor.casilla_seleccionada and self.sonido_seleccionar:
                self.sonido_seleccionar.play()

    def evaluar_estado_jugador(self):
        """
        Callback que se ejecuta cuando el fantasma animado llega a destino.
        Restaura la visibilidad en la cuadrícula y actualiza la etiqueta global[cite: 3].
        """
        self.actualizar_piezas_visuales()
        gestor = self.gestor_ajedrez
        if gestor.estado_puzzle == "VICTORIA":
            self.ids.lbl_estado.text = "¡PUZZLE COMPLETADO!"
            self.ids.lbl_estado.color = [0, 1, 0, 1]
        else:
            self.ids.lbl_estado.text = "¡Excelente! Responde la IA..."
            self.ids.lbl_estado.color = [1, 1, 0, 1]
            Clock.schedule_once(self.procesar_respuesta_ia, 0.3)

    def procesar_respuesta_ia(self, dt: float) -> None:
        """
        Ejecuta y anima el movimiento de respuesta de la IA en la lección táctica.

        Sincroniza la vista mediante un callback asíncrono una vez concluida
        la animación del widget flotante.

        Args:
            dt (float): Delta time inyectado por Clock.schedule_once.
        """
        mov = self.gestor_ajedrez.ejecutar_movimiento_enemigo()
        print("Hola, soy una IA y soy gilipollas")
        if mov:
            origen, destino = mov[:2], mov[2:4]
            pieza = self.gestor_ajedrez.board.piece_at(chess.parse_square(destino))
            simbolo = pieza.symbol() if pieza else ''
            self.diccionario_casillas[origen].ruta_pieza = ''

            def terminar_animacion_ia() -> None:
                """Callback invocado al finalizar la animación de la IA."""
                self.actualizar_piezas_visuales()
                if self.sonido_mover:
                    self.sonido_mover.play()
                if self.gestor_ajedrez.estado_puzzle == "VICTORIA":
                    self.ids.lbl_estado.text = f"[color=#33cc33]{self.msg_correcto}[/color]"
                    self.revelar_boton("Siguiente", [0.2, 0.8, 0.4, 1])
                else:
                    self.ids.lbl_estado.text = "¡Tu turno! Continua."

            self.animar_pieza(origen, destino, simbolo, terminar_animacion_ia)

    def finalizar_turno_ia(self):
        """Alternativa bloqueante para restaurar las piezas (sin animación fantasma)."""
        self.actualizar_piezas_visuales()
        if self.sonido_mover: self.sonido_mover.play()

        if self.gestor_ajedrez.estado_puzzle == "VICTORIA":
            self.ids.lbl_estado.text = "¡PUZZLE COMPLETADO!"
            self.ids.lbl_estado.color = [0, 1, 0, 1]

            # Inyección de temas
            self.mostrar_temas_traducidos()
        else:
            self.ids.lbl_estado.text = "¡Tu turno! Continua."
            self.ids.lbl_estado.color = [0.9, 0.9, 0.9, 1]

    def iluminar_casillas(self):
        """Enciende las luces booleanas Kivy Properties para mostrar destinos legales[cite: 3]."""
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
        """Apaga forzosamente todos los indicadores visuales del tablero[cite: 3]."""
        for widget in self.diccionario_casillas.values():
            widget.origen_seleccionado = False
            widget.destino_valido = False

    def animar_pieza(self, origen, destino, simbolo, callback):
        """
        Crea un widget fantasma temporal, lo vuela sobre el Canvas absoluto
        de Kivy simulando el movimiento fluido y lo destruye al llegar[cite: 3].

        Args:
            origen (str): Coordenada inicial.
            destino (str): Coordenada objetivo.
            simbolo (str): Letra FEN de la pieza para localizar su textura PNG.
            callback (function): Función a invocar tras completar la animación.
        """
        c_origen = self.diccionario_casillas[origen]
        c_destino = self.diccionario_casillas[destino]

        # Convertimos coordenadas relativas a absolutas de la ventana global[cite: 3]
        pos_ini = c_origen.parent.to_window(c_origen.x, c_origen.y)
        pos_fin = c_destino.parent.to_window(c_destino.x, c_destino.y)

        fantasma = Image(
            source=self.mapa_imagenes.get(simbolo, ''),
            size_hint=(None, None),
            size=c_origen.size,
            pos=pos_ini
        )
        Window.add_widget(fantasma)

        # Animación exponencial in-out de 0.3 segundos[cite: 3]
        anim = Animation(pos=pos_fin, d=0.3, t='in_out_expo')

        def limpiar(*args):
            Window.remove_widget(fantasma)
            callback()

        anim.bind(on_complete=limpiar)
        anim.start(fantasma)

    def mostrar_flecha_error(self, mov_correcto):
        """
        Traza vectores geométricos puros sobre el lienzo si el jugador se equivoca,
        indicándole cuál era la solución real con una flecha verde[cite: 3].
        """
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
        """Elimina las formas geométricas del Canvas superior si existen[cite: 3]."""
        if hasattr(self, 'linea_error'):
            self.ids.cuadricula_tablero.canvas.after.remove(self.linea_error)
            self.ids.cuadricula_tablero.canvas.after.remove(self.triangulo_error)
            del self.linea_error
            del self.triangulo_error

    def salir_juego(self):
        """Aborta la aplicación de golpe llamando a la parada oficial del bucle[cite: 3]."""
        App.get_running_app().stop()

    def volver_menu(self):
        """
        Abandona el tablero de juego y retrocede elegantemente al menú principal.

        Corrige el infame error de enrutamiento del ScreenManager de Kivy
        apuntando directamente a la nueva pantalla raíz de nuestra arquitectura,
        dejando atrás los fantasmas del código obsoleto.
        """
        App.get_running_app().sm.current = 'menu_principal'

    def registrar_resultado_puzzle(self, victoria):
        """
        Calcula el ELO mediante números enteros puros y consolida el perfil.

        Extrae los metadatos del motor lógico y del perfil activo. Fuerza el uso
        exclusivo de enteros para aniquilar los espantosos decimales flotantes.
        El suelo de ELO se ha hundido hasta el 0 absoluto por orden divina del arquitecto.
        Delega la persistencia al gestor de almacenamiento JSON[cite: 8].

        Args:
            victoria (bool): True si el jugador resolvió el puzle, False si fracasó.

        Returns:
            tuple: (variacion_entera, nuevo_elo_entero) Listos para ser inyectados
                   en la interfaz sin rastro de decimales.
        """
        if getattr(App.get_running_app(), 'modo_leccion', False):
            return 0, int(self.perfil_actual.get("elo", 0))

        info = self.gestor_ajedrez.info_puzzle
        if not info:
            return 0, int(self.perfil_actual.get("elo", 0))

        # ¡Por los registros desbordados! Todo a entero y partiendo de 0 si hace falta.
        elo_puzzle = int(info.get("rating", 1000))
        elo_jugador = int(self.perfil_actual.get("elo", 0))
        partidas = int(self.perfil_actual.get("partidas_jugadas", 0))

        # Fórmula base con la asquerosa probabilidad esperada
        esperabilidad = 1.0 / (1.0 + math.pow(10, (elo_puzzle - elo_jugador) / 400.0))
        puntuacion = 1.0 if victoria else 0.0
        constante_k = 40.0 if partidas < 30 else 20.0

        # Magia matemática: calculamos, redondeamos y forzamos a entero estricto
        variacion_entera = int(round(constante_k * (puntuacion - esperabilidad)))

        # ¡El escudo protector ha caído! Ahora el suelo es 0 absoluto
        nuevo_elo = max(0, elo_jugador + variacion_entera)

        # Actualizamos las métricas de la memoria volátil
        self.perfil_actual["elo"] = nuevo_elo
        self.perfil_actual["partidas_jugadas"] = partidas + 1

        # Blindamos el historial asegurando que no haya duplicados[cite: 8]
        if victoria:
            id_puzzle = info.get("id")
            if id_puzzle and id_puzzle not in self.perfil_actual["resueltos"]:
                self.perfil_actual["resueltos"].append(id_puzzle)

        # Le pasamos el muerto a tu majestuosa máquina de estados y al gestor[cite: 8]
        escala = self.perfil_actual.get("escala_pop", 0)
        victorias_100 = self.perfil_actual.get("victorias_100", 0)
        nueva_escala, nuevas_victorias = GestorProgresionPop.calcular_siguiente_escala(
            escala, victorias_100, victoria
        )

        # Guardamos el estado puro en disco
        self.perfil_actual["escala_pop"] = nueva_escala
        self.perfil_actual["victorias_100"] = nuevas_victorias
        self.gestor_perfiles.guardar_perfil(self.perfil_actual)

        return variacion_entera, nuevo_elo

    def mostrar_temas_puzzle(self):
        """
        Extrae y renderiza los temas tácticos del puzle activo en la interfaz.

        Formatea la ruda cadena de texto separada por espacios que escupe
        la deficiente base de datos CSV en una elegante lista separada por puntos,
        lista para ser consumida por la vista de Kivy.
        """
        info = self.gestor_ajedrez.info_puzzle
        if info:
            temas = info.get('themes', '').replace(' ', ' • ')
            self.ids.lbl_temas.text = temas

    def mostrar_temas_traducidos(self):
        """
        Extrae los pestilentes temas en inglés del puzle activo.

        Los traduce usando el diccionario superior y los inyecta en la vista.
        Si un tema no existe en el mapeo, lo capitaliza por defecto.
        """
        info = self.gestor_ajedrez.info_puzzle
        if info:
            temas_crudos = info.get('themes', '').split()
            temas_limpios = [DICCIONARIO_TEMAS.get(t, t.capitalize()) for t in temas_crudos]
            self.ids.lbl_temas.text = ' • '.join(temas_limpios)



    def cargar_puzzle_prueba(self, id_puzzle: str) -> None:
        """
        Fuerza la carga de un puzle específico para probar mecánicas complejas.

        Solicita al PuzzleManager el puzle por su ID y reinicia completamente
        el estado visual y lógico del tablero. Aniquila cualquier progreso
        del puzle anterior para evitar bugs de colisión de estados[cite: 3].

        Args:
            id_puzzle (str): El identificador FEN/CSV del puzle a inyectar (ej. '1qC2F').

        Returns:
            None
        """
        # Exigimos el puzzle por la fuerza bruta a nuestro gestor[cite: 3]
        puzzle_test = self.gestor_puzzles.obtener_puzzle_por_id(id_puzzle)

        if puzzle_test:
            self._restablecer_panel_solucion_general()
            # Reseteamos el motor lógico de ajedrez con el nuevo FEN
            self.gestor_ajedrez.cargar_puzzle(puzzle_test)

            # Forzamos a la burocracia de Kivy a redibujar todo desde cero[cite: 3]
            self.inicializar_tablero()
            self.actualizar_piezas_visuales()
            self.limpiar_flecha()

            # Reseteo estético del panel de información inferior[cite: 3]
            self.ids.lbl_temas.text = "Modo Depuración Activo"
            self.ids.btn_siguiente.text = "SIGUIENTE PUZZLE"
            self.ids.btn_volver.opacity = 0
            self.ids.btn_volver.disabled = True

            # Le indicamos al jugador a quién le toca
            es_blancas = self.gestor_ajedrez.board.turn == chess.WHITE
            color_turno = "[color=#ffffff]BLANCAS[/color]" if es_blancas else "[color=#ff6b6b]NEGRAS[/color]"
            self.ids.lbl_estado.text = f"Tu turno: {color_turno}"
        else:
            self.ids.lbl_estado.text = "[color=#ff0000]ERROR: Puzzle no encontrado.[/color]"


class VistaLeccion(BoxLayout):
    """
    Orquestador gráfico dedicado exclusivamente a la asimilación táctica.

    Aislado por completo de la persistencia de perfiles y los cálculos de ELO.
    Solo valida el movimiento y permite al usuario regresar al texto teórico.
    """

    def __init__(self, gestor_ajedrez, msg_correcto="¡MAGISTRAL! Lección dominada.", msg_error="¡ERROR FATAL! Repasa la teoría.", **kwargs):
        """
        Inicializa el tablero de la lección almacenando los textos de respuesta.
        """

        super().__init__(**kwargs)
        self.gestor_ajedrez = gestor_ajedrez
        self.msg_correcto = msg_correcto
        self.msg_error = msg_error
        self.diccionario_casillas = {}

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.sonido_seleccionar = SoundLoader.load(
            os.path.join(BASE_DIR, 'assets', 'sounds', 'select.wav'))
        self.sonido_mover = SoundLoader.load(os.path.join(BASE_DIR, 'assets', 'sounds', 'move.wav'))
        self.sonido_ganar = SoundLoader.load(os.path.join(BASE_DIR, 'assets', 'sounds', 'win.wav'))
        self.sonido_perder = SoundLoader.load(
            os.path.join(BASE_DIR, 'assets', 'sounds', 'lose.wav'))

        self.mapa_imagenes = {
            'P': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_peon.png'),
            'p': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_peon.png'),
            'N': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_caballo.png'),
            'n': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_caballo.png'),
            'B': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_alfil.png'),
            'b': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_alfil.png'),
            'R': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_torre.png'),
            'r': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_torre.png'),
            'Q': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_reina.png'),
            'q': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_reina.png'),
            'K': os.path.join(BASE_DIR, 'assets', 'pieces', 'blanco_rey.png'),
            'k': os.path.join(BASE_DIR, 'assets', 'pieces', 'negro_rey.png')
        }
        self.inicializar_tablero()
        self.actualizar_piezas_visuales()

    def inicializar_tablero(self) -> None:
        cuadricula = self.ids.cuadricula_tablero
        cuadricula.clear_widgets()
        self.diccionario_casillas.clear()

        juega_blancas = self.gestor_ajedrez.board.turn
        filas = list(range(7, -1, -1)) if juega_blancas else list(range(8))
        columnas = list(range(8)) if juega_blancas else list(range(7, -1, -1))

        for fila in filas:
            for col in columnas:
                nombre = chess.square_name(chess.square(col, fila))
                casilla = Casilla(nombre_casilla=nombre, controlador=self)
                es_clara = (fila + col) % 2 != 0
                casilla.ruta_fondo = "assets/squares/casilla_clara.png" if es_clara else "assets/squares/casilla_oscura.png"

                if col == columnas[0]: casilla.texto_fila = nombre[1]
                if fila == filas[-1]: casilla.texto_col = nombre[0]

                self.diccionario_casillas[nombre] = casilla
                cuadricula.add_widget(casilla)

    def actualizar_piezas_visuales(self) -> None:
        tablero = self.gestor_ajedrez.board
        for nombre, widget in self.diccionario_casillas.items():
            pieza = tablero.piece_at(chess.parse_square(nombre))
            widget.ruta_pieza = self.mapa_imagenes.get(pieza.symbol(), '') if pieza else ''

        if self.gestor_ajedrez.estado_puzzle == "JUGANDO":
            es_blancas = tablero.turn == chess.WHITE
            color = "[color=#ffffff]BLANCAS[/color]" if es_blancas else "[color=#ff6b6b]NEGRAS[/color]"
            self.ids.lbl_estado.text = f"Encuentra el movimiento para: {color}"

    def al_tocar_casilla(self, nombre_casilla: str) -> None:
        gestor = self.gestor_ajedrez

        if gestor.casilla_seleccionada and nombre_casilla in gestor.movimientos_validos:
            origen = gestor.casilla_seleccionada
            pieza_antes = gestor.board.piece_at(chess.parse_square(origen))
            simbolo_vuelo = pieza_antes.symbol() if pieza_antes else ''

            exito = gestor.intentar_movimiento_jugador(nombre_casilla)
            self.limpiar_iluminacion()

            if exito:
                if self.sonido_mover: self.sonido_mover.play()
                pieza_despues = gestor.board.piece_at(chess.parse_square(nombre_casilla))
                simbolo_final = pieza_despues.symbol() if pieza_despues else simbolo_vuelo

                self.actualizar_piezas_visuales()
                self.diccionario_casillas[nombre_casilla].ruta_pieza = ''

                def terminar_vuelo() -> None:
                    self.diccionario_casillas[nombre_casilla].ruta_pieza = self.mapa_imagenes.get(
                        simbolo_final, '')
                    if gestor.estado_puzzle == "VICTORIA":
                        if self.sonido_ganar: self.sonido_ganar.play()
                        self.ids.lbl_estado.text = f"[color=#33cc33]{self.msg_correcto}[/color]"
                        self.revelar_boton("Siguiente",[0.2, 0.8, 0.4, 1])
                    else:
                        self.ids.lbl_estado.text = "¡Excelente! Responde la IA..."
                        Clock.schedule_once(self.procesar_respuesta_ia, 0.4)

                self.animar_pieza(origen, nombre_casilla, simbolo_vuelo, terminar_vuelo)
            else:
                self.actualizar_piezas_visuales()
                if self.sonido_perder: self.sonido_perder.play()
                self.ids.lbl_estado.text = f"[color=#cc3333]{self.msg_error}[/color]"

                if gestor.movimiento_fallado:
                    self.mostrar_flecha_error(gestor.movimiento_fallado)

                self.revelar_boton("Siguiente",[0.8, 0.4, 0.1, 1])
        else:
            gestor.seleccionar_casilla(nombre_casilla)
            self.iluminar_casillas()
            if gestor.casilla_seleccionada and self.sonido_seleccionar:
                self.sonido_seleccionar.play()

    # Importa el logger en la cabecera de tu main.py
    from utilidades_log import configurar_logger

    # Inicializa el espía a nivel de módulo
    log = configurar_logger("VistaLeccion")

    # ... (dentro de tu clase VistaLeccion) ...

    def procesar_respuesta_ia(self, dt: float) -> None:
        """
        Ejecuta y anima el movimiento de respuesta de la máquina enemiga.

        Dispara trazas físicas al disco duro para evidenciar si el motor
        gráfico asíncrono está matando el hilo silenciosamente.

        Args:
            dt (float): Tiempo diferencial inyectado por Clock.schedule_once.
        """
        if LOG_DEBUG:
            log.debug(f"INICIO: procesar_respuesta_ia invocado por Clock con dt={dt}")

        mov = self.gestor_ajedrez.ejecutar_movimiento_enemigo()
        if LOG_DEBUG:
            log.debug(f"Motor lógico devolvió el movimiento: {mov}")

        if mov:
            origen, destino = mov[:2], mov[2:4]
            if LOG_DEBUG:
                log.info(f"Procesando texturas de {origen} hacia {destino}")

            pieza = self.gestor_ajedrez.board.piece_at(chess.parse_square(destino))
            simbolo = pieza.symbol() if pieza else ''

            self.diccionario_casillas[origen].ruta_pieza = ''
            if LOG_DEBUG:
                log.debug("Textura de origen borrada con éxito.")

            def terminar_animacion_ia() -> None:
                """Callback invocado al concluir el deslizamiento visual."""
                if LOG_DEBUG:
                    log.debug("CALLBACK: terminar_animacion_ia ejecutado por Animation.")
                self.actualizar_piezas_visuales()

                if self.sonido_mover:
                    self.sonido_mover.play()

                if self.gestor_ajedrez.estado_puzzle == "VICTORIA":
                    self.ids.lbl_estado.text = f"[color=#33cc33]{self.msg_correcto}[/color]"
                    self.revelar_boton("Siguiente", [0.2, 0.8, 0.4, 1])
                else:
                    self.ids.lbl_estado.text = "¡Tu turno! Continua."

            if LOG_DEBUG:
                log.info(f"Disparando self.animar_pieza para el símbolo '{simbolo}'")
            self.animar_pieza(origen, destino, simbolo, terminar_animacion_ia)
            if LOG_DEBUG:
                log.debug("FIN: procesar_respuesta_ia. Animación entregada a Kivy.")
        else:
            if LOG_DEBUG:
                log.warning("El motor lógico devolvió None. No hay movimiento enemigo pendiente.")

    def revelar_boton(self, texto: str, color: list) -> None:
        self.ids.btn_continuar.text = texto
        self.ids.btn_continuar.background_color = color
        self.ids.btn_continuar.opacity = 1
        self.ids.btn_continuar.disabled = False

    def retornar_visor(self) -> None:
        """
        Restaura la pantalla de teoría tras sobrevivir a la emboscada táctica.

        Destruye el modo lección y fuerza el salto capitular si el puzzle
        era el último aliento de la sección actual.
        """
        from kivy.app import App
        app = App.get_running_app()
        app.modo_leccion = False
        visor = app.sm.get_screen('escuela_visor')

        if visor.indice_pagina < len(visor.paginas) - 1:
            visor.indice_pagina += 1
            visor.mostrar_pagina()
            app.sm.current = 'escuela_visor'
        else:
            menu = app.sm.get_screen('menu_leccion')
            exito = menu.avanzar_siguiente_capitulo()
            if not exito:
                app.sm.current = 'escuela_visor'

    def iluminar_casillas(self) -> None:
        self.limpiar_iluminacion()
        gestor = self.gestor_ajedrez
        if gestor.casilla_seleccionada:
            c_orig = self.diccionario_casillas.get(gestor.casilla_seleccionada)
            if c_orig: c_orig.origen_seleccionado = True
            for d in gestor.movimientos_validos:
                c_dest = self.diccionario_casillas.get(d)
                if c_dest: c_dest.destino_valido = True

    def limpiar_iluminacion(self) -> None:
        for widget in self.diccionario_casillas.values():
            widget.origen_seleccionado = False
            widget.destino_valido = False

    def animar_pieza(self, origen: str, destino: str, simbolo: str, callback) -> None:
        co = self.diccionario_casillas[origen]
        cd = self.diccionario_casillas[destino]
        pos_ini = co.parent.to_window(co.x, co.y)
        pos_fin = cd.parent.to_window(cd.x, cd.y)

        fantasma = Image(source=self.mapa_imagenes.get(simbolo, ''), size_hint=(None, None),
                         size=co.size, pos=pos_ini)
        Window.add_widget(fantasma)

        anim = Animation(pos=pos_fin, d=0.3, t='in_out_expo')

        def limpiar(*args):
            Window.remove_widget(fantasma)
            callback()

        anim.bind(on_complete=limpiar)
        anim.start(fantasma)

    def mostrar_flecha_error(self, mov: str) -> None:
        co = self.diccionario_casillas.get(mov[:2])
        cd = self.diccionario_casillas.get(mov[2:4])
        if not co or not cd: return

        x1, y1 = co.x + co.width / 2, co.y + co.height / 2
        x2, y2 = cd.x + cd.width / 2, cd.y + cd.height / 2

        with self.ids.cuadricula_tablero.canvas.after:
            Color(0.4, 0.8, 0.4, 0.7)
            self.linea_error = Line(points=[x1, y1, x2, y2], width=dp(4))
            angulo = math.atan2(y2 - y1, x2 - x1)
            l = dp(16)
            p2 = (x2 - l * math.cos(angulo - math.pi / 6), y2 - l * math.sin(angulo - math.pi / 6))
            p3 = (x2 - l * math.cos(angulo + math.pi / 6), y2 - l * math.sin(angulo + math.pi / 6))
            self.triangulo_error = Triangle(points=[x2, y2, p2[0], p2[1], p3[0], p3[1]])

class PopupElo(Popup):
    """
    Controlador de la ventana emergente modal para mostrar la variación de ELO.

    Aísla la lógica gráfica del pop-up de la VistaTablero, manejando los colores
    y textos dinámicamente según si el usuario ha triunfado o fracasado miserablemente.
    """

    mensaje = StringProperty('')
    color_tema = ListProperty([1, 1, 1, 1])

    def __init__(self, variacion, victoria, **kwargs):
        """
        Inicializa el modal inyectando los datos del cálculo de ELO.

        Args:
            variacion (float): La cantidad exacta de puntos devueltos por el CalculadorElo.
            victoria (bool): True si el jugador resolvió el puzle, False en caso contrario.
        """
        super().__init__(**kwargs)

        if victoria:
            self.title = '¡Victoria Magistral!'
            self.color_tema = [0.1, 0.8, 0.2, 1]  # Verde radiactivo para la victoria
            self.mensaje = f"Has resuelto el puzle con éxito.\\n\\nTu ELO sube: [color=#33cc33][b]+{variacion:.1f}[/b][/color] puntos."
        else:
            self.title = '¡Derrota Humillante!'
            self.color_tema = [0.9, 0.2, 0.2, 1]  # Rojo sangre para el fracaso
            self.mensaje = f"Movimiento incorrecto.\\n\\nTu ELO cae: [color=#cc3333][b]{variacion:.1f}[/b][/color] puntos."


class PopupCoronacion(Popup):
    """
    Ventana emergente modal (Popup) para seleccionar explícitamente la pieza de coronación.

    Este componente visual de Kivy intercepta la interacción del usuario cuando
    un peón alcanza la octava (o primera) fila. Despliega las cuatro opciones
    reglamentarias (Reina, Torre, Alfil, Caballo) cargando dinámicamente las
    texturas correspondientes al color del jugador.

    Attributes:
        img_reina (StringProperty): Ruta dinámica al sprite de la Reina.
        img_torre (StringProperty): Ruta dinámica al sprite de la Torre.
        img_alfil (StringProperty): Ruta dinámica al sprite del Alfil.
        img_caballo (StringProperty): Ruta dinámica al sprite del Caballo.
    """

    # Enlaces mágicos con el parser KV de Kivy[cite: 3]
    img_reina = StringProperty('')
    img_torre = StringProperty('')
    img_alfil = StringProperty('')
    img_caballo = StringProperty('')

    def __init__(self, color_pieza_blanca: bool, callback_seleccion: Callable[[str], None],
                 **kwargs) -> None:
        """
        Inicializa el modal inyectando las texturas correctas según el color a coronar.

        Args:
            color_pieza_blanca (bool): True si el jugador corona piezas blancas,
                                       False si corona piezas negras.
            callback_seleccion (Callable[[str], None]): Función a invocar devolviendo
                                                        el símbolo de la pieza elegida
                                                        ('q', 'r', 'b', 'n').
            **kwargs: Argumentos absorbidos implícitamente por el padre `Popup` de Kivy[cite: 3].
        """
        super().__init__(**kwargs)
        self.callback_seleccion = callback_seleccion

        # Aprovechamos la misma estructura de rutas y convenciones de nombres de tu mapa_imagenes[cite: 3]
        prefijo = "blanco" if color_pieza_blanca else "negro"

        self.img_reina = f"assets/pieces/{prefijo}_reina.png"
        self.img_torre = f"assets/pieces/{prefijo}_torre.png"
        self.img_alfil = f"assets/pieces/{prefijo}_alfil.png"
        self.img_caballo = f"assets/pieces/{prefijo}_caballo.png"

    def seleccionar_pieza(self, simbolo: str) -> None:
        """
        Captura la pulsación del usuario sobre un botón de pieza y despacha el símbolo.

        Invoca el callback almacenado, inyectándole la letra FEN, y destruye la
        ventana modal para devolverle el foco al tablero principal.

        Args:
            simbolo (str): Letra FEN minúscula de la pieza elegida ('q', 'r', 'b', 'n').

        Returns:
            None
        """
        self.callback_seleccion(simbolo)
        self.dismiss()


class PopupCambiarElo(Popup):
    """
    Controlador modal para sobrescribir la puntuación del jugador.
    """

    def __init__(self, perfil_actual, gestor_perfiles, **kwargs):
        super().__init__(**kwargs)
        self.perfil_actual = perfil_actual
        self.gestor_perfiles = gestor_perfiles
        self.ids.lbl_elo_actual.text = f"ELO Actual: {self.perfil_actual.get('elo', 0)}"

    def guardar_cambios(self) -> None:
        """Valida el texto, actualiza el diccionario y persiste en disco."""
        texto = self.ids.input_nuevo_elo.text.strip()
        if texto:
            try:
                nuevo_elo = int(texto)
                self.perfil_actual["elo"] = max(0, nuevo_elo)
                self.gestor_perfiles.guardar_perfil(self.perfil_actual)
            except ValueError:
                pass
        self.dismiss()


class PopupBorrarRegistros(Popup):
    """
    Controlador modal para purgar el historial de tácticas completadas.
    """

    def __init__(self, perfil_actual, gestor_perfiles, **kwargs):
        super().__init__(**kwargs)
        self.perfil_actual = perfil_actual
        self.gestor_perfiles = gestor_perfiles
        resueltos = len(self.perfil_actual.get('resueltos', []))
        self.ids.lbl_puzzles.text = f"Puzzles resueltos: {resueltos}"

    def confirmar_borrado(self) -> None:
        """Aniquila las listas del perfil y reinicia contadores."""
        self.perfil_actual["resueltos"] = []
        self.perfil_actual["partidas_jugadas"] = 0
        self.perfil_actual["escala_pop"] = 0
        self.perfil_actual["victorias_100"] = 0
        self.gestor_perfiles.guardar_perfil(self.perfil_actual)
        self.dismiss()


class PopupBorrarUsuario(Popup):
    """
    Controlador modal para la destrucción irreversible de perfiles.

    Intercepta la intención de borrado para evitar que un misclick destruya
    meses de tácticas resueltas. Delega la eliminación física al sistema operativo.
    """
    mensaje = StringProperty('')

    def __init__(self, nombre_usuario, pantalla_padre, gestor_perfiles, **kwargs):
        """
        Inicializa la advertencia de aniquilación de datos.

        Args:
            nombre_usuario (str): Identificador exacto del archivo a eliminar.
            pantalla_padre (PantallaGestionUsuarios): Referencia a la vista contenedora
                                                      para forzar su repintado.
            gestor_perfiles (PerfilManager): Interfaz de acceso al disco.
        """
        super().__init__(**kwargs)
        self.nombre_usuario = nombre_usuario
        self.pantalla_padre = pantalla_padre
        self.gestor_perfiles = gestor_perfiles
        self.mensaje = f"¿Destruir para siempre el perfil de [b]{nombre_usuario}[/b]?"

    def confirmar_borrado(self) -> None:
        """
        Ejecuta la eliminación física del archivo JSON del sistema.
        """
        ruta = os.path.join(self.gestor_perfiles.directorio, f"{self.nombre_usuario}.json")
        if os.path.exists(ruta):
            os.remove(ruta)

        ultimo = self.gestor_perfiles.obtener_ultimo_usuario()
        if ultimo == self.nombre_usuario:
            self.gestor_perfiles.fijar_ultimo_usuario("")

        self.pantalla_padre.poblar_usuarios()
        self.dismiss()


class PopupEnConstruccion(Popup):
    """
    Ventana modal genérica para notificar al usuario sobre características futuras.

    Aísla las pulsaciones de botones aún no implementados para evitar que la
    aplicación colapse o parezca que no responde.
    """
    pass

class PantallaGestionUsuarios(Screen):
    """
    Panel de administración para la creación y exterminio de perfiles.

    Actúa como controlador aislando el repugnante renderizado de botones dinámicos
    del modelo de datos subyacente.
    """

    def __init__(self, gestor_perfiles, **kwargs):
        """
        Prepara el panel inyectando la dependencia del gestor de archivos.

        Args:
            gestor_perfiles (PerfilManager): Motor de persistencia.
        """
        super().__init__(**kwargs)
        self.gestor_perfiles = gestor_perfiles

    def on_pre_enter(self, *args) -> None:
        """Fuerza la lectura del disco justo antes de mostrar la pantalla."""
        self.poblar_usuarios()

    def poblar_usuarios(self) -> None:
        """
        Barre el directorio de perfiles y escupe un botón de borrado por cada uno.
        """
        self.ids.grid_usuarios.clear_widgets()
        usuarios = self.gestor_perfiles.obtener_lista_usuarios()

        for u in usuarios:
            caja = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50),
                             spacing=dp(5))

            btn_nombre = Button(
                text=u,
                background_color=(0.2, 0.6, 0.8, 1),
                bold=True,
                size_hint_x=0.7
            )

            btn_borrar = Button(
                text='X',
                background_color=(0.9, 0.2, 0.2, 1),
                bold=True,
                size_hint_x=0.3
            )
            btn_borrar.bind(on_release=lambda instance, nombre=u: self.solicitar_borrado(nombre))

            caja.add_widget(btn_nombre)
            caja.add_widget(btn_borrar)
            self.ids.grid_usuarios.add_widget(caja)

    def solicitar_borrado(self, nombre_usuario: str) -> None:
        """Instancia y lanza la ventana modal de confirmación."""
        PopupBorrarUsuario(nombre_usuario, self, self.gestor_perfiles).open()

    def crear_usuario(self) -> None:
        """
        Fuerza la serialización de un nuevo archivo JSON en el directorio.
        """
        nombre = self.ids.input_nuevo_nombre.text.strip()
        texto_elo = self.ids.input_nuevo_elo.text.strip()

        if nombre:
            try:
                elo_inicial = int(texto_elo)
            except ValueError:
                elo_inicial = 0

            elo_inicial = max(0, elo_inicial)

            nuevo_perfil = self.gestor_perfiles.cargar_perfil(nombre)
            nuevo_perfil["elo"] = elo_inicial
            self.gestor_perfiles.guardar_perfil(nuevo_perfil)

            self.ids.input_nuevo_nombre.text = ''
            self.ids.input_nuevo_elo.text = ''
            self.poblar_usuarios()

    def volver_menu(self) -> None:
        """Regresa al menú principal."""
        App.get_running_app().sm.current = 'menu_principal'


class PantallaConfiguracion(Screen):
    """
    Vista y orquestador maestro del panel de preferencias del usuario.

    Implementa el Controlador en la arquitectura MVC, enrutando los comandos
    hacia los modales emergentes o alterando la máquina de estados de las vistas.
    """

    def __init__(self, gestor_perfiles, **kwargs):
        super().__init__(**kwargs)
        self.gestor_perfiles = gestor_perfiles
        self.perfil_actual = None

    def on_pre_enter(self, *args) -> None:
        """Carga el perfil activo justo antes de renderizar la pantalla."""
        ultimo = self.gestor_perfiles.obtener_ultimo_usuario()
        if ultimo:
            self.perfil_actual = self.gestor_perfiles.cargar_perfil(ultimo)
            self.ids.lbl_usuario.text = str(ultimo)
        else:
            self.ids.lbl_usuario.text = "Desconocido"

    def abrir_popup_elo(self) -> None:
        """Despliega la ventana de edición de ELO."""
        if self.perfil_actual:
            PopupCambiarElo(self.perfil_actual, self.gestor_perfiles).open()

    def abrir_popup_registros(self) -> None:
        """Despliega la ventana de confirmación de borrado."""
        if self.perfil_actual:
            PopupBorrarRegistros(self.perfil_actual, self.gestor_perfiles).open()

    def jugar_general(self) -> None:
        """Inicia el motor de juego en modo estándar."""
        app = App.get_running_app()
        if self.perfil_actual:
            app.iniciar_juego(self.perfil_actual["nombre"])

    def volver_menu(self) -> None:
        """Retorna a la pantalla principal de la aplicación."""
        App.get_running_app().sm.current = 'menu_principal'

    # def abrir_temas(self) -> None:
    #     """
    #     Despliega un aviso temporal (Placeholder) para el futuro selector de temas.
    #     """
    #     PopupEnConstruccion().open()
    #
    # def abrir_escuela(self) -> None:
    #     """
    #     Despacha el evento al gestor de pantallas de Kivy para cargar la Vista
    #     de selección de temario.
    #     """
    #     from kivy.app import App
    #     App.get_running_app().sm.current = 'escuela_temas'
    #
    # def jugar_general(self) -> None:
    #     """Propulsa la aplicación hacia el tablero de juego estándar."""
    #     app = App.get_running_app()
    #     if self.perfil_actual:
    #         app.iniciar_juego(self.perfil_actual["nombre"])


class PantallaPractica(Screen):
    """
    Vista y orquestador maestro del panel de práctica.

    Implementa el Controlador en la arquitectura MVC, enrutando los comandos
    hacia los modales emergentes o alterando la máquina de estados de las vistas.
    """

    def __init__(self, gestor_perfiles, **kwargs):
        super().__init__(**kwargs)
        self.gestor_perfiles = gestor_perfiles
        self.perfil_actual = None

    def on_pre_enter(self, *args) -> None:
        """Carga el perfil activo justo antes de renderizar la pantalla."""
        ultimo = self.gestor_perfiles.obtener_ultimo_usuario()
        if ultimo:
            self.perfil_actual = self.gestor_perfiles.cargar_perfil(ultimo)
            self.ids.lbl_usuario.text = str(ultimo)
        else:
            self.ids.lbl_usuario.text = "Desconocido"

    def jugar_general(self) -> None:
        """Inicia el motor de juego en modo estándar."""
        app = App.get_running_app()
        if self.perfil_actual:
            app.iniciar_juego(self.perfil_actual["nombre"])

    def volver_menu(self) -> None:
        """Retorna a la pantalla principal de la aplicación."""
        App.get_running_app().sm.current = 'menu_principal'

    def abrir_temas(self) -> None:
        """
        Despliega un aviso temporal (Placeholder) para el futuro selector de temas.
        """
        PopupEnConstruccion().open()

    def abrir_escuela(self) -> None:
        """
        Despacha el evento al gestor de pantallas de Kivy para cargar la Vista
        de selección de temario.
        """
        from kivy.app import App
        App.get_running_app().sm.current = 'escuela_temas'


class PantallaMenuPrincipal(Screen):
    """
    Vista y controlador del menú principal de la aplicación.

    Implementa el patrón MVC aislando la interfaz gráfica de la
    lógica de persistencia de perfiles.
    """

    def __init__(self, gestor_perfiles, **kwargs):
        """
        Inicializa la pantalla del menú principal.

        Args:
            gestor_perfiles (PerfilManager): Instancia del modelo de datos local.
            **kwargs: Argumentos absorbidos por Kivy.
        """
        super().__init__(**kwargs)
        self.gestor_perfiles = gestor_perfiles

    def on_pre_enter(self, *args):
        """
        Intercepta el evento de renderizado de la pantalla.

        Fuerza la actualización del nombre de usuario leyendo el disco duro.
        """
        self.cargar_ultimo_usuario()

    def cargar_ultimo_usuario(self):
        """
        Interroga al modelo de datos para obtener el último perfil activo.
        """
        ultimo = self.gestor_perfiles.obtener_ultimo_usuario()

        if ultimo:
            self.ids.lbl_usuario.text = f"USUARIO: {ultimo}"
        else:
            self.ids.lbl_usuario.text = "USUARIO: Desconocido"

    def abrir_configuracion(self):
        """
        Transiciona a la pantalla de preferencias del jugador activo.
        """
        App.get_running_app().sm.current = 'configuracion'

    def cambiar_usuario(self):
        """
        Transiciona a la vista de selección de perfiles alternativos.
        """
        App.get_running_app().sm.current = 'cambiar_usuario'

    def gestionar_usuarios(self):
        """
        Transiciona al panel de administración de cuentas.
        """
        App.get_running_app().sm.current = 'gestion_usuarios'

    def abrir_practica(self):
        """
        Transiciona a la pantalla de preferencias del jugador activo.
        """
        App.get_running_app().sm.current = 'practica'


def inyectar_tipografia_personalizada() -> None:
    """
    Sobrescribe la aburrida fuente Roboto que Kivy utiliza por defecto.

    Obliga al motor de renderizado de texto a utilizar un archivo TrueType Font (.ttf)
    personalizado en todos los componentes de la interfaz (Labels, Buttons, TextInputs)
    de forma global, preservando la limpieza del archivo .kv.
    """
    # Define la ruta exacta donde has guardado tu obra de arte tipográfica
    ruta_fuente = 'assets/fonts/BD_Cartoon_Shout.ttf'
    ruta_michroma = 'assets/fonts/Michroma-Regular.ttf'
    # Secuestramos el núcleo tipográfico de Kivy
    LabelBase.register(DEFAULT_FONT, ruta_fuente)
    LabelBase.register('Michroma', ruta_michroma)

    # Resurrección de la tipografía seria
    ruta_roboto = os.path.join(kivy.kivy_data_dir, 'fonts', 'Roboto-Regular.ttf')
    LabelBase.register('RobotoSerio', ruta_roboto)

inyectar_tipografia_personalizada()
# class PantallaMenuPrincipal(Screen):
#     """
#     Vista y controlador del menú principal de Mind Chess.
#
#     Implementa el patrón MVC actuando como puente entre la interfaz gráfica
#     y el gestor de perfiles. Proporciona los puntos de anclaje para la
#     navegación hacia las distintas secciones de gestión de la aplicación.
#     """
#
#     def __init__(self, gestor_perfiles, **kwargs):
#         """
#         Inicializa la pantalla del menú principal e inyecta las dependencias.
#
#         Args:
#             gestor_perfiles (PerfilManager): Instancia del modelo de persistencia
#                                              para acceder a los datos locales.
#             **kwargs: Argumentos absorbidos implícitamente por Kivy.
#         """
#         super().__init__(**kwargs)
#         self.gestor_perfiles = gestor_perfiles
#         self.cargar_ultimo_usuario()
#
#     def cargar_ultimo_usuario(self) -> None:
#         """
#         Interroga al modelo de datos y actualiza la etiqueta visual del jugador.
#
#         Asigna 'Desconocido' como medida de seguridad si el archivo JSON
#         está vacío o el sistema de archivos de Android se pone rebelde.
#         """
#         ultimo_usuario = self.gestor_perfiles.obtener_ultimo_usuario()
#
#         if ultimo_usuario:
#             texto_mostrar = f"USUARIO: {ultimo_usuario}"
#         else:
#             texto_mostrar = "USUARIO: Desconocido"
#
#         self.ids.lbl_usuario.text = texto_mostrar
#
#     def on_pre_enter(self, *args) -> None:
#         """
#         Intercepta el evento de renderizado justo antes de mostrar la pantalla.
#
#         Fuerza la actualización del nombre de usuario en caso de que el jugador
#         haya cambiado su perfil activo en una pantalla secundaria.
#         """
#         self.cargar_ultimo_usuario()
#
#     def abrir_configuracion(self) -> None:
#         """
#         Despacha el evento para transicionar a la pantalla de configuración.
#         """
#         print("Stub: Navegar a Configuración del usuario activo")
#
#     def cambiar_usuario(self) -> None:
#         """
#         Despacha el evento para transicionar a la selección de perfiles.
#         """
#         from kivy.app import App
#         App.get_running_app().sm.current = 'cambiar_usuario'
#
#     def gestionar_usuarios(self) -> None:
#         """
#         Despacha el evento para transicionar al panel de administración.
#         """
#         print("Stub: Navegar a Gestión de Usuarios")

class ChessApp(App):
    """
    Clase principal que inicializa y gestiona el ciclo de vida de la aplicación.

    Actúa como el orquestador maestro del patrón MVC, enlazando los modelos de
    datos (perfiles, ajedrez y puzles) con las vistas basadas en el burocrático
    ecosistema de Kivy. Implementa un ScreenManager para navegar elegantemente
    entre el menú de selección y el tablero de juego.
    """

    def build(self):
        """
        Construye la jerarquía de la interfaz gráfica y prepara las dependencias.

        Instancia los controladores lógicos para la persistencia de usuarios[cite: 4],
        el motor de validación de ajedrez[cite: 1] y la base de datos de tácticas[cite: 5].
        A continuación, configura el gestor de pantallas (ScreenManager) inyectando
        las dependencias en la pantalla de selección para evitar un acoplamiento duro.

        Returns:
            ScreenManager: El widget raíz que contendrá y gestionará las transiciones
                           entre todas las pantallas de la aplicación.
        """
        Builder.load_file('interfaz.kv')
        Builder.load_file('escuela.kv')
        # Doblegamos la voluntad de Android justo antes de arrancar la interfaz gráfica
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])

        # Inicialización de la capa de Modelos
        self.gestor_perfiles = PerfilManager()
        self.gestor_ajedrez = ChessManager()
        self.gestor_puzzles = PuzzleManager()

        # Inicialización del Controlador Gráfico Maestro
        self.sm = ScreenManager()

        # 1. Menú Principal (Pantalla de aterrizaje)
        pantalla_menu = PantallaMenuPrincipal(
            gestor_perfiles=self.gestor_perfiles,
            name='menu_principal'
        )
        self.sm.add_widget(pantalla_menu)

        # 2. Pantalla de Cambio de Usuario (Sustituye a la antigua selección)
        pantalla_cambiar = PantallaCambiarUsuario(
            gestor_perfiles=self.gestor_perfiles,
            al_seleccionar=self.iniciar_juego,
            name='cambiar_usuario'
        )
        self.sm.add_widget(pantalla_cambiar)

        # 3. Pantalla de Gestión (Para crear y fulminar perfiles)
        pantalla_gestion = PantallaGestionUsuarios(
            gestor_perfiles=self.gestor_perfiles,
            name='gestion_usuarios'
        )
        self.sm.add_widget(pantalla_gestion)

        # 4. Pantalla de Configuración del Perfil
        pantalla_configuracion = PantallaConfiguracion(
            gestor_perfiles=self.gestor_perfiles,
            name='configuracion'
        )
        self.sm.add_widget(pantalla_configuracion)

        # 5. Contenedor de la Vista del Tablero de Ajedrez
        self.pantalla_juego = Screen(name='juego')
        self.sm.add_widget(self.pantalla_juego)

        # 6. Pantalla de Practica
        pantalla_practica = PantallaPractica(
            gestor_perfiles=self.gestor_perfiles,
            name='practica'
        )
        self.sm.add_widget(pantalla_practica)

        # Forzamos la entrada inicial al menú principal por si Kivy se despista
        self.sm.current = 'menu_principal'

        # 7. Controlador de Categorías de la Escuela
        pantalla_escuela_temas = PantallaEscuelaTemas(name='escuela_temas')
        self.sm.add_widget(pantalla_escuela_temas)

        # 8. Visor de Unidades y Temario
        pantalla_escuela_unidades = PantallaEscuelaUnidades(
            gestor_perfiles=self.gestor_perfiles,
            name='escuela_unidades'
        )
        self.sm.add_widget(pantalla_escuela_unidades)

        # 9. Controlador del submenú de disección de lecciones
        from escuela_controladores import PantallaMenuLeccion
        pantalla_menu = PantallaMenuLeccion(name='menu_leccion')
        self.sm.add_widget(pantalla_menu)

        # Visor Teórico de Unidades (La cura definitiva para tu error)
        pantalla_visor = PantallaVisorUnidad(name='escuela_visor')
        self.sm.add_widget(pantalla_visor)

        # Contenedor dedicado puramente a la ejecución táctica de las lecciones
        self.pantalla_leccion = Screen(name='pantalla_leccion')
        self.sm.add_widget(self.pantalla_leccion)

        # Forzamos la entrada inicial al menú principal
        self.sm.current = 'menu_principal'
        return self.sm

    def iniciar_juego(self, nombre_usuario):
        """
        Despliega el tablero de ajedrez y carga un desafío adaptado al usuario.

        Este método se dispara al seleccionar un perfil. Carga los datos del
        jugador, actualiza el registro del último usuario activo en disco[cite: 4]
        y solicita un puzle acorde a su ELO, descartando dinámicamente los que
        el jugador ya ha resuelto[cite: 5]. Finalmente, limpia y renderiza la vista.

        Args:
            nombre_usuario (str): El nombre del perfil seleccionado en la interfaz.
        """
        # Actualizamos la memoria para fijar el jugador activo[cite: 4]
        self.perfil_actual = self.gestor_perfiles.cargar_perfil(nombre_usuario)
        self.gestor_perfiles.guardar_perfil(self.perfil_actual)

        escala_actual = self.perfil_actual.get("escala_pop", 0)
        pop_min, pop_max = GestorProgresionPop.ESCALAS[escala_actual]

        puzzle = self.gestor_puzzles.obtener_puzzle_aleatorio(
            elo_objetivo=self.perfil_actual["elo"],
            ids_locales=set(self.perfil_actual["resueltos"]),
            pop_min=pop_min,
            pop_max=pop_max
        )

        if puzzle:
            self.gestor_ajedrez.cargar_puzzle(puzzle)

        self.pantalla_juego.clear_widgets()

        vista = VistaTablero(
            gestor_ajedrez=self.gestor_ajedrez,
            gestor_puzzles=self.gestor_puzzles,
            perfil_actual=self.perfil_actual,
            gestor_perfiles=self.gestor_perfiles
        )
        self.pantalla_juego.add_widget(vista)

        self.sm.current = 'juego'

        if puzzle:
            # Inyectamos la notación FEN y los movimientos en el motor central[cite: 1]
            self.gestor_ajedrez.cargar_puzzle(puzzle)

        # Limpiamos el lienzo por si volvimos del menú para evitar colapsos visuales o duplicidades
        self.pantalla_juego.clear_widgets()

        vista = VistaTablero(
            gestor_ajedrez=self.gestor_ajedrez,
            gestor_puzzles=self.gestor_puzzles,
            perfil_actual=self.perfil_actual,
            gestor_perfiles=self.gestor_perfiles
        )
        self.pantalla_juego.add_widget(vista)

        # Ordenamos a la traicionera máquina de estados de Kivy que cambie de pantalla
        self.sm.current = 'juego'

    # def solicitar_permisos_android() -> None:
    #     """
    #     Extorsiona al miserable sistema operativo Android para obtener acceso al disco.
    #
    #     Verifica si la plataforma de ejecución es el entorno móvil y lanza
    #     la petición de permisos de almacenamiento en tiempo de ejecución.
    #     """
    # 
    #     if platform == 'android':
    #         from android.permissions import request_permissions, Permission
    #         request_permissions([
    #             Permission.READ_EXTERNAL_STORAGE,
    #             Permission.WRITE_EXTERNAL_STORAGE
    #         ])

if __name__ == '__main__':
    ChessApp().run()