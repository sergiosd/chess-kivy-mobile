import os
import math
import chess
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, BooleanProperty
from kivy.app import App
from kivy.factory import Factory
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line, Triangle
from kivy.clock import Clock


class PantallaEscuelaUnidades(Screen):
    """
    Vista de detalle que despliega el temario interactivo y gestiona la lectura de archivos.

    Esta clase actúa como Controlador en el patrón MVC. Interroga el progreso del 
    usuario almacenado en disco y renderiza las filas visuales. Carga dinámicamente
    el contenido teórico leyendo archivos de texto del directorio 'lecciones'.
    """

    TEMARIO = {
        'tactica': [
            ('tac_01', 'Introduccion a la tactica'),
            ('tac_02', 'El ataque doble'),
            ('tac_03', 'La clavada absoluta'),
            ('tac_04', 'Descubiertas letales')
        ],
        'mates': [
            ('mat_01', 'Mate del pasillo'),
            ('mat_02', 'Beso de la muerte')
        ],
        'finales': [
            ('fin_01', 'Oposicion basica'),
            ('fin_02', 'Regla del cuadrado')
        ]
    }

    # Mapa para enlazar el identificador interno con el archivo físico real
    ARCHIVOS_LECCIONES = {
        'tac_01': 'tactica_contenido.txt'
    }

    def __init__(self, gestor_perfiles, **kwargs) -> None:
        """
        Prepara la pantalla inyectando la dependencia de acceso a disco duro.

        Args:
            gestor_perfiles (PerfilManager): Motor de persistencia en disco.
        """
        super().__init__(**kwargs)
        self.gestor_perfiles = gestor_perfiles
        self.tema_actual = ''

    def cargar_tema(self, id_tema: str) -> None:
        """
        Construye las filas gráficas iterando sobre la base de datos local.
        Aniquila prefijos innecesarios y formatea el título limpiamente.
        """
        self.tema_actual = id_tema

        nombres_temas = {
            'tactica': 'TACTICA',
            'mates': 'MATES IMPRESCINDIBLES',
            'finales': 'FINALES DE PEONES',
            'aperturas': 'APERTURAS BÁSICAS'
        }
        titulo_limpio = nombres_temas.get(id_tema, id_tema.upper())

        # Inyección directa del título puro
        self.ids.lbl_titulo_tema.text = f"[b]{titulo_limpio}[/b]"

        self.ids.grid_unidades.clear_widgets()

        perfil = self._obtener_perfil_activo()
        progreso_escuela = perfil.get('progreso_escuela', {})

        lecciones = self.TEMARIO.get(id_tema, [])
        for id_leccion, titulo in lecciones:
            estado_completado = progreso_escuela.get(id_leccion, False)
            fila = FilaUnidadEscuela(
                id_unidad=id_leccion,
                controlador=self,
                texto_unidad=titulo
            )
            fila.completada = estado_completado
            self.ids.grid_unidades.add_widget(fila)

    def registrar_progreso(self, id_unidad: str, estado: bool) -> None:
        """
        Modifica el diccionario del jugador en RAM y fuerza la escritura física.

        Args:
            id_unidad (str): El identificador de la lección modificada.
            estado (bool): El nuevo valor booleano de la casilla.
        """
        perfil = self._obtener_perfil_activo()

        if 'progreso_escuela' not in perfil:
            perfil['progreso_escuela'] = {}

        perfil['progreso_escuela'][id_unidad] = estado
        self.gestor_perfiles.guardar_perfil(perfil)

    def _obtener_perfil_activo(self) -> dict:
        """
        Extrae el diccionario de estado del jugador activo en sesión.

        Returns:
            dict: Estructura de datos del perfil recuperada del gestor.
        """
        nombre = self.gestor_perfiles.obtener_ultimo_usuario()
        return self.gestor_perfiles.cargar_perfil(nombre)

    def volver_temas(self) -> None:
        """Retorna a la pantalla de selección de categorías principales."""
        App.get_running_app().sm.current = 'escuela_temas'

    def abrir_visor(self, id_leccion: str, titulo: str) -> None:
        """
        Localiza el archivo de texto asociado a la unidad y lo inyecta en el visor teórico.

        Si el archivo no existe en el sistema de directorios inyecta un texto de error por defecto.

        Args:
            id_leccion (str): Código interno de la lección.
            titulo (str): Texto amigable que se mostrará en la cabecera de la interfaz.
        """
        app = App.get_running_app()
        pantalla_visor = app.sm.get_screen('escuela_visor')

        nombre_archivo = self.ARCHIVOS_LECCIONES.get(id_leccion, f"{id_leccion}_contenido.txt")
        ruta_archivo = os.path.join('lecciones', nombre_archivo)

        texto = "Este papiro digital aún se está forjando. Vuelve más tarde."

        if os.path.exists(ruta_archivo):
            with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                texto = archivo.read()

        # Inyección brutal del ID para que el visor sepa exactamente qué lección está manipulando
        pantalla_visor.cargar_contenido(id_leccion, titulo, texto)
        app.sm.current = 'escuela_visor'

    def siguiente_unidad(self) -> None:
        """
        Escanea implacablemente el progreso del usuario.

        Abre el visor teórico de la primera lección del tema actual que mantenga
        su casilla desmarcada. Si todas están completadas, abre la primera unidad
        del bloque.
        """
        perfil = self._obtener_perfil_activo()
        progreso = perfil.get('progreso_escuela', {})
        lecciones = self.TEMARIO.get(self.tema_actual, [])

        for id_leccion, titulo in lecciones:
            if not progreso.get(id_leccion, False):
                self.abrir_visor(id_leccion, titulo)
                return

        if lecciones:
            self.abrir_visor(lecciones[0][0], lecciones[0][1])


