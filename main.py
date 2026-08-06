"""
Módulo principal de la aplicación Kivy para Mind Chess.

Este archivo actúa como el núcleo de la Vista en el patrón MVC, orquestando
la interfaz gráfica, las animaciones asíncronas de Kivy, el motor de audio y
la interacción directa con los controladores lógicos (ajedrez, perfiles y puzles)[cite: 3].
"""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.properties import BooleanProperty, StringProperty
from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.graphics import Color, Line, Triangle
from kivy.metrics import dp
import chess
import math

# Importación de nuestros robustos módulos lógicos[cite: 3]
from chess_manager import ChessManager
from puzzle_manager import PuzzleManager
from perfil_manager import PerfilManager

# Fijamos el tamaño de la ventana simulando un dispositivo móvil[cite: 3]
Window.size = (450, 800)

# Diseño KV purgado y estructurado sin errores de indentación en el parser[cite: 3]
Builder.load_string("""
<Casilla>:
    ruta_fondo: ''
    ruta_pieza: ''
    origen_seleccionado: False
    destino_valido: False
    texto_fila: ''
    texto_col: ''

    canvas.before:
        Color:
            rgba: (1, 1, 1, 1)
        Rectangle:
            pos: 0, 0
            size: self.size
            source: root.ruta_fondo
        Color:
            rgba: (1, 1, 0, 0.4) if root.origen_seleccionado else (0, 0, 0, 0)
        Rectangle:
            pos: 0, 0
            size: self.size

    canvas.after:
        Color:
            rgba: (0, 0.7, 0, 0.8) if root.destino_valido else (0, 0, 0, 0)
        Ellipse:
            size: self.width / 4, self.height / 4
            pos: self.center_x - self.width / 8, self.center_y - self.height / 8

    Image:
        source: root.ruta_pieza
        opacity: 1 if root.ruta_pieza else 0
        fit_mode: 'contain'
        size_hint: 0.85, 0.85
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}

    Label:
        text: root.texto_fila
        font_size: '12sp'
        bold: True
        color: 0.1, 0.1, 0.1, 0.8
        size_hint: None, None
        size: self.texture_size
        pos_hint: {'x': 0.05, 'top': 0.95}

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
            text: 'VOLVER AL MENÚ'
            size_hint_y: None
            height: dp(45)
            background_color: 0.8, 0.4, 0.1, 1
            opacity: 0
            disabled: True
            on_press: root.volver_menu()
            
<PantallaSeleccion>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(30)
        spacing: dp(15)
        canvas.before:
            Color:
                rgba: 0.12, 0.29, 0.42, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        Label:
            text: '[b]MIND CHESS[/b]\\nSelecciona tu Perfil'
            markup: True
            halign: 'center'
            font_size: '28sp'
            color: 0.1, 0.8, 0.8, 1
            size_hint_y: 0.2
            
        ScrollView:
            size_hint_y: 0.4
            GridLayout:
                id: grid_perfiles
                cols: 1
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height
                
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.4
            spacing: dp(10)
            
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: dp(45)
                spacing: dp(10)
                
                TextInput:
                    id: input_nuevo
                    hint_text: 'Nuevo usuario...'
                    multiline: False
                    font_size: '18sp'
                    
                TextInput:
                    id: input_elo
                    hint_text: 'ELO (Min 600)'
                    input_filter: 'int'
                    multiline: False
                    font_size: '18sp'
                    size_hint_x: 0.5
                
            Button:
                text: 'CREAR PERFIL NUEVO'
                size_hint_y: None
                height: dp(50)
                background_color: 0.8, 0.6, 0.1, 1
                bold: True
                on_press: root.crear_perfil()
                
            Button:
                text: 'SALIR DEL JUEGO'
                size_hint_y: None
                height: dp(50)
                background_color: 0.8, 0.2, 0.2, 1
                bold: True
                on_press: app.stop()
""")

from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.metrics import dp


