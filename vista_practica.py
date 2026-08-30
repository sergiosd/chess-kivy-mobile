from __future__ import annotations

import unicodedata

import chess
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from main import VistaTablero
from utilidades import CalculadorRatingTactico


class VistaPracticaLeccion(VistaTablero):
    """Controlador gráfico especializado para los ejercicios tácticos de la Escuela."""

    def __init__(
        self,
        id_leccion: str,
        archivo_csv: str,
        titulo_leccion: str = "",
        **kwargs,
    ):
        """
        Inicializa la vista de práctica con el contexto de la lección activa.

        Args:
            id_leccion: Identificador de la lección.
            archivo_csv: Archivo CSV con los puzles de la lección.
            titulo_leccion: Título legible de la lección.
            **kwargs: Argumentos absorbidos por la clase base.
        """
        self.id_leccion = id_leccion
        self.archivo_csv = archivo_csv
        self.titulo_leccion = titulo_leccion
        self._modo_solucion = False
        self._tablero_revision: chess.Board | None = None
        self._movimientos_revision: list[str] = []
        self._indice_revision = 0
        self._animacion_solucion_activa = False
        super().__init__(habilitar_visor_solucion=False, **kwargs)
        self._configurar_controles_solucion()

    def _configurar_controles_solucion(self) -> None:
        """Prepara los controles de revisión sin alterar el layout global."""
        panel = self.ids.panel_inferior
        indice_original = panel.children.index(self.ids.btn_siguiente)

        # self.ids guarda WeakProxy. Conservamos la instancia real antes de
        # sacarla del árbol para que Kivy no pueda liberarla al reparentarla.
        self._btn_siguiente = panel.children[indice_original]
        panel.remove_widget(self._btn_siguiente)

        self._fila_acciones = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60),
            spacing=0,
        )
        self._btn_mostrar_solucion = Button(
            text="MOSTRAR SOLUCION",
            size_hint_x=None,
            width=0,
            opacity=0,
            disabled=True,
            background_color=(1, 1, 1, 1),
            background_normal="assets/ui/button.png",
            background_down="assets/ui/button_down.png",
            border=(0, 0, 0, 0),
            bold=True,
        )
        self._btn_mostrar_solucion.bind(on_release=self.mostrar_solucion)

        self._btn_siguiente.size_hint_x = 1
        self._fila_acciones.add_widget(self._btn_mostrar_solucion)
        self._fila_acciones.add_widget(self._btn_siguiente)
        panel.add_widget(self._fila_acciones, index=indice_original)

        self._fila_navegacion = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )
        self._btn_solucion_anterior = Button(
            text="<",
            size_hint_x=0.25,
            background_color=(1, 1, 1, 1),
            background_normal="assets/ui/button.png",
            background_down="assets/ui/button_down.png",
            border=(0, 0, 0, 0),
            bold=True,
        )
        self._btn_solucion_anterior.bind(on_release=self.retroceder_solucion)

        self._lbl_paso_solucion = Label(
            text="INICIO",
            size_hint_x=0.5,
            font_size="16sp",
            bold=True,
            color=(0.95, 0.95, 0.95, 1),
            halign="center",
            valign="middle",
        )
        self._lbl_paso_solucion.bind(
            size=lambda instance, size: setattr(instance, "text_size", size)
        )

        self._btn_solucion_siguiente = Button(
            text=">",
            size_hint_x=0.25,
            background_color=(1, 1, 1, 1),
            background_normal="assets/ui/button.png",
            background_down="assets/ui/button_down.png",
            border=(0, 0, 0, 0),
            bold=True,
        )
        self._btn_solucion_siguiente.bind(on_release=self.avanzar_solucion)

        self._fila_navegacion.add_widget(self._btn_solucion_anterior)
        self._fila_navegacion.add_widget(self._lbl_paso_solucion)
        self._fila_navegacion.add_widget(self._btn_solucion_siguiente)

    def _mostrar_acciones_fallo(self) -> None:
        """Muestra Mostrar solución junto a Siguiente puzzle tras una derrota."""
        self._fila_acciones.spacing = dp(8)
        self._btn_mostrar_solucion.size_hint_x = 1
        self._btn_mostrar_solucion.opacity = 1
        self._btn_mostrar_solucion.disabled = False
        self._btn_siguiente.size_hint_x = 1
        self._btn_siguiente.text = "SIGUIENTE PUZZLE"

    def _ocultar_boton_solucion(self) -> None:
        """Oculta el acceso a la solución y devuelve el ancho al botón siguiente."""
        self._fila_acciones.spacing = 0
        self._btn_mostrar_solucion.size_hint_x = None
        self._btn_mostrar_solucion.width = 0
        self._btn_mostrar_solucion.opacity = 0
        self._btn_mostrar_solucion.disabled = True
        self._btn_siguiente.size_hint_x = 1

    def _restablecer_panel_practica(self) -> None:
        """Abandona la revisión y restaura el panel normal de práctica."""
        self._modo_solucion = False
        self._tablero_revision = None
        self._movimientos_revision = []
        self._indice_revision = 0
        self._animacion_solucion_activa = False

        if self._fila_navegacion.parent is not None:
            self._fila_navegacion.parent.remove_widget(self._fila_navegacion)

        for etiqueta in (self.ids.lbl_info, self.ids.lbl_temas):
            etiqueta.size_hint_y = 1
            etiqueta.opacity = 1

        self._ocultar_boton_solucion()
        self._btn_siguiente.disabled = False
        self._btn_siguiente.text = "SIGUIENTE PUZZLE"

    def al_tocar_casilla(self, nombre_casilla: str) -> None:
        """Añade a la práctica el acceso a la solución cuando se produce un fallo."""
        if self._modo_solucion:
            return

        estado_anterior = self.gestor_ajedrez.estado_puzzle
        super().al_tocar_casilla(nombre_casilla)

        if (
            estado_anterior != "DERROTA"
            and self.gestor_ajedrez.estado_puzzle == "DERROTA"
        ):
            self._mostrar_acciones_fallo()

    def mostrar_solucion(self, *_args) -> None:
        """Inicia una reproducción manual de toda la solución sobre un tablero aislado."""
        if self.gestor_ajedrez.estado_puzzle != "DERROTA":
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

        self._modo_solucion = True
        self._tablero_revision = tablero_revision
        self._movimientos_revision = movimientos
        self._indice_revision = 0
        self._animacion_solucion_activa = False

        self.limpiar_iluminacion()
        self.limpiar_flecha()
        self._ocultar_boton_solucion()

        panel = self.ids.panel_inferior
        if self._fila_navegacion.parent is None:
            indice = panel.children.index(self._fila_acciones) + 1
            panel.add_widget(self._fila_navegacion, index=indice)

        for etiqueta in (self.ids.lbl_info, self.ids.lbl_temas):
            etiqueta.size_hint_y = None
            etiqueta.height = 0
            etiqueta.opacity = 0

        self.ids.lbl_estado.text = "REVISION DE LA SOLUCION"
        self.ids.lbl_estado.color = [0.1, 0.8, 0.8, 1]
        self._btn_siguiente.text = "SIGUIENTE PUZZLE"

        self._renderizar_tablero_revision()
        self._actualizar_navegacion_solucion()

        # La reproducción comienza mostrando también la jugada inicial de la IA.
        self.avanzar_solucion()

    def avanzar_solucion(self, *_args) -> None:
        """Anima y avanza un movimiento dentro de la solución."""
        tablero = self._tablero_revision
        if (
            not self._modo_solucion
            or tablero is None
            or self._animacion_solucion_activa
            or self._indice_revision >= len(self._movimientos_revision)
        ):
            return

        movimiento_uci = self._movimientos_revision[self._indice_revision]
        movimiento = chess.Move.from_uci(movimiento_uci)
        if movimiento not in tablero.legal_moves:
            self._btn_solucion_siguiente.disabled = True
            self._lbl_paso_solucion.text = "ERROR"
            return

        origen = movimiento_uci[:2]
        destino = movimiento_uci[2:4]
        pieza = tablero.piece_at(movimiento.from_square)
        simbolo = pieza.symbol() if pieza else ""
        if not simbolo:
            return

        self.limpiar_flecha()
        self._bloquear_controles_revision(True)

        # El tablero lógico aún no avanza: la posición anterior permanece visible
        # mientras el sprite fantasma recorre físicamente el movimiento.
        self.diccionario_casillas[origen].ruta_pieza = ""

        def terminar_animacion() -> None:
            """Consolida el avance lógico cuando termina el desplazamiento visual."""
            if not self._modo_solucion or self._tablero_revision is not tablero:
                return

            tablero.push(movimiento)
            self._indice_revision += 1
            self._renderizar_tablero_revision()

            if self.sonido_mover:
                self.sonido_mover.play()

            self.mostrar_flecha_error(movimiento_uci)
            self._bloquear_controles_revision(False)
            self._actualizar_navegacion_solucion()

        self.animar_pieza(origen, destino, simbolo, terminar_animacion)

    def retroceder_solucion(self, *_args) -> None:
        """Anima hacia atrás el último movimiento y restaura la posición anterior."""
        tablero = self._tablero_revision
        if (
            not self._modo_solucion
            or tablero is None
            or self._animacion_solucion_activa
            or self._indice_revision <= 0
        ):
            return

        movimiento_uci = self._movimientos_revision[self._indice_revision - 1]
        movimiento = chess.Move.from_uci(movimiento_uci)
        origen = movimiento_uci[:2]
        destino = movimiento_uci[2:4]

        pieza = tablero.piece_at(movimiento.to_square)
        simbolo = pieza.symbol() if pieza else ""
        if not simbolo:
            return

        self.limpiar_flecha()
        self._bloquear_controles_revision(True)
        self.diccionario_casillas[destino].ruta_pieza = ""

        def terminar_animacion() -> None:
            """Restaura el estado lógico previo al finalizar la animación inversa."""
            if not self._modo_solucion or self._tablero_revision is not tablero:
                return

            tablero.pop()
            self._indice_revision -= 1
            self._renderizar_tablero_revision()

            if self.sonido_mover:
                self.sonido_mover.play()

            if self._indice_revision > 0:
                movimiento_anterior = self._movimientos_revision[
                    self._indice_revision - 1
                ]
                self.mostrar_flecha_error(movimiento_anterior)

            self._bloquear_controles_revision(False)
            self._actualizar_navegacion_solucion()

        self.animar_pieza(destino, origen, simbolo, terminar_animacion)

    def _bloquear_controles_revision(self, bloqueados: bool) -> None:
        """Evita pulsaciones concurrentes mientras una pieza está en movimiento."""
        self._animacion_solucion_activa = bloqueados
        self._btn_siguiente.disabled = bloqueados
        self.ids.btn_volver.disabled = bloqueados

        if bloqueados:
            self._btn_solucion_anterior.disabled = True
            self._btn_solucion_siguiente.disabled = True

    def _renderizar_tablero_revision(self) -> None:
        """Pinta el tablero aislado de revisión sin tocar el estado real del puzzle."""
        if self._tablero_revision is None:
            return

        for nombre_casilla, widget in self.diccionario_casillas.items():
            indice_casilla = chess.parse_square(nombre_casilla)
            pieza = self._tablero_revision.piece_at(indice_casilla)
            widget.ruta_pieza = (
                self.mapa_imagenes.get(pieza.symbol(), "") if pieza else ""
            )

    def _actualizar_navegacion_solucion(self) -> None:
        """Actualiza contador y límites de los botones anterior/siguiente."""
        total = len(self._movimientos_revision)
        if self._indice_revision == 0:
            self._lbl_paso_solucion.text = "INICIO"
        else:
            self._lbl_paso_solucion.text = f"{self._indice_revision} / {total}"

        if not self._animacion_solucion_activa:
            self._btn_solucion_anterior.disabled = self._indice_revision == 0
            self._btn_solucion_siguiente.disabled = self._indice_revision >= total

    @staticmethod
    def _texto_sin_acentos(texto: str) -> str:
        """Devuelve un texto sin acentos ni marcas diacríticas."""
        normalizado = unicodedata.normalize("NFD", texto or "")
        return "".join(
            caracter
            for caracter in normalizado
            if unicodedata.category(caracter) != "Mn"
        )

    def _obtener_nombre_tactica(self) -> str:
        """Construye el nombre visible de la táctica sin acentos."""
        titulo = self._texto_sin_acentos(self.titulo_leccion).strip().upper()

        if not titulo:
            return "TACTICA"

        equivalencias = {
            "ATAQUE DOBLE": "ATAQUES DOBLES",
            "ATAQUES DOBLES": "ATAQUES DOBLES",
        }
        return equivalencias.get(titulo, titulo)

    def _obtener_titulo_superior(self) -> str:
        """Genera el título superior visible para la práctica actual."""
        estado_local = self.perfil_actual["practica_lecciones"][self.id_leccion]
        rating_local = float(estado_local.get("rating", 0.0))
        rango = self._texto_sin_acentos(
            CalculadorRatingTactico.obtener_rango(rating_local)
        ).upper()
        return f"{rango} EN {self._obtener_nombre_tactica()}"

    def _obtener_bloque_inferior(self) -> str:
        """Genera el bloque inferior con temas, rating y plies."""
        info = self.gestor_ajedrez.info_puzzle or {}
        estado_local = self.perfil_actual["practica_lecciones"][self.id_leccion]
        rating_local = float(estado_local.get("rating", 0.0))
        plies = int(info.get("plies", len(info.get("moves", []))))

        super().mostrar_temas_traducidos()
        temas = self._texto_sin_acentos(self.ids.lbl_temas.text).upper().strip()

        dificultad_visible = CalculadorRatingTactico.obtener_dificultad_visible(plies)

        lineas = []
        if temas:
            lineas.append(temas)
        lineas.append(f"RATING: {rating_local:.1f} · {dificultad_visible}")
        lineas.append(f"PUZZLE: {plies} PLIES")
        return "\n".join(lineas)

    def mostrar_temas_traducidos(self) -> None:
        """Elimina acentos y añade rating y plies al bloque inferior."""
        self.ids.lbl_temas.text = self._obtener_bloque_inferior()

    def registrar_resultado_puzzle(self, victoria: bool) -> tuple[float, float]:
        """
        Calcula y persiste el rating 0–100 de la lección activa.

        La dificultad se deriva de la longitud real del puzzle en plies. El ELO
        externo del CSV queda únicamente como metadato y no afecta al cálculo.
        """
        info = self.gestor_ajedrez.info_puzzle
        if not info:
            return 0.0, 0.0

        id_puzzle = info.get("id")
        plies = int(info.get("plies", len(info.get("moves", []))))
        dificultad = float(
            info.get(
                "dificultad_rating",
                CalculadorRatingTactico.dificultad_por_plies(plies),
            )
        )

        estado_local = self.perfil_actual["practica_lecciones"][self.id_leccion]
        rating_actual = float(estado_local.get("rating", 0.0))
        variacion, nuevo_rating = CalculadorRatingTactico.actualizar_rating(
            rating_actual,
            dificultad,
            victoria,
        )

        estado_local["rating"] = nuevo_rating

        if victoria:
            if id_puzzle and id_puzzle not in estado_local["resueltos"]:
                estado_local["resueltos"].append(id_puzzle)
        else:
            if id_puzzle and id_puzzle not in estado_local["fallados"]:
                estado_local["fallados"].append(id_puzzle)

        self.gestor_perfiles.guardar_perfil(self.perfil_actual)
        return variacion, nuevo_rating

    def cargar_siguiente_puzzle(self) -> None:
        """Extrae el siguiente desafío de la base de datos local y redibuja la vista."""
        self._restablecer_panel_practica()
        self.limpiar_flecha()

        nuevo_puzzle = self.gestor_puzzles.obtener_puzzle_practica(
            id_leccion=self.id_leccion,
            archivo_csv=self.archivo_csv,
            perfil_usuario=self.perfil_actual,
        )

        if nuevo_puzzle:
            self.gestor_ajedrez.cargar_puzzle(nuevo_puzzle)
            self.inicializar_tablero()
            self.actualizar_piezas_visuales()
            self._btn_siguiente.text = "SIGUIENTE PUZZLE"
        else:
            self.ids.lbl_estado.text = "MODULO COMPLETADO"
            self.ids.lbl_estado.color = [0, 1, 0, 1]
            self._btn_siguiente.disabled = True

    def volver_menu(self) -> None:
        """Abandona la práctica y retrocede al menú de la lección."""
        App.get_running_app().sm.current = "menu_leccion"

    def actualizar_piezas_visuales(self) -> None:
        """Sincroniza tablero y textos de la práctica táctica."""
        super().actualizar_piezas_visuales()

        info = self.gestor_ajedrez.info_puzzle
        if info:
            self.ids.lbl_mision.text = self._obtener_titulo_superior()
            self.ids.lbl_info.text = self._texto_sin_acentos(
                f"TACTICA ID: {info.get('id', '--')}"
            ).upper()
            self.mostrar_temas_traducidos()

            es_blancas = self.gestor_ajedrez.board.turn == chess.WHITE
            color_turno = (
                "[color=#ffffff]BLANCAS[/color]"
                if es_blancas
                else "[color=#ff6b6b]NEGRAS[/color]"
            )
            if self.gestor_ajedrez.estado_puzzle == "JUGANDO":
                self.ids.lbl_estado.text = f"TU TURNO: {color_turno}"

    def formatear_resultado_puzzle(
        self,
        victoria: bool,
        variacion: float,
        nueva_puntuacion: float,
    ) -> str:
        """Genera el feedback visible del rating táctico de la lección."""
        rango = self._texto_sin_acentos(
            CalculadorRatingTactico.obtener_rango(nueva_puntuacion)
        ).upper()
        return (
            f"{'CORRECTO' if victoria else 'INCORRECTO'} "
            f"RATING: {nueva_puntuacion:.1f} "
            f"({variacion:+.1f}) · {rango}"
        )

    def formatear_info_resultado(self, info: dict) -> str:
        """Muestra el identificador del puzzle sin depender del ELO externo."""
        return self._texto_sin_acentos(
            f"TACTICA ID: {info.get('id', '--')}"
        ).upper()
