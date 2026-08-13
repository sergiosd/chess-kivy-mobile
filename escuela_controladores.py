from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty
from kivy.app import App


class FilaUnidadEscuela(BoxLayout):
    """
    Componente visual interactivo que representa una lección del temario.

    Gestiona de forma aislada la casilla de verificación y notifica al
    controlador principal sobre los cambios de estado.
    """
    texto_unidad = StringProperty('')
    completada = BooleanProperty(False)

    def __init__(self, id_unidad: str, controlador, **kwargs) -> None:
        """
        Inicializa la fila inyectando su identificador y el gestor superior.

        Args:
            id_unidad (str): Código interno de la lección.
            controlador (PantallaEscuelaUnidades): Pantalla que orquesta el guardado.
        """
        super().__init__(**kwargs)
        self.id_unidad = id_unidad
        self.controlador = controlador

    def al_alternar(self, estado: bool) -> None:
        """
        Intercepta el toque asqueroso del usuario sobre la casilla y lo delega.

        Args:
            estado (bool): Verdadero si el usuario marcó el tick.
        """
        self.controlador.registrar_progreso(self.id_unidad, estado)


class PantallaEscuelaTemas(Screen):
    """Controlador gráfico principal para seleccionar bloques de estudio masivos."""

    def abrir_tema(self, id_tema: str) -> None:
        """
        Configura la pantalla de unidades con el contenido del bloque seleccionado.

        Args:
            id_tema (str): El identificador de la categoría pulsada.
        """
        app = App.get_running_app()
        pantalla_unidades = app.sm.get_screen('escuela_unidades')
        pantalla_unidades.cargar_tema(id_tema)
        app.sm.current = 'escuela_unidades'

    def volver_menu(self) -> None:
        """Abandona el entorno educativo retornando al menú general."""
        App.get_running_app().sm.current = 'menu_principal'


class PantallaEscuelaUnidades(Screen):
    """Vista de detalle que despliega el temario y escupe las casillas de verificación."""

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
        Purga la cuadrícula gráfica y construye las filas iterando sobre la base de datos local.

        Args:
            id_tema (str): La clave del diccionario correspondiente a la categoría elegida.
        """
        self.tema_actual = id_tema
        self.ids.lbl_titulo_tema.text = f"[b]TEMA: {id_tema.upper()}[/b]"
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
            estado (bool): El nuevo valor de la casilla booleana.
        """
        perfil = self._obtener_perfil_activo()

        if 'progreso_escuela' not in perfil:
            perfil['progreso_escuela'] = {}

        perfil['progreso_escuela'][id_unidad] = estado
        self.gestor_perfiles.guardar_perfil(perfil)

    def _obtener_perfil_activo(self) -> dict:
        """
        Extrae y devuelve el diccionario de estado del jugador activo en sesión.

        Returns:
            dict: Objeto JSON parseado directamente desde la memoria.
        """
        nombre = self.gestor_perfiles.obtener_ultimo_usuario()
        return self.gestor_perfiles.cargar_perfil(nombre)

    def volver_temas(self) -> None:
        """Huye despavoridamente a la selección de categorías."""
        App.get_running_app().sm.current = 'escuela_temas'

    def siguiente_unidad(self) -> None:
        """Maneja la lógica de saltar a un visor de contenido de la unidad."""
        print("Stub: Aquí abriremos el tablero interactivo de la lección.")