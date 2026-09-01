from __future__ import annotations

import unicodedata

import chess
from kivy.app import App
from kivy.core.text import DEFAULT_FONT
from kivy.graphics import Color, RoundedRectangle, Triangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from main import BotonTextoAdaptativo, VistaTablero
from utilidades import CalculadorRatingTactico
from widgets_adaptativos import BotonTextoAdaptativo, TextoAdaptativo


class BocadilloGuia(RelativeLayout):
    """Dibuja un bocadillo adaptable para el personaje guía."""

    def __init__(self, **kwargs) -> None:
        """Inicializa el fondo redondeado y su cola lateral."""
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color_fondo = Color(1, 1, 1, 0.97)
            self._cola = Triangle()
            self._fondo = RoundedRectangle(radius=[dp(14)])

        self.bind(pos=self._actualizar_canvas, size=self._actualizar_canvas)
        self._actualizar_canvas()

    def _actualizar_canvas(self, *_args) -> None:
        """Mantiene el bocadillo ajustado al tamaño del widget."""
        ancho_cola = dp(13)
        ancho_fondo = max(0, self.width - ancho_cola)

        self._fondo.pos = (self.x + ancho_cola, self.y)
        self._fondo.size = (ancho_fondo, self.height)

        centro_y = self.y + self.height * 0.48
        self._cola.points = [
            self.x + ancho_cola,
            centro_y + dp(10),
            self.x,
            centro_y,
            self.x + ancho_cola,
            centro_y - dp(10),
        ]