class FilaUnidadEscuela(ButtonBehavior, BoxLayout):
    """
    Componente visual interactivo que representa una lección del temario.

    Hereda de ButtonBehavior para permitir que toda la fila sea pulsable,
    orquestando la apertura del contenido teórico sin depender del checkbox.
    """
    texto_unidad = StringProperty('')
    completada = BooleanProperty(False)

    def __init__(self, id_unidad: str, controlador, **kwargs) -> None:
        """
        Inicializa la fila inyectando su identificador y el gestor superior.
        """
        super().__init__(**kwargs)
        self.id_unidad = id_unidad
        self.controlador = controlador

    def al_alternar(self, estado: bool) -> None:
        """Intercepta el toque sobre la casilla booleana."""
        self.controlador.registrar_progreso(self.id_unidad, estado)

    def on_release(self) -> None:
        """
        Dispara la transición de pantalla al tocar cualquier parte de la fila.
        """
        self.controlador.abrir_visor(self.id_unidad, self.texto_unidad)


class PantallaEscuelaTemas(Screen):
    """
    Controlador gráfico principal para seleccionar bloques de estudio masivos.

    Orquesta la inyección dinámica de los temas en un único panel visual,
    calculando en tiempo real el porcentaje de avance del usuario activo
    mediante la lectura de su perfil en disco.
    """

    def on_pre_enter(self, *args) -> None:
        """
        Intercepta el ciclo de vida de Kivy antes de pintar la pantalla en el canvas.
        Fuerza la actualización de métricas del jugador.
        """
        self.poblar_temas()

    def poblar_temas(self) -> None:
        """
        Construye la lista de temas dentro del panel único calculando los progresos.
        """
        self.ids.grid_temas.clear_widgets()
        app = App.get_running_app()

        # Recuperación del progreso del usuario activo
        nombre_usuario = app.gestor_perfiles.obtener_ultimo_usuario()
        perfil = app.gestor_perfiles.cargar_perfil(nombre_usuario) if nombre_usuario else {}
        progreso_usuario = perfil.get('progreso_escuela', {})

        # Obtenemos el temario definido en la pantalla de unidades
        pantalla_unidades = app.sm.get_screen('escuela_unidades')
        temario = pantalla_unidades.TEMARIO

        # Mapeo de identificadores a títulos legibles con tildes UTF-8
        nombres_temas = {
            'tactica': 'Táctica',
            'mates': 'Mates Imprescindibles',
            'finales': 'Finales de Peones',
            'aperturas': 'Aperturas Básicas'
        }

        # Generamos dinámicamente cada fila interactiva dentro del panel único
        for id_tema, titulo in nombres_temas.items():
            lecciones = temario.get(id_tema, [])
            total = len(lecciones)

            completadas = sum(
                1 for id_leccion, _ in lecciones
                if progreso_usuario.get(id_leccion, False)
            )

            porcentaje = int((completadas / total * 100)) if total > 0 else 0

            fila = Factory.FilaTemaProgreso()
            fila.texto_tema = titulo
            fila.porcentaje = porcentaje
            fila.id_tema = id_tema
            fila.controlador = self

            self.ids.grid_temas.add_widget(fila)

    def abrir_tema(self, id_tema: str) -> None:
        """
        Configura y despliega la pantalla de unidades del bloque didáctico.

        Args:
            id_tema (str): Identificador interno del bloque temático.
        """
        app = App.get_running_app()
        pantalla_unidades = app.sm.get_screen('escuela_unidades')
        pantalla_unidades.cargar_tema(id_tema)
        app.sm.current = 'escuela_unidades'

    def volver_menu(self) -> None:
        """
        Retorna a la pantalla del menú de prácticas de la aplicación.
        """
        App.get_running_app().sm.current = 'practica'

    def abrir_tema(self, id_tema: str) -> None:
        """
        Configura la pantalla hija de unidades con el contenido del bloque seleccionado.

        Args:
            id_tema (str): El identificador interno del bloque de lecciones.
        """
        app = App.get_running_app()
        pantalla_unidades = app.sm.get_screen('escuela_unidades')
        pantalla_unidades.cargar_tema(id_tema)
        app.sm.current = 'escuela_unidades'

    def volver_menu(self) -> None:
        """
        Abandona el entorno educativo retornando al menú general de la aplicación.
        """
        App.get_running_app().sm.current = 'menu_principal'


