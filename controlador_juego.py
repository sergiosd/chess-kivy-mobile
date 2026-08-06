# controlador_juego.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
import chess


class CasillaTablero(ButtonBehavior, FloatLayout):
    """
    Representa un componente visual interactivo para cada escaque del tablero.

    Esta clase es un componente visual purgado de las inestables Properties
    de Kivy, diseñado para interceptar los toques del usuario en la pantalla
    y delegarlos al controlador lógico superior[cite: 2].
    """

    def __init__(self, nombre_casilla, controlador, **kwargs):
        """
        Inicializa una instancia de la casilla del tablero.

        Args:
            nombre_casilla (str): Identificador alfanumérico estándar de la casilla,
                                  como por ejemplo 'e2' o 'd4'[cite: 2].
            controlador (ControladorTablero): Referencia al gestor visual principal
                                              que maneja el estado de la interfaz y
                                              los eventos globales del tablero[cite: 2].
            **kwargs: Argumentos adicionales absorbidos por la clase base de Kivy[cite: 2].
        """
        super().__init__(**kwargs)
        self.nombre_casilla = nombre_casilla
        self.controlador = controlador

    def on_press(self):
        """
        Captura el evento de pulsación física sobre el widget.

        En lugar de gestionar lógica localmente, delega inmediatamente la
        responsabilidad notificando al controlador principal qué casilla
        específica ha sido tocada[cite: 2].
        """
        self.controlador.al_tocar_casilla(self.nombre_casilla)


class ControladorTablero(BoxLayout):
    """
    Gestor visual principal del tablero de ajedrez.

    Orquesta la renderización de las casillas, la actualización de las texturas
    de las piezas y actúa como puente de comunicación (Vista) entre las acciones
    del usuario y el motor lógico puro (ChessManager)[cite: 2].
    """

    def __init__(self, gestor_ajedrez, **kwargs):
        """
        Inicializa el controlador visual y prepara los recursos gráficos.

        Configura el diccionario de referencias de casillas e inicializa el mapa
        de imágenes que enlaza la notación FEN con las rutas de los archivos PNG
        de cada pieza, desde peones hasta reyes, tanto blancos como negros[cite: 2].

        Args:
            gestor_ajedrez (ChessManager): Instancia del modelo lógico que valida
                                           los movimientos y mantiene el estado
                                           del puzzle[cite: 2].
            **kwargs: Argumentos adicionales del BoxLayout de Kivy[cite: 2].
        """
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
        """
        Genera y posiciona dinámicamente las 64 casillas en la interfaz gráfica.

        Limpia la cuadrícula actual y la rellena iterando desde la fila 7 hasta
        la 0, y por las 8 columnas[cite: 2]. Determina el color de fondo
        (claro u oscuro) basándose en la paridad de la suma de la fila y columna[cite: 2].
        Inyecta la ruta de la textura directamente, saltándose la burocracia
        de las variables de Kivy para evitar sobrecargas[cite: 2].
        """
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
        """
        Almacena la referencia de un widget de casilla en la memoria del controlador.

        Args:
            nombre_casilla (str): Nombre coordenado de la casilla (ej: 'a1')[cite: 2].
            widget_casilla (CasillaTablero): Instancia del widget visual correspondiente[cite: 2].
        """
        self.diccionario_casillas[nombre_casilla] = widget_casilla

    def actualizar_piezas_visuales(self):
        """
        Sincroniza el estado visual del tablero con el estado lógico subyacente.

        Itera sobre todas las casillas registradas, consulta al tablero lógico
        qué pieza reside en cada índice y actualiza la fuente de la imagen
        correspondiente consultando el mapa de imágenes[cite: 2]. Además,
        actualiza la etiqueta de información con el nivel ELO del puzzle actual
        si está disponible[cite: 2].
        """
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
        """
        Procesa el flujo lógico principal cuando el usuario interactúa con una casilla.

        Si ya hay una pieza seleccionada y el destino es uno de los movimientos
        válidos, intenta ejecutar el movimiento[cite: 2]. Limpia las iluminaciones,
        actualiza las piezas y evalúa el resultado: si es victoria, actualiza
        la etiqueta de estado en color verde; si es correcto pero no ha terminado,
        programa la respuesta de la IA; si falla, muestra un mensaje de error en rojo[cite: 2].
        Si no había casilla previa seleccionada, la selecciona y muestra las opciones[cite: 2].

        Args:
            nombre_casilla (str): La coordenada de la casilla interactuada[cite: 2].
        """
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
        """
        Ejecuta y renderiza el movimiento del rival automatizado (IA).

        Llama al gestor lógico para obtener el siguiente movimiento de la solución
        y, de ejecutarse, sincroniza los widgets[cite: 2]. Tras el movimiento,
        evalúa si el puzzle ha concluido en victoria (marcando texto en verde)
        o si le devuelve el turno al jugador[cite: 2].

        Args:
            dt (float): Delta time. Argumento requerido por Clock.schedule_once
                        de Kivy, representa el tiempo transcurrido[cite: 2].
        """
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
        """
        Aplica un filtro de color sobre las casillas clave para guiar al usuario.

        Tiñe la casilla de origen seleccionada de color amarillo, y colorea
        de verde todas las casillas que representen un destino legal para la
        pieza activa, basándose en la lista de movimientos válidos del gestor[cite: 2].
        """
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
        """
        Restaura el color original por defecto de todas las casillas del tablero.

        Itera a través de todos los widgets registrados en el diccionario y
        restablece el multiplicador de color a blanco puro (RGBA: 1, 1, 1, 1)[cite: 2].
        """
        for widget in self.diccionario_casillas.values():
            widget.ids.img_fondo.color = [1, 1, 1, 1]