class PantallaSeleccion(Screen):
    """
    Vista y controlador de la pantalla inicial de selección de usuarios.

    Hereda de la clase Screen de Kivy. Su rol en el patrón MVC es gestionar la
    creación de nuevos perfiles (incluyendo la validación de un ELO mínimo) y
    despachar el evento para iniciar el juego o cerrar la aplicación.
    """

    def __init__(self, gestor_perfiles, al_seleccionar, **kwargs):
        """
        Inicializa la pantalla de selección inyectando sus dependencias.

        Args:
            gestor_perfiles (PerfilManager): Referencia al modelo de persistencia de datos[cite: 4].
            al_seleccionar (callable): Función callback para iniciar el tablero.
            **kwargs: Argumentos para el inicializador de Kivy[cite: 3].
        """
        super().__init__(**kwargs)
        self.gestor_perfiles = gestor_perfiles
        self.al_seleccionar = al_seleccionar
        self.poblar_perfiles()

    def poblar_perfiles(self):
        """
        Genera los botones interactivos dinámicamente según los usuarios registrados.
        """
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
            btn.bind(on_press=lambda instance, nombre=u: self.al_seleccionar(nombre))
            self.ids.grid_perfiles.add_widget(btn)

    def crear_perfil(self):
        """
        Captura el nombre y el ELO para registrar un nuevo jugador.

        Valida que el ELO introducido sea un número válido y garantiza que
        sea igual o superior a 600 puntos. Tras configurar el diccionario,
        lo persiste en el almacenamiento local[cite: 4].
        """
        nombre = self.ids.input_nuevo.text.strip()
        texto_elo = self.ids.input_elo.text.strip()

        if nombre:
            try:
                elo_inicial = int(texto_elo)
            except ValueError:
                # Si el campo está vacío o el sádico usuario metió basura, fijamos el mínimo
                elo_inicial = 600

            # Forzamos matemáticamente el suelo de 600 puntos de ELO
            elo_inicial = max(600, elo_inicial)

            nuevo_perfil = self.gestor_perfiles.cargar_perfil(nombre)
            nuevo_perfil["elo"] = elo_inicial
            self.gestor_perfiles.guardar_perfil(nuevo_perfil)

            self.ids.input_nuevo.text = ''
            self.ids.input_elo.text = ''
            self.poblar_perfiles()

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
        nuevo_puzzle = self.gestor_puzzles.obtener_puzzle_aleatorio(1000, set())
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
            self.ids.lbl_mision.text = f"Puzzle ELO: {info.get('rating', '--')}"
            self.ids.lbl_info.text = f"Popularidad: {info.get('popularity', '--')}% | ID: {info.get('id', '--')}"

            es_blancas = tablero.turn == chess.WHITE
            color_turno = "[color=#ff6b6b]NEGRAS[/color]" if not es_blancas else "[color=#ffffff]BLANCAS[/color]"

            if self.gestor_ajedrez.estado_puzzle == "JUGANDO":
                self.ids.lbl_estado.text = f"Tu turno: {color_turno}"

    def al_tocar_casilla(self, nombre_casilla):
        """
        Procesa la lógica central cuando un usuario pulsa una coordenada táctil.

        Valida el origen y destino. Si el movimiento pertenece a la solución,
        lanza la animación de vuelo de la pieza y programa la respuesta enemiga[cite: 3].
        Si es un error, reproduce un sonido vergonzoso, dibuja la flecha roja
        y muestra la penalización simulada[cite: 3].

        Args:
            nombre_casilla (str): Casilla en notación algebraica (ej. 'c3')[cite: 3].
        """
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
                # Ocultamos la textura en la casilla destino original para evitar clonaciones visuales durante el vuelo[cite: 3]
                self.diccionario_casillas[nombre_casilla].ruta_pieza = ''

                def terminar_vuelo():
                    self.diccionario_casillas[nombre_casilla].ruta_pieza = self.mapa_imagenes.get(
                        simbolo, '')
                    if gestor.estado_puzzle == "VICTORIA":
                        if self.sonido_ganar: self.sonido_ganar.play()
                        self.ids.lbl_estado.text = "¡PUZZLE COMPLETADO!"
                        self.ids.lbl_estado.color = [0, 1, 0, 1]
                        self.ids.btn_volver.opacity = 1
                        self.ids.btn_volver.disabled = False
                        self.registrar_victoria()
                    else:
                        self.ids.lbl_estado.text = "¡Excelente! Responde la IA..."
                        self.ids.lbl_estado.color = [1, 1, 0, 1]
                        # Programamos el contraataque de la IA de forma asíncrona[cite: 3]
                        Clock.schedule_once(self.procesar_respuesta_ia, 0.4)

                self.animar_pieza(origen, nombre_casilla, simbolo, terminar_vuelo)
            else:
                self.actualizar_piezas_visuales()
                if self.sonido_perder: self.sonido_perder.play()

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
            # Si tocamos por primera vez, seleccionamos e iluminamos las rutas[cite: 3]
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
        de movimiento antes de pintar la textura real en la matriz[cite: 3].

        Args:
            dt (float): Tiempo delta inyectado por el sagrado pero temperamental
                        Clock.schedule de Kivy[cite: 3].
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
                    self.ids.lbl_estado.text = "¡PUZZLE COMPLETADO!"
                    self.ids.lbl_estado.color = [0, 1, 0, 1]
                    self.ids.btn_volver.opacity = 1
                    self.ids.btn_volver.disabled = False
                    self.registrar_victoria()
                else:
                    self.ids.lbl_estado.text = "¡Tu turno! Continúa."
                    self.ids.lbl_estado.color = [0.9, 0.9, 0.9, 1]

            self.animar_pieza(origen, destino, simbolo, terminar_animacion_ia)

    def finalizar_turno_ia(self):
        """Alternativa bloqueante para restaurar las piezas (sin animación fantasma)[cite: 3]."""
        self.actualizar_piezas_visuales()
        if self.sonido_mover: self.sonido_mover.play()

        if self.gestor_ajedrez.estado_puzzle == "VICTORIA":
            self.ids.lbl_estado.text = "¡PUZZLE COMPLETADO!"
            self.ids.lbl_estado.color = [0, 1, 0, 1]
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

    def registrar_victoria(self):
        """
        Registra el ID del puzzle resuelto en el perfil del jugador.

        Este método protege el historial, asegurando que un mismo táctico
        no se duplique en la lista de 'resueltos' y ordenando al gestor
        que consolide la nueva información en el disco duro JSON[cite: 3, 4].
        """
        info = self.gestor_ajedrez.info_puzzle
        if info:
            id_puzzle = info.get("id")
            if id_puzzle and id_puzzle not in self.perfil_actual["resueltos"]:
                self.perfil_actual["resueltos"].append(id_puzzle)
                self.gestor_perfiles.guardar_perfil(self.perfil_actual)

    def volver_menu(self):
        """
        Abandona el tablero y retrocede elegantemente al menú de selección de perfiles.
        """
        App.get_running_app().sm.current = 'seleccion'


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

        # Instanciamos el gestor gráfico
        self.sm = ScreenManager()

        pantalla_seleccion = PantallaSeleccion(
            gestor_perfiles=self.gestor_perfiles,
            al_seleccionar=self.iniciar_juego,
            name='seleccion'
        )
        self.sm.add_widget(pantalla_seleccion)

        self.pantalla_juego = Screen(name='juego')
        self.sm.add_widget(self.pantalla_juego)

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

        # Buscamos tácticas basándonos en su puntuación e ignorando las que ya completó[cite: 5]
        puzzle = self.gestor_puzzles.obtener_puzzle_aleatorio(
            self.perfil_actual["elo"],
            set(self.perfil_actual["resueltos"])
        )
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