class VistaPracticaLeccion(VistaTablero):
    """Controlador gráfico especializado para los ejercicios tácticos de la Escuela."""

    _PISTAS_MOTIVO = (
        ("fork", "Busca un ataque doble"),
        ("pin", "Busca cómo aprovechar una clavada"),
        ("skewer", "Busca una enfilada"),
        ("discoveredCheck", "Busca un jaque descubierto"),
        ("discoveredAttack", "Busca un ataque descubierto"),
        ("doubleCheck", "Busca la posibilidad de un jaque doble"),
        ("capturingDefender", "Busca eliminar una pieza defensora"),
        ("deflection", "Busca desviar una pieza defensora"),
        ("attraction", "Busca atraer una pieza enemiga a una casilla vulnerable"),
        ("clearance", "Busca despejar una línea o una casilla clave"),
        ("interference", "Busca cortar la coordinación de las piezas defensoras"),
        ("xRayAttack", "Busca un ataque de rayos X"),
        ("hangingPiece", "Busca una pieza enemiga sin defensa suficiente"),
        ("trappedPiece", "Busca cómo encerrar una pieza enemiga"),
        ("intermezzo", "Antes de la jugada evidente, busca una jugada intermedia más fuerte"),
        ("sacrifice", "Considera un sacrificio táctico"),
        ("quietMove", "No busques solo jaques o capturas: considera una jugada tranquila"),
        ("defensiveMove", "Busca la defensa más precisa"),
        ("underPromotion", "Considera promocionar a una pieza distinta de la dama"),
        ("promotion", "Busca una secuencia que permita promocionar un peón"),
        ("enPassant", "Comprueba si la captura al paso es decisiva"),
        ("castling", "Comprueba si el enroque cumple una función táctica"),
        ("advancedPawn", "Busca cómo aprovechar el peón avanzado"),
        ("passedPawn", "Busca cómo aprovechar el peón pasado"),
        ("attackingF2F7", "Busca cómo explotar la debilidad de f2 o f7"),
        ("exposedKing", "Busca cómo aprovechar la exposición del rey"),
        ("kingsideAttack", "Busca cómo intensificar el ataque en el flanco de rey"),
        ("queensideAttack", "Busca cómo intensificar el ataque en el flanco de dama"),
        ("zugzwang", "Busca una jugada que deje al rival sin una respuesta útil"),
        ("backRankMate", "Busca una red de mate aprovechando la última fila"),
        ("smotheredMate", "Busca encerrar al rey con sus propias piezas y aprovechar el caballo"),
        ("anastasiaMate", "Busca coordinar una pieza de largo alcance y un caballo contra el rey"),
        ("arabianMate", "Busca coordinar torre y caballo alrededor del rey"),
        ("bodenMate", "Busca una red de mate basada en diagonales cruzadas"),
        ("doubleBishopMate", "Busca cómo coordinar los dos alfiles contra el rey"),
    )
    _TEMAS_MATE = frozenset({
        "mate",
        "mateIn1",
        "mateIn2",
        "mateIn3",
        "mateIn4",
        "mateIn5",
    })
    _PISTAS_MATE_ESPECIFICAS = frozenset({
        "backRankMate",
        "smotheredMate",
        "anastasiaMate",
        "arabianMate",
        "bodenMate",
        "doubleBishopMate",
    })

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
        self._pista_usada = False
        self._pista_usada_antes_resultado = False
        self._btn_pista: BotonTextoAdaptativo | None = None
        self._panel_pista: BoxLayout | None = None
        self._lbl_pista: TextoAdaptativo | None = None
        self._lbl_temas_pista: TextoAdaptativo | None = None
        self._img_guia: Image | None = None
        super().__init__(habilitar_visor_solucion=False, **kwargs)
        self._configurar_controles_solucion()
        self._configurar_pista()
        self._reiniciar_pista()
        self.actualizar_piezas_visuales()

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
            size_hint_x=0.94,
            size_hint_y=None,
            height=dp(50),
            spacing=dp(8),
            pos_hint={"center_x": 0.5},
        )
        self._btn_mostrar_solucion = BotonTextoAdaptativo(
            text="MOSTRAR SOLUCION",
            size_hint_x=None,
            width=0,
            opacity=0,
            disabled=True,
            font_size_max="16sp",
            margen_horizontal=dp(6),
            background_color=(1, 1, 1, 1),
            background_normal="assets/ui/button.png",
            background_down="assets/ui/button_down.png",
            border=(0, 0, 0, 0),
            bold=True,
        )
        self._btn_mostrar_solucion.bind(on_release=self.mostrar_solucion)

        self._btn_siguiente.size_hint_x = 1
        self._btn_siguiente.size_hint_y = 1
        self._btn_siguiente.font_size_max = sp(14)
        self._fila_acciones.add_widget(self._btn_mostrar_solucion)
        self._fila_acciones.add_widget(self._btn_siguiente)
        panel.add_widget(self._fila_acciones, index=indice_original)

        self._fila_navegacion = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )
        self._btn_solucion_anterior = BotonTextoAdaptativo(
            text="<",
            size_hint_x=0.25,
            background_color=(1, 1, 1, 1),
            background_normal="assets/ui/button.png",
            background_down="assets/ui/button_down.png",
            border=(0, 0, 0, 0),
            bold=True,
        )
        self._btn_solucion_anterior.bind(on_release=self.retroceder_solucion)

        self._lbl_paso_solucion = TextoAdaptativo(
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

        self._btn_solucion_siguiente = BotonTextoAdaptativo(
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

    def _configurar_pista(self) -> None:
        """Prepara la información y la fila de acciones de la práctica."""
        panel = self.ids.panel_inferior
        panel.spacing = dp(5)
        panel.padding = (0, dp(8), 0, 0)

        estado = self.ids.lbl_estado
        estado.font_name = DEFAULT_FONT
        estado.font_size_max = sp(18)
        estado.font_size_min = sp(14)

        # Título y estado comparten la zona superior original. De este modo
        # TU TURNO no reduce la altura disponible para el tablero.
        mision = self.ids.lbl_mision
        if estado.parent is panel:
            indice_mision = self.children.index(mision)
            panel.remove_widget(estado)
            self.remove_widget(mision)

            self._cabecera_practica = BoxLayout(
                orientation="vertical",
                size_hint_y=0.15,
                spacing=dp(2),
                padding=(0, 0, 0, dp(12)),
            )

            mision.size_hint_y = 0.62
            estado.size_hint_y = 0.38

            self._cabecera_practica.add_widget(mision)
            self._cabecera_practica.add_widget(estado)
            self.add_widget(self._cabecera_practica, index=indice_mision)

        self.ids.lbl_info.size_hint_y = None
        self.ids.lbl_info.height = dp(30)
        self.ids.lbl_info.font_name = DEFAULT_FONT
        self.ids.lbl_info.font_size_max = sp(14)
        self.ids.lbl_info.font_size_min = sp(11)

        self.ids.lbl_temas.text = ""
        self.ids.lbl_temas.size_hint_y = None
        self.ids.lbl_temas.height = 0
        self.ids.lbl_temas.opacity = 0

        self._panel_pista = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(92),
            padding=(dp(8), dp(3), dp(8), dp(3)),
            spacing=dp(5),
        )

        self._img_guia = Image(
            source="assets/ui/mascota_torre_guia.png",
            size_hint_x=0.24,
            allow_stretch=True,
            keep_ratio=True,
        )

        bocadillo = BocadilloGuia(size_hint_x=0.76)
        contenido_bocadillo = BoxLayout(
            orientation="vertical",
            padding=(dp(20), dp(7), dp(9), dp(6)),
            spacing=dp(2),
        )

        self._lbl_pista = TextoAdaptativo(
            text="",
            font_name="Michroma",
            font_size=sp(11),
            font_size_max=sp(11),
            font_size_min=sp(8),
            color=(0.10, 0.12, 0.16, 1),
            bold=False,
            halign="left",
            valign="middle",
            size_hint_y=0.72,
        )
        self._lbl_pista.bind(
            size=lambda instance, size: setattr(instance, "text_size", size)
        )

        self._lbl_temas_pista = TextoAdaptativo(
            text="",
            font_name="Michroma",
            font_size=sp(8),
            font_size_max=sp(8),
            font_size_min=sp(6),
            color=(0.0, 0.55, 0.55, 1),
            bold=False,
            halign="left",
            valign="middle",
            size_hint_y=0.28,
        )
        self._lbl_temas_pista.bind(
            size=lambda instance, size: setattr(instance, "text_size", size)
        )

        contenido_bocadillo.add_widget(self._lbl_pista)
        contenido_bocadillo.add_widget(self._lbl_temas_pista)
        bocadillo.add_widget(contenido_bocadillo)

        self._panel_pista.add_widget(self._img_guia)
        self._panel_pista.add_widget(bocadillo)

        indice_panel = panel.children.index(self._fila_acciones) + 1
        panel.add_widget(self._panel_pista, index=indice_panel)

        self._btn_pista = BotonTextoAdaptativo(
            text="PISTA",
            size_hint_x=1,
            size_hint_y=1,
            font_size_max=sp(14),
            margen_horizontal=dp(6),
            background_color=(1, 1, 1, 1),
            background_normal="assets/ui/button.png",
            background_down="assets/ui/button_down.png",
            background_disabled_normal="assets/ui/button.png",
            disabled_color=(1, 1, 1, 1),
            border=(0, 0, 0, 0),
            bold=True,
        )
        self._btn_pista.bind(on_release=self.mostrar_pista)
        self._btn_pista.disabled = True
        self._btn_pista.opacity = 0.6

        # BoxLayout guarda los hijos en orden inverso. Insertarlo al final
        # mantiene visualmente PISTA a la izquierda y SIGUIENTE a la derecha.
        self._fila_acciones.add_widget(
            self._btn_pista,
            index=len(self._fila_acciones.children),
        )

    def _reiniciar_pista(self) -> None:
        """Restaura el personaje guía para el puzzle activo."""
        self._pista_usada = False
        self._pista_usada_antes_resultado = False

        if self._panel_pista is not None:
            self._panel_pista.height = dp(92)
            self._panel_pista.opacity = 1

        self._actualizar_guia_puzzle()

        if self._btn_pista is None:
            return

        self._btn_pista.text = "PISTA"
        self._btn_pista.size_hint_x = 1
        self._btn_pista.opacity = 0.6
        self._btn_pista.disabled = True

    def _actualizar_guia_puzzle(self) -> None:
        """Muestra desde el inicio el enunciado generado a partir de los temas."""
        info = self.gestor_ajedrez.info_puzzle or {}
        temas_crudos = str(info.get("themes", "") or "").strip()

        if self._lbl_pista is not None:
            self._lbl_pista.text = (
                self._construir_pista(temas_crudos)
                if info
                else ""
            )

        if self._lbl_temas_pista is not None:
            self._lbl_temas_pista.text = (
                f"TEMAS: {temas_crudos}"
                if temas_crudos
                else ("TEMAS: --" if info else "")
            )

    def mostrar_pista(self, *_args) -> None:
        """Reserva el botón para una futura pista real."""
        return

    def _construir_pista(self, temas_crudos: str) -> str:
        """Construye una pista breve usando solo temas con valor pedagógico."""
        temas = set((temas_crudos or "").split())

        tema_motivo = None
        frase = "Busca una jugada precisa"
        for tema, pista in self._PISTAS_MOTIVO:
            if tema in temas:
                tema_motivo = tema
                frase = pista
                break

        if (
            temas & self._TEMAS_MATE
            and tema_motivo not in self._PISTAS_MATE_ESPECIFICAS
        ):
            frase += " que conduzca al mate"
        elif "crushing" in temas:
            frase += " que te permita obtener una ventaja decisiva"
        elif "advantage" in temas:
            frase += " que te permita obtener ventaja"
        elif "equality" in temas:
            frase += " que te permita igualar la posición"

        if "endgame" in temas:
            frase += " en este final"
        elif "middlegame" in temas:
            frase += " en esta posición de medio juego"
        elif "opening" in temas:
            frase += " en esta apertura"

        return frase.rstrip(".") + "."

    def _mostrar_acciones_fallo(self) -> None:
        """Sustituye Pista por Mostrar solución tras una derrota."""
        if self._btn_pista is not None:
            self._btn_pista.size_hint_x = None
            self._btn_pista.width = 0
            self._btn_pista.opacity = 0
            self._btn_pista.disabled = True

        self._btn_mostrar_solucion.size_hint_x = 1
        self._btn_mostrar_solucion.opacity = 1
        self._btn_mostrar_solucion.disabled = False
        self._btn_siguiente.size_hint_x = 1
        self._btn_siguiente.text = "SIGUIENTE PUZZLE"

    def _ocultar_boton_solucion(self) -> None:
        """Oculta Mostrar solución y recupera la fila normal de práctica."""
        self._btn_mostrar_solucion.size_hint_x = None
        self._btn_mostrar_solucion.width = 0
        self._btn_mostrar_solucion.opacity = 0
        self._btn_mostrar_solucion.disabled = True
        self._btn_siguiente.size_hint_x = 1

        if self._btn_pista is not None:
            self._btn_pista.size_hint_x = 1
            self._btn_pista.opacity = 0.6
            self._btn_pista.disabled = True

    def _restablecer_panel_practica(self) -> None:
        """Abandona la revisión y restaura el panel normal de práctica."""
        self._modo_solucion = False
        self._tablero_revision = None
        self._movimientos_revision = []
        self._indice_revision = 0
        self._animacion_solucion_activa = False

        if self._fila_navegacion.parent is not None:
            self._fila_navegacion.parent.remove_widget(self._fila_navegacion)

        self.ids.lbl_info.size_hint_y = None
        self.ids.lbl_info.height = dp(28)
        self.ids.lbl_info.opacity = 1
        self.ids.lbl_temas.size_hint_y = None
        self.ids.lbl_temas.height = 0
        self.ids.lbl_temas.opacity = 0

        self._reiniciar_pista()
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

        if self._panel_pista is not None:
            self._panel_pista.height = 0
            self._panel_pista.opacity = 0

        if self._btn_pista is not None:
            self._btn_pista.size_hint_x = None
            self._btn_pista.width = 0
            self._btn_pista.opacity = 0
            self._btn_pista.disabled = True

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

    def _obtener_linea_rating_dificultad(self) -> str:
        """Devuelve rating local y dificultad visible sin metadatos técnicos."""
        info = self.gestor_ajedrez.info_puzzle or {}
        estado_local = self.perfil_actual["practica_lecciones"][self.id_leccion]
        rating_local = float(estado_local.get("rating", 0.0))
        plies = int(info.get("plies", len(info.get("moves", []))))
        dificultad_visible = CalculadorRatingTactico.obtener_dificultad_visible(plies)
        return f"RATING: {int(round(rating_local))}% · {dificultad_visible}"

    def mostrar_temas_traducidos(self) -> None:
        """Mantiene ocultos los temas y refresca rating y dificultad."""
        self.ids.lbl_temas.text = ""
        self.ids.lbl_info.text = self._obtener_linea_rating_dificultad()

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

        if victoria and self._pista_usada_antes_resultado:
            if id_puzzle and id_puzzle not in estado_local["resueltos"]:
                estado_local["resueltos"].append(id_puzzle)
            self.gestor_perfiles.guardar_perfil(self.perfil_actual)
            return 0.0, rating_actual

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
            if self._btn_pista is not None:
                self._btn_pista.disabled = True

    def volver_menu(self) -> None:
        """Abandona la práctica y refresca el rating del menú de la lección."""
        app = App.get_running_app()
        menu_leccion = app.sm.get_screen("menu_leccion")
        menu_leccion.refrescar_menu_principal()
        app.sm.current = "menu_leccion"

    def actualizar_piezas_visuales(self) -> None:
        """Sincroniza tablero y muestra solo información útil para la práctica."""
        super().actualizar_piezas_visuales()

        info = self.gestor_ajedrez.info_puzzle
        if info:
            self.ids.lbl_mision.text = self._obtener_titulo_superior()
            self.ids.lbl_info.text = self._obtener_linea_rating_dificultad()
            self.ids.lbl_temas.text = ""

            es_blancas = self.gestor_ajedrez.board.turn == chess.WHITE
            color_turno = (
                "[color=#ffffff]BLANCAS[/color]"
                if es_blancas
                else "[color=#ff6b6b]NEGRAS[/color]"
            )
            if self.gestor_ajedrez.estado_puzzle == "JUGANDO":
                self.ids.lbl_estado.text = f"TU TURNO: {color_turno}"

            self._actualizar_guia_puzzle()

    def formatear_resultado_puzzle(
        self,
        victoria: bool,
        variacion: float,
        nueva_puntuacion: float,
    ) -> str:
        """Genera el feedback visible del rating táctico de la lección."""
        rating_visible = int(round(nueva_puntuacion))
        if victoria and self._pista_usada_antes_resultado:
            return (
                f"CORRECTO · PISTA UTILIZADA · "
                f"RATING: {rating_visible}% (SIN CAMBIO)"
            )

        rango = self._texto_sin_acentos(
            CalculadorRatingTactico.obtener_rango(nueva_puntuacion)
        ).upper()
        return (
            f"{'CORRECTO' if victoria else 'INCORRECTO'} "
            f"RATING: {rating_visible}% "
            f"({variacion:+.1f}) · {rango}"
        )

    def formatear_info_resultado(self, info: dict) -> str:
        """Mantiene rating y dificultad en lugar del identificador del puzzle."""
        return self._obtener_linea_rating_dificultad()