class CasillaMini(RelativeLayout):
    """
    Componente visual microscópico, inerte y estúpido para ilustrar tácticas.

    Carece de comportamiento interactivo. Se limita a renderizar el fondo del
    escaque y la textura de la pieza inyectada por el controlador.
    """

    def __init__(self, es_clara: bool, ruta_pieza: str, **kwargs) -> None:
        """
        Ensambla el escaque visual inyectando las texturas directamente al Canvas.
        """
        super().__init__(**kwargs)
        ruta_fondo = "assets/squares/casilla_clara.png" if es_clara else "assets/squares/casilla_oscura.png"

        self.add_widget(Image(source=ruta_fondo, allow_stretch=True, keep_ratio=False))
        if ruta_pieza:
            self.add_widget(Image(source=ruta_pieza, fit_mode='contain', size_hint=(0.85, 0.85),
                                  pos_hint={'center_x': 0.5, 'center_y': 0.5}))


class PantallaVisorUnidad(Screen):
    """
    Controlador maestro de la lectura de lecciones tácticas.

    Aniquila el texto en bruto, lo convierte en estados paginados independientes
    y orquesta la interfaz gráfica para inyectar minitableros dinámicos.
    """

    def __init__(self, **kwargs):
        """
        Inicializa las variables de estado en memoria RAM.

        Args:
            **kwargs: Metadatos requeridos por la espantosa arquitectura de Kivy.
        """
        super().__init__(**kwargs)
        self.id_leccion_actual = ""
        self.paginas = []
        self.indice_pagina = 0

    def cargar_contenido(self, id_leccion: str, titulo: str, texto: str) -> None:
        """
        Aniquila el texto crudo y construye la lista de páginas lógicas.

        Usa el delimitador [PAGINA] para estructurar la lectura de forma independiente
        al contenido táctico.

        Args:
            id_leccion (str): Identificador único para registrar progreso.
            titulo (str): Encabezado de la lección.
            texto (str): Contenido completo cargado desde el disco.
        """
        self.id_leccion_actual = id_leccion
        self.ids.lbl_titulo.text = f"[b]{titulo.upper()}[/b]"
        self.paginas = []
        self.indice_pagina = 0

        partes_pagina = texto.split('[PAGINA]')

        for bloque in partes_pagina:
            if bloque.strip():
                self.paginas.append(bloque.strip())

        self.mostrar_pagina()

    def mostrar_pagina(self) -> None:
        """
        Limpia el lienzo e inyecta el contenido exclusivo de la página actual.

        Analiza el texto activo buscando etiquetas FEN para intercalar
        dinámicamente los minitableros y el texto.
        """
        if not self.paginas:
            return

        contenedor = self.ids.contenedor_contenido
        contenedor.clear_widgets()

        texto_pagina = self.paginas[self.indice_pagina]
        partes = texto_pagina.split('[FEN:')

        for i, bloque in enumerate(partes):
            if i == 0:
                if bloque.strip():
                    self._agregar_texto(contenedor, bloque.strip())
            else:
                subpartes = bloque.split(']', 1)
                if len(subpartes) == 2:
                    codigo_fen = subpartes[0].strip()
                    resto_texto = subpartes[1].strip()

                    self._agregar_minitablero(contenedor, codigo_fen)

                    if resto_texto.strip():
                        self._agregar_texto(contenedor, resto_texto.strip())

        if self.indice_pagina == len(self.paginas) - 1 and self.id_leccion_actual:
            app = App.get_running_app()
            pantalla_unidades = app.sm.get_screen('escuela_unidades')
            pantalla_unidades.registrar_progreso(self.id_leccion_actual, True)

    def pagina_anterior(self) -> None:
        """Resta el contador de página y redibuja la vista gráfica."""
        if self.indice_pagina > 0:
            self.indice_pagina -= 1
            self.mostrar_pagina()

    def pagina_siguiente(self) -> None:
        """
        Avanza devorando el conocimiento teórico.
        Si ya está en la última página, ignora la pulsación.
        """
        if self.indice_pagina < len(self.paginas) - 1:
            self.indice_pagina += 1
            self.mostrar_pagina()

    def volver_unidades(self) -> None:
        """Ejecuta una retirada estratégica hacia el menú de unidades."""
        App.get_running_app().sm.current = 'escuela_unidades'

    def _agregar_texto(self, contenedor, texto: str) -> None:
        """
        Instancia una etiqueta de texto y la pega en el contenedor padre.

        Args:
            contenedor: Widget de Kivy contenedor.
            texto (str): Teoría de ajedrez.
        """
        etiqueta = Factory.TextoLeccion()
        etiqueta.text = texto
        contenedor.add_widget(etiqueta)

    def _agregar_minitablero(self, contenedor, bloque_datos: str) -> None:
        """
        Invoca la construcción del tablero, procesando el código FEN y dibujando vectores dinámicos.

        Trocea la etiqueta inyectada buscando los delimitadores '|'. Interpreta los
        comandos 'C:' para colorear escaques y 'A:' para disparar flechas. Ataca
        directamente al Canvas post-renderizado (after) de Kivy, vinculando la
        geometría a los eventos de redimensionamiento para evitar desajustes asquerosos.

        Args:
            contenedor (BoxLayout): El padre gráfico que devorará el minitablero.
            bloque_datos (str): El contenido crudo extraído del archivo de teoría.
        """
        mapa_imagenes = {
            'P': 'assets/pieces/blanco_peon.png', 'p': 'assets/pieces/negro_peon.png',
            'N': 'assets/pieces/blanco_caballo.png', 'n': 'assets/pieces/negro_caballo.png',
            'B': 'assets/pieces/blanco_alfil.png', 'b': 'assets/pieces/negro_alfil.png',
            'R': 'assets/pieces/blanco_torre.png', 'r': 'assets/pieces/negro_torre.png',
            'Q': 'assets/pieces/blanco_reina.png', 'q': 'assets/pieces/negro_reina.png',
            'K': 'assets/pieces/blanco_rey.png', 'k': 'assets/pieces/negro_rey.png'
        }

        # 1. El bisturí del parser extrae el FEN puro y los comandos extra
        tramos = bloque_datos.split('|')
        fen_real = tramos[0].strip()

        colores_casillas = []
        flechas_vectores = []

        # Paletas RGBA (Verde táctico y Rojo hemorragia)
        mapa_resaltes = {'g': (0.2, 0.8, 0.2, 0.5), 'r': (0.8, 0.2, 0.2, 0.5)}
        mapa_lineas = {'g': (0.2, 0.8, 0.2, 0.85), 'r': (0.8, 0.2, 0.2, 0.85)}

        # 2. Descuartizamos los argumentos extra
        for tramo in tramos[1:]:
            tramo = tramo.strip()
            if tramo.startswith('C:'):
                datos = tramo[2:].split(',')
                for d in datos:
                    if '-' in d:
                        cas, c = d.strip().split('-')
                        colores_casillas.append((cas.strip(), mapa_resaltes.get(c.strip().lower(),
                                                                                (0.2, 0.8, 0.2,
                                                                                 0.5))))
            elif tramo.startswith('A:'):
                datos = tramo[2:].split(',')
                for d in datos:
                    if '-' in d:
                        mov, c = d.strip().split('-')
                        mov = mov.strip()
                        if len(mov) >= 4:
                            flechas_vectores.append((mov[:2], mov[2:4],
                                                     mapa_lineas.get(c.strip().lower(),
                                                                     (0.2, 0.8, 0.2, 0.85))))

        envoltorio = Factory.ContenedorTableroMini()
        cuadricula = envoltorio.ids.grid

        # 3. Ensamblaje del tablero estático subyacente
        try:
            tablero = chess.Board(fen_real)
            for fila in range(7, -1, -1):
                for col in range(8):
                    es_clara = (fila + col) % 2 != 0
                    pieza = tablero.piece_at(chess.square(col, fila))
                    ruta_pieza = mapa_imagenes.get(pieza.symbol(), '') if pieza else ''
                    cuadricula.add_widget(CasillaMini(es_clara, ruta_pieza))

            contenedor.add_widget(envoltorio)
        except ValueError:
            self._agregar_texto(contenedor,
                                f"[color=#ff0000]ERROR: FEN inválido o corrupto ({fen_real})[/color]")
            return

        # 4. Inyección de la brujería geométrica en el Canvas
        def redibujar_anotaciones(instancia, valor) -> None:
            """Callback forzado que recalcula los píxeles absolutos cuando Kivy respira."""
            instancia.canvas.after.clear()
            with instancia.canvas.after:
                sq_w = instancia.width / 8.0
                sq_h = instancia.height / 8.0

                # Pintando los mosaicos
                for cas, col_rgba in colores_casillas:
                    idx = chess.parse_square(cas)
                    f = chess.square_file(idx)
                    r = chess.square_rank(idx)
                    Color(*col_rgba)
                    Rectangle(pos=(instancia.x + f * sq_w, instancia.y + r * sq_h),
                              size=(sq_w, sq_h))

                # Trazando la balística de las flechas
                for origen, destino, col_rgba in flechas_vectores:
                    idx_o = chess.parse_square(origen)
                    idx_d = chess.parse_square(destino)

                    x1 = instancia.x + (chess.square_file(idx_o) + 0.5) * sq_w
                    y1 = instancia.y + (chess.square_rank(idx_o) + 0.5) * sq_h
                    x2 = instancia.x + (chess.square_file(idx_d) + 0.5) * sq_w
                    y2 = instancia.y + (chess.square_rank(idx_d) + 0.5) * sq_h

                    Color(*col_rgba)
                    Line(points=[x1, y1, x2, y2], width=dp(3))

                    # Forjando la mortífera punta del vector
                    angulo = math.atan2(y2 - y1, x2 - x1)
                    l_punta = dp(14)
                    p1 = (x2, y2)
                    p2 = (x2 - l_punta * math.cos(angulo - math.pi / 6.0),
                          y2 - l_punta * math.sin(angulo - math.pi / 6.0))
                    p3 = (x2 - l_punta * math.cos(angulo + math.pi / 6.0),
                          y2 - l_punta * math.sin(angulo + math.pi / 6.0))
                    Triangle(points=[p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]])

        # 5. Atamos el callback a las entrañas inestables del diseño de Kivy
        cuadricula.bind(pos=redibujar_anotaciones, size=redibujar_anotaciones)
        Clock.schedule_once(lambda dt: redibujar_anotaciones(cuadricula, None), 0.1)

    def volver_unidades(self) -> None:
        """Abandona la clase magistral y huye hacia el índice de unidades."""
        App.get_running_app().sm.current = 'escuela_unidades'