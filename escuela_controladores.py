import os
import math
import chess
import json
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import StringProperty, BooleanProperty
from kivy.app import App
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line, Triangle
from kivy.clock import Clock

from utilidades import compilar_markdown_a_kivy



class PantallaEscuelaUnidades(Screen):
    """
    Vista de detalle que despliega el temario interactivo y gestiona la lectura de archivos.

    Esta clase actúa como Controlador en el patrón MVC. Interroga el progreso del 
    usuario almacenado en disco y renderiza las filas visuales. Carga dinámicamente
    el contenido teórico leyendo archivos de texto del directorio 'lecciones'.
    """

    def __init__(self, gestor_perfiles, **kwargs) -> None:
        """
        Prepara la pantalla inyectando la dependencia de acceso a disco duro.

        Args:
            gestor_perfiles (PerfilManager): Motor de persistencia en disco.
        """
        super().__init__(**kwargs)
        self.gestor_perfiles = gestor_perfiles
        self.tema_actual = ''
        self.TEMARIO = {}
        self.ARCHIVOS_LECCIONES = {}
        self.cargar_datos_json()

    def cargar_datos_json(self) -> None:
        """
        Inyecta el diccionario en memoria devorando el archivo JSON local.
        """
        ruta = os.path.join('lecciones', 'temario.json')
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                try:
                    datos = json.load(f)
                    self.TEMARIO = datos.get('temario', {})
                    self.ARCHIVOS_LECCIONES = datos.get('archivos', {})
                except json.JSONDecodeError:
                    print("ERROR: ¡Por el kernel panic! El JSON está corrupto.")
        else:
            print("ERROR: Archivo temario.json no encontrado en la raíz.")

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
        Localiza el archivo teórico anidado en el diccionario y lo inyecta en el visor.

        Args:
            id_leccion (str): Código interno de la lección.
            titulo (str): Texto amigable de la cabecera.
        """
        app = App.get_running_app()
        pantalla_visor = app.sm.get_screen('escuela_visor')

        datos_archivos = self.ARCHIVOS_LECCIONES.get(id_leccion, {})
        nombre_archivo = datos_archivos.get("teoria", f"{id_leccion}_contenido.txt")

        ruta_archivo = os.path.join('lecciones', nombre_archivo)
        texto = "Este papiro digital aún se está forjando. Vuelve más tarde."

        if os.path.exists(ruta_archivo):
            with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                texto = archivo.read()

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

    def abrir_menu_leccion(self, id_leccion: str, titulo: str) -> None:
        """
        Redirige al submenú intermedio evaluando dinámicamente el diccionario JSON.

        Args:
            id_leccion (str): Código interno de la lección.
            titulo (str): Texto amigable de la cabecera.
        """
        app = App.get_running_app()
        pantalla_menu = app.sm.get_screen('menu_leccion')

        titulo_tema_limpio = self.ids.lbl_titulo_tema.text.replace('[b]', '').replace('[/b]', '')

        datos_archivos = self.ARCHIVOS_LECCIONES.get(id_leccion, {})

        tiene_ejemplos = bool(datos_archivos.get("ejemplos"))
        tiene_practica = bool(datos_archivos.get("practica"))

        pantalla_menu.cargar_leccion(id_leccion, titulo, titulo_tema_limpio, tiene_ejemplos,
                                     tiene_practica)
        app.sm.current = 'menu_leccion'


    def abrir_visor_teoria(self, id_leccion: str, titulo: str) -> None:
        """
        Localiza el archivo de texto asociado a la unidad y lo inyecta.

        Args:
            id_leccion (str): Código interno de la lección.
            titulo (str): Texto amigable de la cabecera.
        """
        app = App.get_running_app()
        pantalla_visor = app.sm.get_screen('escuela_visor')
        nombre_dicc = self.ARCHIVOS_LECCIONES.get(id_leccion, f"{id_leccion}_contenido.txt")
        nombre_archivo = nombre_dicc.get("teoria", f"{id_leccion}_contenido.txt")
        ruta_archivo = os.path.join('lecciones', nombre_archivo)

        texto = "Este papiro digital aún se está forjando. Vuelve más tarde."
        if os.path.exists(ruta_archivo):
            with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                texto = archivo.read()

        pantalla_visor.cargar_contenido(id_leccion, titulo, texto)
        app.sm.current = 'escuela_visor'

class FilaParteLeccion(ButtonBehavior, BoxLayout):
    """
    Componente físico para las opciones del menú de lección.
    Reemplaza la inestable generación dinámica de Kivy.
    """
    texto_parte = StringProperty('')
    completada = BooleanProperty(False)

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
        """Dispara la transición al menú intermedio al tocar la fila."""
        self.controlador.abrir_menu_leccion(self.id_unidad, self.texto_unidad)


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
        Disecciona el papiro digital separando teoría, tácticas y mensajes de feedback.

        Escanea implacablemente buscando las etiquetas de resolución.
        Frena el análisis al detectar el ancla [FIN] para reanudar el flujo
        normal de la lección sin contaminar la interfaz.
        """
        self.id_leccion_actual = id_leccion
        self.ids.lbl_titulo.text = f"[b]{titulo.upper()}[/b]"
        self.paginas = []
        self.indice_pagina = 0

        partes_pagina = texto.split('[PAGINA]')

        for bloque in partes_pagina:
            if '[PUZZLE]' in bloque:
                texto_antes, resto = bloque.split('[PUZZLE]', 1)
                inicio_fen = resto.find('[FEN:')
                fin_fen = resto.find(']', inicio_fen)

                if inicio_fen != -1 and fin_fen != -1:
                    datos_puzzle = resto[inicio_fen + 5:fin_fen]
                    texto_teoria = resto[fin_fen + 1:].strip()

                    msg_correcto = "¡MAGISTRAL! Lección dominada."
                    msg_error = "¡ERROR FATAL! Repasa la teoría."

                    if '[CORRECTO]' in texto_teoria:
                        b_izq, b_der = texto_teoria.split('[CORRECTO]', 1)
                        texto_teoria = b_izq

                        if '[ERROR]' in b_der:
                            t_corr, t_err_resto = b_der.split('[ERROR]', 1)
                            msg_correcto = t_corr.strip()

                            if '[FIN]' in t_err_resto:
                                tramos_err = t_err_resto.split('[FIN]', 1)
                                msg_error = tramos_err[0].strip()
                                texto_teoria += '\n\n' + tramos_err[1].strip()
                            else:
                                msg_error = t_err_resto.strip()
                        else:
                            if '[FIN]' in b_der:
                                tramos_corr = b_der.split('[FIN]', 1)
                                msg_correcto = tramos_corr[0].strip()
                                texto_teoria += '\n\n' + tramos_corr[1].strip()
                            else:
                                msg_correcto = b_der.strip()

                    self.paginas.append({
                        'texto': texto_antes.strip(),
                        'puzzle': datos_puzzle,
                        'msg_correcto': msg_correcto,
                        'msg_error': msg_error
                    })

                    if texto_teoria:
                        self.paginas.append({'texto': texto_teoria, 'puzzle': None})
                else:
                    self.paginas.append({'texto': bloque.strip(), 'puzzle': None})
            else:
                if bloque.strip():
                    self.paginas.append({'texto': bloque.strip(), 'puzzle': None})

        self.mostrar_pagina()

    def mostrar_pagina(self) -> None:
        """
        Renderiza la página actual destruyendo los widgets previos.

        Inyecta el fragmento teórico en el contenedor visual. Detecta los tableros
        estáticos residuales para mantener la retrocompatibilidad del formato FEN.
        """
        if not self.paginas:
            return

        contenedor = self.ids.contenedor_contenido
        contenedor.clear_widgets()

        pagina_actual = self.paginas[self.indice_pagina]
        texto_pagina = pagina_actual['texto']
        partes = texto_pagina.split('[FEN:')

        for i, bloque in enumerate(partes):
            if i == 0:
                if bloque.strip():
                    self._agregar_texto(contenedor, bloque.strip())
            else:
                subpartes = bloque.split(']', 1)
                if len(subpartes) == 2:
                    self._agregar_minitablero(contenedor, subpartes[0].strip())
                    if subpartes[1].strip():
                        self._agregar_texto(contenedor, subpartes[1].strip())

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
        Avanza en el temario o detona la emboscada táctica interactiva.

        Usurpa el controlador maestro si el papiro digital se ha consumido por completo
        para encadenar automáticamente el siguiente fragmento capitular.
        """
        pagina_actual = self.paginas[self.indice_pagina]

        if pagina_actual.get('puzzle'):
            self.lanzar_puzzle_leccion(
                pagina_actual['puzzle'],
                pagina_actual.get('msg_correcto', '¡MAGISTRAL! Leccion dominada.'),
                pagina_actual.get('msg_error', '¡ERROR FATAL! Repasa la teoria.')
            )
        else:
            if self.indice_pagina < len(self.paginas) - 1:
                self.indice_pagina += 1
                self.mostrar_pagina()
            else:
                from kivy.app import App
                app = App.get_running_app()
                menu = app.sm.get_screen('menu_leccion')
                menu.avanzar_siguiente_capitulo()

    def volver_unidades(self) -> None:
        """Ejecuta una retirada estratégica hacia el menú de disección de la lección."""
        App.get_running_app().sm.current = 'menu_leccion'

    def _agregar_texto(self, contenedor, texto: str) -> None:
        """
        Instancia una etiqueta de texto y la pega en el contenedor padre.

        Args:
            contenedor: Widget de Kivy contenedor.
            texto (str): Teoría de ajedrez.
        """
        etiqueta = Factory.TextoLeccion()
        etiqueta.text = compilar_markdown_a_kivy(texto)
        contenedor.add_widget(etiqueta)

    def _agregar_minitablero(self, contenedor, bloque_datos: str) -> None:
        """
        Materializa tableros vivos o estáticos respetando las anotaciones geométricas.

        Trocea la etiqueta buscando FEN, flechas y comandos de interactividad.
        Si encuentra la directiva SOL, delega el control de la cuadrícula al
        controlador interactivo.

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

        tramos = bloque_datos.split('|')
        fen_real = tramos[0].strip()

        colores_casillas = []
        flechas_vectores = []
        solucion_uci = []

        mapa_resaltes = {'g': (0.2, 0.8, 0.2, 0.5), 'r': (0.8, 0.2, 0.2, 0.5)}
        mapa_lineas = {'g': (0.2, 0.8, 0.2, 0.85), 'r': (0.8, 0.2, 0.2, 0.85)}

        for tramo in tramos[1:]:
            tramo = tramo.strip()
            if tramo.startswith('C:'):
                datos = tramo[2:].split(',')
                for d in datos:
                    if '-' in d:
                        cas, c = d.strip().split('-')
                        colores_casillas.append((cas.strip(), mapa_resaltes.get(c.strip().lower(), (0.2, 0.8, 0.2, 0.5))))
            elif tramo.startswith('A:'):
                datos = tramo[2:].split(',')
                for d in datos:
                    if '-' in d:
                        mov, c = d.strip().split('-')
                        mov = mov.strip()
                        if len(mov) >= 4:
                            flechas_vectores.append((mov[:2], mov[2:4], mapa_lineas.get(c.strip().lower(), (0.2, 0.8, 0.2, 0.85))))
            elif tramo.startswith('SOL:'):
                datos = tramo[4:].split(',')
                solucion_uci = [mov.strip() for mov in datos if mov.strip()]

        envoltorio = Factory.ContenedorTableroMini()
        cuadricula = envoltorio.ids.grid

        try:
            if solucion_uci:
                ControladorMiniInteractivo(cuadricula, fen_real, solucion_uci)
            else:
                tablero = chess.Board(fen_real)
                for fila in range(7, -1, -1):
                    for col in range(8):
                        es_clara = (fila + col) % 2 != 0
                        pieza = tablero.piece_at(chess.square(col, fila))
                        ruta_pieza = mapa_imagenes.get(pieza.symbol(), '') if pieza else ''
                        cuadricula.add_widget(CasillaMini(es_clara, ruta_pieza))
            contenedor.add_widget(envoltorio)
        except ValueError:
            self._agregar_texto(contenedor, f"[color=#ff0000]ERROR: FEN inválido o corrupto ({fen_real})[/color]")
            return

        def redibujar_anotaciones(instancia, valor) -> None:
            """Callback forzado que recalcula los píxeles absolutos cuando Kivy respira."""
            instancia.canvas.after.clear()
            with instancia.canvas.after:
                sq_w = instancia.width / 8.0
                sq_h = instancia.height / 8.0

                for cas, col_rgba in colores_casillas:
                    idx = chess.parse_square(cas)
                    f = chess.square_file(idx)
                    r = chess.square_rank(idx)
                    Color(*col_rgba)
                    Rectangle(pos=(instancia.x + f * sq_w, instancia.y + r * sq_h), size=(sq_w, sq_h))

                for origen, destino, col_rgba in flechas_vectores:
                    idx_o = chess.parse_square(origen)
                    idx_d = chess.parse_square(destino)

                    x1 = instancia.x + (chess.square_file(idx_o) + 0.5) * sq_w
                    y1 = instancia.y + (chess.square_rank(idx_o) + 0.5) * sq_h
                    x2 = instancia.x + (chess.square_file(idx_d) + 0.5) * sq_w
                    y2 = instancia.y + (chess.square_rank(idx_d) + 0.5) * sq_h

                    Color(*col_rgba)
                    Line(points=[x1, y1, x2, y2], width=dp(3))

                    angulo = math.atan2(y2 - y1, x2 - x1)
                    l_punta = dp(14)
                    p1 = (x2, y2)
                    p2 = (x2 - l_punta * math.cos(angulo - math.pi / 6.0), y2 - l_punta * math.sin(angulo - math.pi / 6.0))
                    p3 = (x2 - l_punta * math.cos(angulo + math.pi / 6.0), y2 - l_punta * math.sin(angulo + math.pi / 6.0))
                    Triangle(points=[p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]])

        cuadricula.bind(pos=redibujar_anotaciones, size=redibujar_anotaciones)
        Clock.schedule_once(lambda dt: redibujar_anotaciones(cuadricula, None), 0.1)

    def volver_unidades(self) -> None:
        """Abandona la clase magistral y huye hacia el índice de unidades."""
        App.get_running_app().sm.current = 'menu_leccion'

    def lanzar_puzzle_leccion(self, datos_puzzle: str, msg_correcto: str, msg_error: str) -> None:
        """
        Inyecta los datos de la lección y despliega la interfaz educativa.

        Normaliza el desglose de la cadena de datos aislando el FEN y
        la secuencia de movimientos en notación UCI, admitiendo espacios o comas.

        Args:
            datos_puzzle (str): Cadena en bruto extraída de la etiqueta [FEN:...].
            msg_correcto (str): Mensaje de victoria configurado en la lección.
            msg_error (str): Mensaje de fallo configurado en la lección.
        """
        from kivy.app import App
        from kivy.factory import Factory

        # Troceamos por la barra vertical ignorando espacios sobrantes
        tramos = datos_puzzle.split('|')
        fen = tramos[0].strip()
        solucion = []

        for tramo in tramos[1:]:
            tramo_limpio = tramo.strip()
            if tramo_limpio.startswith('SOL:'):
                # Extraemos la cadena tras 'SOL:' y unificamos comas a espacios
                crudo = tramo_limpio[4:].replace(',', ' ')
                solucion = [mov.strip() for mov in crudo.split() if mov.strip()]

        app = App.get_running_app()
        app.modo_leccion = True

        puzzle_dict = {
            'fen': fen,
            'moves': solucion,
            'id': 'Leccion',
            'rating': '--',
            'popularity': '--',
            'themes': ''
        }

        app.gestor_ajedrez.cargar_puzzle(puzzle_dict)

        pantalla = app.sm.get_screen('pantalla_leccion')
        pantalla.clear_widgets()

        vista = Factory.VistaLeccion(
            gestor_ajedrez=app.gestor_ajedrez,
            msg_correcto=msg_correcto,
            msg_error=msg_error
        )
        pantalla.add_widget(vista)

        app.sm.current = 'pantalla_leccion'


