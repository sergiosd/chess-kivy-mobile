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


from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.properties import BooleanProperty, StringProperty, ListProperty
from kivy.animation import Animation
from kivy.graphics import Color, Line, Triangle
from kivy.metrics import dp
import chess
import math
from typing import Callable
import os

# Importación de nuestros robustos módulos lógicos[cite: 3]
from chess_manager import ChessManager
from puzzle_manager import PuzzleManager, GestorProgresionPop
from perfil_manager import PerfilManager, PantallaMenuPrincipal
from utilidades import CalculadorElo


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
    'advancedPawn': 'Peón avanzado', 'passedPawn': 'Peón pasado',
    'attraction': 'Atracción', 'clearance': 'Despeje', 'deflection': 'Desviación',
    'zugzwang': 'Zugzwang', 'quietMove': 'Jugada tranquila',
    'hangingPiece': 'Pieza colgada', 'trappedPiece': 'Pieza atrapada',
    'xRayAttack': 'Rayos X', 'capturingDefender': 'Captura del defensor',
    'promotion': 'Coronación', 'interference': 'Interferencia',
    'doubleCheck': 'Jaque doble', 'enPassant': 'Al paso',
    'castling': 'Enroque'
}
# Fijamos el tamaño de la ventana simulando un dispositivo móvil[cite: 3]
Window.size = (450, 800)

# Diseño KV purgado y estructurado sin errores de indentación en el parser[cite: 3]
Builder.load_file('interfaz.kv')

from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.metrics import dp


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
            btn = Button(
                text=f"Jugar como {u}",
                size_hint_y=None,
                height=dp(55),
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

    def __init__(self, gestor_ajedrez, gestor_puzzles, perfil_actual, gestor_perfiles, **kwargs):
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

        # Cargamos los molestos pero necesarios efectos de sonido en la RAM[cite: 3]
        self.sonido_seleccionar = SoundLoader.load('assets/sounds/select.wav')
        self.sonido_mover = SoundLoader.load('assets/sounds/move.wav')
        self.sonido_ganar = SoundLoader.load('assets/sounds/win.wav')
        self.sonido_perder = SoundLoader.load('assets/sounds/lose.wav')

        # Mapa de sprites para asociar la notación FEN con nuestros PNGs[cite: 3]
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
            self.ids.btn_volver.opacity = 0
            self.ids.btn_volver.disabled = True

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
            self.ids.lbl_info.text = f"Popularidad: {info.get('popularity', '--')}% | ID: {info.get('id', '--')}"

            es_blancas = tablero.turn == chess.WHITE
            color_turno = "[color=#ff6b6b]NEGRAS[/color]" if not es_blancas else "[color=#ffffff]BLANCAS[/color]"

            if self.gestor_ajedrez.estado_puzzle == "JUGANDO":
                self.ids.lbl_estado.text = f"Tu turno: {color_turno}"

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
                        self.ids.lbl_estado.text = f"¡CORRECTO!, nuevo ELO = {nuevo_elo} (+{variacion})"
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
                self.ids.lbl_estado.text = f"¡INCORRECTO! nuevo ELO = {nuevo_elo} ({variacion})"
                self.ids.lbl_estado.color = [1, 0.4, 0.4, 1]

                # Dibujamos vectores indicando la jugada que debió hacerse[cite: 3]
                mov_erroneo = gestor.movimiento_fallado
                if mov_erroneo:
                    self.mostrar_flecha_error(mov_erroneo)

                info = gestor.info_puzzle
                if info:
                    # Inyectamos el conocimiento traducido en la derrota (¡Respetado!)
                    self.mostrar_temas_traducidos()
                    self.ids.lbl_info.text = f"Nivel: {info.get('rating')} ELO"

                self.ids.btn_siguiente.text = "Siguiente Misión"
                self.ids.btn_volver.opacity = 1
                self.ids.btn_volver.disabled = False
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

    def procesar_respuesta_ia(self, dt):
        """
        Ejecuta el paso de la táctica correspondiente a la máquina enemiga.

        Programa la animación fantasma del rival para crear la ilusión óptica
        de movimiento antes de pintar la textura real en la matriz. Si el puzle
        concluye victoriosamente tras el forzado movimiento de la IA, revela los temas.

        Args:
            dt (float): Tiempo delta inyectado por el sagrado pero temperamental
                        Clock.schedule de Kivy.
        """
        mov = self.gestor_ajedrez.ejecutar_movimiento_enemigo()
        if mov:
            origen = mov[:2]
            destino = mov[2:4]

            indice_destino = chess.parse_square(destino)
            pieza = self.gestor_ajedrez.board.piece_at(indice_destino)
            simbolo = pieza.symbol() if pieza else ''

            self.diccionario_casillas[origen].ruta_pieza = ''

            def terminar_animacion_ia():
                self.actualizar_piezas_visuales()
                if self.sonido_mover: self.sonido_mover.play()

                if self.gestor_ajedrez.estado_puzzle == "VICTORIA":
                    variacion, nuevo_elo = self.registrar_resultado_puzzle(True)
                    self.ids.lbl_estado.text = f"¡CORRECTO! Elo sube +{variacion}, nuevo ELO = {nuevo_elo}"
                    self.ids.lbl_estado.color = [0, 1, 0, 1]

                    # Desplegamos los temas si la táctica finaliza con el enemigo
                    self.mostrar_temas_traducidos()

                    self.ids.btn_volver.opacity = 1
                    self.ids.btn_volver.disabled = False
                else:
                    self.ids.lbl_estado.text = "¡Tu turno! Continúa."
                    self.ids.lbl_estado.color = [0.9, 0.9, 0.9, 1]

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
            self.ids.lbl_estado.text = "¡Tu turno! Continúa."
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
        Abandona el tablero y retrocede elegantemente al menú de selección de perfiles.
        """
        App.get_running_app().sm.current = 'seleccion'

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
    Vista y controlador del panel de preferencias del usuario.
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
        self.gestor_perfiles = PerfilManager()
        self.gestor_ajedrez = ChessManager()
        self.gestor_puzzles = PuzzleManager()

        self.sm = ScreenManager()

        # Tu gloriosa pantalla principal diseñada a medida
        pantalla_menu = PantallaMenuPrincipal(
            gestor_perfiles=self.gestor_perfiles,
            name='menu_principal'
        )
        self.sm.add_widget(pantalla_menu)

        # La pantalla de selección reciclada y purgada
        pantalla_cambiar = PantallaCambiarUsuario(
            gestor_perfiles=self.gestor_perfiles,
            al_seleccionar=self.iniciar_juego,
            name='cambiar_usuario'
        )
        self.sm.add_widget(pantalla_cambiar)

        self.pantalla_juego = Screen(name='juego')
        self.sm.add_widget(self.pantalla_juego)

        pantalla_gestion = PantallaGestionUsuarios(
            gestor_perfiles=self.gestor_perfiles,
            name='gestion_usuarios'
        )
        self.sm.add_widget(pantalla_gestion)

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


if __name__ == '__main__':
    ChessApp().run()