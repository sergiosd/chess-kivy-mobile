from kivy.app import App
from main import VistaTablero  # Asegúrate del nombre real de tu archivo de vistas
import chess


class VistaPracticaLeccion(VistaTablero):
    """
    Controlador gráfico especializado para los ejercicios tácticos de la Escuela.

    Hereda de VistaTablero (Vista en MVC) para reutilizar la lógica de renderizado,
    pero sobrescribe los métodos de persistencia para confinar el ELO y el historial
    estrictamente al nodo 'practica_lecciones' del perfil del usuario.
    """

    def __init__(self, id_leccion: str, archivo_csv: str, **kwargs):
        """
        Inicializa la vista de práctica con el contexto de la lección activa.

        Args:
            id_leccion (str): Identificador de la lección (ej. 'tac_02').
            archivo_csv (str): Nombre del archivo que contiene los puzles locales.
            **kwargs: Argumentos absorbidos por la clase base (gestores y perfil).
        """
        self.id_leccion = id_leccion
        self.archivo_csv = archivo_csv
        super().__init__(**kwargs)

    def registrar_resultado_puzzle(self, victoria: bool) -> tuple:
        """
        Calcula y persiste el ELO local de la lección, aislando los resultados.

        Sobrescribe el método de la clase base. Aplica la variación matemática
        al 'elo' local de la táctica y registra el ID en 'resueltos' o 'fallados'.

        Args:
            victoria (bool): True si el jugador superó el puzle, False si erró.

        Returns:
            tuple: (variacion_entera, nuevo_elo_entero) para inyectar en la UI.
        """
        info = self.gestor_ajedrez.info_puzzle
        if not info:
            return 0, 1000

        id_puzzle = info.get("id")
        elo_puzzle = int(info.get("rating", 1000))

        # Accedemos estrictamente al estado local de esta lección específica
        estado_local = self.perfil_actual["practica_lecciones"][self.id_leccion]
        elo_jugador = int(estado_local.get("elo", 1000))

        # Calculamos la variación usando nuestro servicio matemático agnóstico
        from utilidades import CalculadorElo
        # Pasamos 0 como partidas jugadas para mantener la constante K estable en modo práctica
        variacion = CalculadorElo.calcular_variacion(elo_jugador, elo_puzzle, victoria, 0)
        variacion_entera = int(round(variacion))
        nuevo_elo = max(0, elo_jugador + variacion_entera)

        # Actualizamos RAM
        estado_local["elo"] = nuevo_elo

        if victoria:
            if id_puzzle not in estado_local["resueltos"]:
                estado_local["resueltos"].append(id_puzzle)
        else:
            if id_puzzle not in estado_local["fallados"]:
                estado_local["fallados"].append(id_puzzle)

        # Persistimos en disco duro
        self.gestor_perfiles.guardar_perfil(self.perfil_actual)

        return variacion_entera, nuevo_elo

    def cargar_siguiente_puzzle(self) -> None:
        """
        Extrae el siguiente desafío de la base de datos local y redibuja la vista.

        Sobrescribe el comportamiento global para forzar la lectura del CSV
        confinado a la lección actual.
        """
        self.limpiar_flecha()

        nuevo_puzzle = self.gestor_puzzles.obtener_puzzle_practica(
            id_leccion=self.id_leccion,
            archivo_csv=self.archivo_csv,
            perfil_usuario=self.perfil_actual
        )

        if nuevo_puzzle:
            self.gestor_ajedrez.cargar_puzzle(nuevo_puzzle)
            self.inicializar_tablero()
            self.actualizar_piezas_visuales()

            es_blancas = self.gestor_ajedrez.board.turn == chess.WHITE
            color_turno = "[color=#ffffff]BLANCAS[/color]" if es_blancas else "[color=#ff6b6b]NEGRAS[/color]"
            self.ids.lbl_estado.text = f"Tu turno: {color_turno}"

            self.ids.lbl_temas.text = "Práctica de Lección"
            self.ids.btn_siguiente.text = "SIGUIENTE PUZZLE"
        else:
            self.ids.lbl_estado.text = "¡Módulo completado!"
            self.ids.lbl_estado.color = [0, 1, 0, 1]
            self.ids.btn_siguiente.disabled = True

    def volver_menu(self) -> None:
        """
        Abandona la práctica y retrocede al menú de la lección en lugar del menú general.
        """
        App.get_running_app().sm.current = 'menu_leccion'

    def actualizar_piezas_visuales(self) -> None:
        """
        Sincroniza el estado lógico con el lienzo gráfico interceptando los metadatos.

        Sobrescribe el comportamiento de la clase base `VistaTablero`. Primero
        delega el renderizado estricto de las texturas PNG al método superior
        y, posteriormente, secuestra las etiquetas de la interfaz para inyectar
        el ELO aislado correspondiente a la práctica de la lección activa.

        Returns:
            None
        """
        # 1. Delegamos el renderizado de los escaques y piezas PNG a la clase padre
        super().actualizar_piezas_visuales()

        # 2. Interceptamos la actualización de texto
        info = self.gestor_ajedrez.info_puzzle
        if info:
            # Extraemos de forma segura el nodo aislado de la lección
            estado_local = self.perfil_actual.get("practica_lecciones", {}).get(self.id_leccion, {})
            elo_local = int(estado_local.get("elo", 1000))

            # Subyugamos los IDs visuales inyectando las métricas de la escuela
            self.ids.lbl_mision.text = f"ELO Lección: {elo_local} | Puzzle ELO: {info.get('rating', '--')}"

            # Purgamos información irrelevante del panel inferior
            self.ids.lbl_info.text = f"Táctica ID: {info.get('id', '--')}"

            # Sincronizamos el indicador de turno
            es_blancas = self.gestor_ajedrez.board.turn == chess.WHITE
            color_turno = "[color=#ffffff]BLANCAS[/color]" if es_blancas else "[color=#ff6b6b]NEGRAS[/color]"
            if self.gestor_ajedrez.estado_puzzle == "JUGANDO":
                self.ids.lbl_estado.text = f"Tu turno: {color_turno}"