class CasillaInteractivaLeccion(ButtonBehavior, RelativeLayout):
    """
    Componente visual microscópico y táctil para resolver tácticas.

    A diferencia de su hermana inerte, esta clase procesa eventos físicos
    y permite modificar su textura PNG en tiempo real.
    """

    def __init__(self, nombre_casilla: str, controlador, es_clara: bool, ruta_pieza: str,
                 **kwargs) -> None:
        """
        Inicializa la celda y posiciona sus capas visuales.

        Args:
            nombre_casilla (str): Coordenada alfanumérica pura.
            controlador (ControladorMiniInteractivo): El cerebro que valida la táctica.
            es_clara (bool): Determina el color del mosaico de fondo.
            ruta_pieza (str): Ruta local del archivo gráfico de la pieza.
        """
        super().__init__(**kwargs)
        self.nombre_casilla = nombre_casilla
        self.controlador = controlador

        ruta_fondo = "assets/squares/casilla_clara.png" if es_clara else "assets/squares/casilla_oscura.png"
        self.add_widget(Image(source=ruta_fondo, allow_stretch=True, keep_ratio=False))

        self.img_pieza = Image(source=ruta_pieza, fit_mode='contain', size_hint=(0.85, 0.85),
                               pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.add_widget(self.img_pieza)

    def on_press(self) -> None:
        """Captura la agresión física contra la pantalla y avisa al orquestador."""
        self.controlador.procesar_toque(self.nombre_casilla)

    def actualizar_imagen(self, ruta: str) -> None:
        """Reemplaza la textura visual de la pieza instantáneamente."""
        self.img_pieza.source = ruta


class TableroInteractivoLeccion(GridLayout):
    """
    Controlador autónomo del mini-tablero incrustado en el texto.

    Mantiene su propia instancia del Modelo (chess.Board) y compara
    las pulsaciones del usuario con la solución estricta.
    """

    def __init__(self, fen_inicial: str, solucion_uci: list, **kwargs):
        """
        Ensambla el motor lógico y renderiza la cuadrícula.

        Args:
            fen_inicial (str): Disposición de las piezas.
            solucion_uci (list): Movimientos esperados en notación UCI.
        """
        super().__init__(**kwargs)
        self.cols = 8
        self.rows = 8
        self.size_hint = (None, None)
        self.width = dp(320)
        self.height = dp(320)

        self.board = chess.Board(fen_inicial)
        self.solucion = solucion_uci
        self.paso_actual = 0
        self.casilla_seleccionada = None
        self.diccionario_casillas = {}

        self.mapa_imagenes = {
            'P': 'assets/pieces/blanco_peon.png', 'p': 'assets/pieces/negro_peon.png',
            'N': 'assets/pieces/blanco_caballo.png', 'n': 'assets/pieces/negro_caballo.png',
            'B': 'assets/pieces/blanco_alfil.png', 'b': 'assets/pieces/negro_alfil.png',
            'R': 'assets/pieces/blanco_torre.png', 'r': 'assets/pieces/negro_torre.png',
            'Q': 'assets/pieces/blanco_reina.png', 'q': 'assets/pieces/negro_reina.png',
            'K': 'assets/pieces/blanco_rey.png', 'k': 'assets/pieces/negro_rey.png'
        }

        self.construir_cuadricula()
        self.actualizar_piezas()

    def construir_cuadricula(self) -> None:
        """Inyecta los 64 widgets en la memoria del layout."""
        for fila in range(7, -1, -1):
            for col in range(8):
                nombre = chess.square_name(chess.square(col, fila))
                es_clara = (fila + col) % 2 != 0
                casilla = CasillaInteractivaLeccion(nombre, self, es_clara)
                self.diccionario_casillas[nombre] = casilla
                self.add_widget(casilla)

    def actualizar_piezas(self) -> None:
        """Fuerza la sincronización de los sprites PNG con la matriz lógica."""
        for nombre, widget in self.diccionario_casillas.items():
            pieza = self.board.piece_at(chess.parse_square(nombre))
            widget.img_pieza.source = self.mapa_imagenes.get(pieza.symbol(), '') if pieza else ''

    def procesar_toque(self, nombre_casilla: str) -> None:
        """
        Cruza la interacción humana con la secuencia perfecta.

        Args:
            nombre_casilla (str): El escaque profanado por el usuario.
        """
        if self.paso_actual >= len(self.solucion):
            return

        if self.casilla_seleccionada:
            movimiento_intento = self.casilla_seleccionada + nombre_casilla
            movimiento_esperado = self.solucion[self.paso_actual]

            if movimiento_intento == movimiento_esperado[:4]:
                move = chess.Move.from_uci(movimiento_esperado)
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.paso_actual += 1
                    self.actualizar_piezas()
                    self.casilla_seleccionada = None

                    # Llamada a Kivy para colorear de verde y dar feedback al usuario
                    print("¡Movimiento Magistral!")
                    Clock.schedule_once(self.respuesta_enemiga, 0.6)
                    return

            self.casilla_seleccionada = None
            print("¡Error fatal! Intenta de nuevo.")
        else:
            pieza = self.board.piece_at(chess.parse_square(nombre_casilla))
            if pieza and pieza.color == self.board.turn:
                self.casilla_seleccionada = nombre_casilla

    def respuesta_enemiga(self, dt: float) -> None:
        """
        Devuelve el golpe ejecutando el siguiente movimiento de la lista.

        Args:
            dt (float): Basura inyectada por el Clock de Kivy.
        """
        if self.paso_actual < len(self.solucion):
            movimiento_esperado = self.solucion[self.paso_actual]
            self.board.push(chess.Move.from_uci(movimiento_esperado))
            self.paso_actual += 1
            self.actualizar_piezas()


class ControladorMiniInteractivo:
    """
    Orquesta la lógica de un tablero táctil incrustado en la teoría.

    Se acopla a un GridLayout de Kivy ya existente. Lo vacía y lo rellena
    con celdas interactivas respetando el flujo de la lección.
    """

    def __init__(self, cuadricula, fen_inicial: str, solucion_uci: list) -> None:
        """
        Prepara el motor lógico y renderiza la cuadricula viva.

        Args:
            cuadricula (GridLayout): El contenedor vacío de Kivy.
            fen_inicial (str): Disposición matemática de las piezas.
            solucion_uci (list): Movimientos ganadores requeridos.
        """
        self.cuadricula = cuadricula
        self.board = chess.Board(fen_inicial)
        self.solucion = solucion_uci
        self.paso_actual = 0
        self.casilla_seleccionada = None
        self.diccionario_casillas = {}

        self.mapa_imagenes = {
            'P': 'assets/pieces/blanco_peon.png', 'p': 'assets/pieces/negro_peon.png',
            'N': 'assets/pieces/blanco_caballo.png', 'n': 'assets/pieces/negro_caballo.png',
            'B': 'assets/pieces/blanco_alfil.png', 'b': 'assets/pieces/negro_alfil.png',
            'R': 'assets/pieces/blanco_torre.png', 'r': 'assets/pieces/negro_torre.png',
            'Q': 'assets/pieces/blanco_reina.png', 'q': 'assets/pieces/negro_reina.png',
            'K': 'assets/pieces/blanco_rey.png', 'k': 'assets/pieces/negro_rey.png'
        }
        self.construir_cuadricula()

    def construir_cuadricula(self) -> None:
        """Inyecta los widgets interactivos dentro de la jaula gráfica."""
        self.cuadricula.clear_widgets()
        for fila in range(7, -1, -1):
            for col in range(8):
                nombre = chess.square_name(chess.square(col, fila))
                es_clara = (fila + col) % 2 != 0
                pieza = self.board.piece_at(chess.square(col, fila))
                ruta_pieza = self.mapa_imagenes.get(pieza.symbol(), '') if pieza else ''

                casilla = CasillaInteractivaLeccion(nombre, self, es_clara, ruta_pieza)
                self.diccionario_casillas[nombre] = casilla
                self.cuadricula.add_widget(casilla)

    def procesar_toque(self, nombre_casilla: str) -> None:
        """
        Cruza la interacción humana con la secuencia perfecta.

        Args:
            nombre_casilla (str): El escaque profanado por el jugador.
        """
        if self.paso_actual >= len(self.solucion):
            return

        if self.casilla_seleccionada:
            movimiento_intento = self.casilla_seleccionada + nombre_casilla
            movimiento_esperado = self.solucion[self.paso_actual]

            if movimiento_intento == movimiento_esperado[:4]:
                move = chess.Move.from_uci(movimiento_esperado)
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.paso_actual += 1
                    self.actualizar_piezas()
                    self.casilla_seleccionada = None
                    Clock.schedule_once(self.respuesta_enemiga, 0.6)
                    return

            self.casilla_seleccionada = None
        else:
            pieza = self.board.piece_at(chess.parse_square(nombre_casilla))
            if pieza and pieza.color == self.board.turn:
                self.casilla_seleccionada = nombre_casilla

    def actualizar_piezas(self) -> None:
        """Fuerza la sincronización de los sprites PNG con la matriz lógica."""
        for nombre, widget in self.diccionario_casillas.items():
            pieza = self.board.piece_at(chess.parse_square(nombre))
            ruta = self.mapa_imagenes.get(pieza.symbol(), '') if pieza else ''
            widget.actualizar_imagen(ruta)

    def respuesta_enemiga(self, dt: float) -> None:
        """
        Devuelve el golpe ejecutando el siguiente movimiento de la lista.

        Args:
            dt (float): Basura inyectada por el Clock de Kivy.
        """
        if self.paso_actual < len(self.solucion):
            movimiento_esperado = self.solucion[self.paso_actual]
            self.board.push(chess.Move.from_uci(movimiento_esperado))
            self.paso_actual += 1
            self.actualizar_piezas()


class PantallaMenuLeccion(Screen):
    """
    Controlador gráfico para el submenú de una lección específica.

    Presenta al jugador las opciones iniciales y muta dinámicamente para desplegar
    capítulos teóricos paginados. Actúa como el Controlador puro en el patrón MVC.
    """

    def __init__(self, **kwargs) -> None:
        """Inicializa las variables de estado relativas a la paginación de la vista."""
        super().__init__(**kwargs)
        self.id_leccion = ""
        self.titulo_leccion = ""
        self.texto_crudo_teoria = ""
        self.capitulos_extraidos = []

        self.pagina_actual_capitulos = 0
        self.elementos_por_pagina = 6

    def cargar_leccion(self, id_leccion: str, titulo: str, titulo_tema: str,
                       tiene_ejemplos: bool = True, tiene_practica: bool = True) -> None:
        """
        Forja las tarjetas principales de la lección e inyecta la jerarquía de texto.

        Args:
            id_leccion (str): Identificador unívoco del archivo teórico.
            titulo (str): Título amigable para consumo humano.
            titulo_tema (str): Categoría padre para el breadcrumb visual.
            tiene_ejemplos (bool): Bandera de inyección del botón de ejemplos.
            tiene_practica (bool): Bandera de inyección del botón de ejercicios.
        """
        self.id_leccion = id_leccion
        self.titulo_leccion = titulo

        texto_formateado = f"[b]{titulo_tema.upper()}\n[size=16sp]Leccion: {titulo}[/size][/b]"
        self.ids.lbl_titulo_leccion.text = texto_formateado

        self.dibujar_menu_principal(tiene_ejemplos, tiene_practica)

    def dibujar_menu_principal(self, tiene_ejemplos: bool, tiene_practica: bool) -> None:
        """
        Pinta los botones raíz del menú de lección y purga la vista previa.

        Args:
            tiene_ejemplos (bool): Condicional estructural de tácticas.
            tiene_practica (bool): Condicional estructural de test.
        """
        contenedor = self.ids.grid_partes
        contenedor.clear_widgets()

        btn_teoria = FilaParteLeccion()
        btn_teoria.texto_parte = "1. Teoría"
        btn_teoria.bind(on_release=lambda x: self.desplegar_capitulos_teoria())
        contenedor.add_widget(btn_teoria)

        if tiene_ejemplos:
            btn_ejemplos = FilaParteLeccion()
            btn_ejemplos.texto_parte = "2. Ejemplos"
            btn_ejemplos.bind(on_release=lambda x: self.abrir_ejemplos())
            contenedor.add_widget(btn_ejemplos)

        if tiene_practica:
            btn_practica = FilaParteLeccion()
            btn_practica.texto_parte = "3. Práctica"
            btn_practica.bind(on_release=lambda x: self.abrir_practica())
            contenedor.add_widget(btn_practica)

    def desplegar_capitulos_teoria(self) -> None:
        """
        Lee el papiro digital y secuestra la interfaz para mostrar el desglose.

        Busca anclas Markdown de nivel dos en disco. Prepara el estado interno para
        la paginación gráfica en RAM.
        """
        app = App.get_running_app()
        pantalla_unidades = app.sm.get_screen('escuela_unidades')

        datos_archivos = pantalla_unidades.ARCHIVOS_LECCIONES.get(self.id_leccion, {})
        nombre_archivo = datos_archivos.get("teoria", f"{self.id_leccion}_contenido.txt")
        ruta_archivo = os.path.join('lecciones', nombre_archivo)

        if not os.path.exists(ruta_archivo):
            print("ERROR: Archivo no forjado en el disco físico.")
            return

        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            self.texto_crudo_teoria = archivo.read()

        texto_normalizado = f"\n{self.texto_crudo_teoria}"
        fragmentos = texto_normalizado.split('\n## ')
        self.capitulos_extraidos = []

        intro_cruda = fragmentos[0].strip()
        if intro_cruda:
            self.capitulos_extraidos.append(("Introducción", intro_cruda))

        for frag in fragmentos[1:]:
            lineas = frag.split('\n', 1)
            titulo_cap = lineas[0].strip()
            contenido = f"## {frag}" if len(lineas) > 1 else f"## {titulo_cap}"
            self.capitulos_extraidos.append((titulo_cap, contenido))

        self.pagina_actual_capitulos = 0
        self.renderizar_pagina_capitulos()

    def renderizar_pagina_capitulos(self) -> None:
        """
        Inyecta un subconjunto de botones en la interfaz basándose en el estado.

        Genera dinámicamente controles de navegación inferior instanciando widgets
        estáticos en un contenedor aislado para eludir las limitaciones del scroll.
        """
        contenedor = self.ids.grid_partes
        contenedor.clear_widgets()

        caja_nav = self.ids.caja_paginacion
        caja_nav.clear_widgets()

        inicio = self.pagina_actual_capitulos * self.elementos_por_pagina
        fin = inicio + self.elementos_por_pagina
        capitulos_pagina = self.capitulos_extraidos[inicio:fin]

        for indice_relativo, (titulo_cap, contenido_cap) in enumerate(capitulos_pagina):
            indice_absoluto = inicio + indice_relativo
            btn_cap = FilaParteLeccion()
            btn_cap.texto_parte = titulo_cap
            # Pasamos la posición exacta en memoria aniquilando la inyección de strings
            btn_cap.bind(
                on_release=lambda x, idx=indice_absoluto: self.abrir_visor_fragmentado(idx))
            contenedor.add_widget(btn_cap)

        total_paginas = (len(self.capitulos_extraidos) - 1) // self.elementos_por_pagina + 1

        if total_paginas > 1:
            from kivy.uix.button import Button
            from kivy.uix.label import Label

            btn_prev = Button(
                text="< ANT",
                font_name='Michroma',
                background_color=[0.2, 0.6, 0.8, 1],
                background_normal='assets/ui/button.png',
                background_down='assets/ui/button_down.png',
                border=(0, 0, 0, 0),
                bold=True,
                disabled=(self.pagina_actual_capitulos == 0)
            )
            btn_prev.bind(on_release=lambda x: self.cambiar_pagina_capitulos(-1))

            lbl_pag = Label(
                text=f"{self.pagina_actual_capitulos + 1} / {total_paginas}",
                font_name='Michroma',
                color=[0.1, 0.5, 0.6, 1],
                bold=True
            )

            btn_next = Button(
                text="SIG >",
                font_name='Michroma',
                background_color=[0.2, 0.8, 0.4, 1],
                background_normal='assets/ui/button.png',
                background_down='assets/ui/button_down.png',
                border=(0, 0, 0, 0),
                bold=True,
                disabled=(self.pagina_actual_capitulos == total_paginas - 1)
            )
            btn_next.bind(on_release=lambda x: self.cambiar_pagina_capitulos(1))

            caja_nav.add_widget(btn_prev)
            caja_nav.add_widget(lbl_pag)
            caja_nav.add_widget(btn_next)

    def cambiar_pagina_capitulos(self, delta: int) -> None:
        """
        Altera la posición del puntero de memoria y fuerza una reconstrucción.

        Args:
            delta (int): Escalar de desplazamiento de vista (-1 o 1).
        """
        self.pagina_actual_capitulos += delta
        self.renderizar_pagina_capitulos()

    def abrir_visor_fragmentado(self, indice_capitulo: int) -> None:
        """
        Inyecta el fragmento aislado y despierta la vista de lectura.

        Args:
            indice_capitulo (int): Coordenada exacta en el array de capítulos.
        """
        from kivy.app import App

        self.indice_capitulo_actual = indice_capitulo
        titulo_capitulo, contenido = self.capitulos_extraidos[indice_capitulo]

        app = App.get_running_app()
        pantalla_visor = app.sm.get_screen('escuela_visor')
        pantalla_visor.cargar_contenido(self.id_leccion, self.titulo_leccion, contenido)
        app.sm.current = 'escuela_visor'

    def avanzar_siguiente_capitulo(self) -> bool:
        """
        Fuerza la carga del siguiente bloque de texto en el motor gráfico.

        Sincroniza la paginación oculta en segundo plano para que el usuario
        no pierda su posición si decide volver al índice.

        Returns:
            bool: Verdadero si la mutación tuvo éxito. Falso si chocamos contra el muro final.
        """
        if hasattr(self, 'indice_capitulo_actual') and self.indice_capitulo_actual < len(
                self.capitulos_extraidos) - 1:
            siguiente_indice = self.indice_capitulo_actual + 1
            self.abrir_visor_fragmentado(siguiente_indice)

            nueva_pagina = siguiente_indice // self.elementos_por_pagina
            if nueva_pagina != self.pagina_actual_capitulos:
                self.pagina_actual_capitulos = nueva_pagina
                self.renderizar_pagina_capitulos()

            return True
        return False

    def abrir_ejemplos(self) -> None:
        """Despliega la simulación visual."""
        print("Stub: Cargar minitableros interactivos de ejemplos")

    def abrir_practica(self) -> None:
        """Activa el motor de ejercicios lógicos."""
        print("Stub: Cargar motor de validación de práctica")

    def volver_unidades(self) -> None:
        """Provoca la rendición y devuelve al menú global."""
        App.get_running_app().sm.current = 'escuela_unidades'