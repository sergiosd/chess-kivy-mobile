from __future__ import annotations

import unicodedata

import chess
from kivy.app import App

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
        super().__init__(**kwargs)

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
            self.ids.btn_siguiente.text = "SIGUIENTE PUZZLE"
        else:
            self.ids.lbl_estado.text = "MODULO COMPLETADO"
            self.ids.lbl_estado.color = [0, 1, 0, 1]
            self.ids.btn_siguiente.disabled = True

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
