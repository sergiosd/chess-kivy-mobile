import pygame
import sys
import math
import os

from perfil_manager import PerfilManager
from ui_mvp import UIMVP
from puzzle_manager import PuzzleManager
from chess_manager import ChessManager
from chess_renderer import ChessRenderer

ANCHO = 540
ALTO = 960


def calcular_variacion_elo(elo_jugador, elo_puzzle, victoria):
    E = 1.0 / (1.0 + math.pow(10, (elo_puzzle - elo_jugador) / 400.0))
    S = 1.0 if victoria else 0.0
    K = 42.0
    return K * (S - E)


def cargar_sonido(nombre):
    ruta = os.path.join("assets", "sounds", nombre)
    return pygame.mixer.Sound(ruta) if os.path.exists(ruta) else None


def main():
    pygame.init()
    pygame.mixer.init()

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Ajedrez MVP - Entrenamiento Táctico Móvil")
    reloj = pygame.time.Clock()

    ui = UIMVP(ANCHO, ALTO)
    gestor_perfiles = PerfilManager()
    gestor_puzzles = PuzzleManager()
    gestor_ajedrez = ChessManager()
    render_ajedrez = ChessRenderer(ANCHO, ALTO)

    snd_select = cargar_sonido("select.wav")
    snd_move = cargar_sonido("move.wav")
    snd_win = cargar_sonido("win.wav")
    snd_lose = cargar_sonido("lose.wav")

    ultimo_usuario = gestor_perfiles.obtener_ultimo_usuario()
    estado_app = "LOGIN" if ultimo_usuario else "NUEVO_USUARIO"

    perfil_activo = None
    perspectiva_blancas = True
    variacion_reciente_elo = 0

    inputs_nuevo = {"nombre": "", "elo": "1000"}
    input_activo = "nombre"

    corriendo = True
    while corriendo:
        pos_raton = pygame.mouse.get_pos()

        # --- FONDO DINÁMICO ---
        # Enviamos el ELO actual si hay un perfil cargado para calcular el color
        elo_actual = perfil_activo["elo"] if perfil_activo else None
        ui.dibujar_fondo(pantalla, elo_actual)

        btn_ancho, btn_alto = 280, 60
        centro_x = (ANCHO - btn_ancho) // 2

        btn_entrar = pygame.Rect(centro_x, 380, btn_ancho, btn_alto)
        btn_crear_nuevo = pygame.Rect(centro_x, 460, btn_ancho, btn_alto)

        btn_empezar = pygame.Rect(centro_x, 380, btn_ancho, btn_alto)
        btn_salir = pygame.Rect(centro_x, 460, btn_ancho, btn_alto)

        btn_continuar = pygame.Rect(centro_x, 780, btn_ancho, btn_alto)
        btn_menu = pygame.Rect(centro_x, 860, btn_ancho, btn_alto)

        rect_input_nombre = pygame.Rect(centro_x, 300, btn_ancho, 50)
        rect_input_elo = pygame.Rect(centro_x, 420, btn_ancho, 50)
        btn_guardar_perfil = pygame.Rect(centro_x, 520, btn_ancho, btn_alto)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False

            if estado_app == "LOGIN":
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if btn_entrar.collidepoint(evento.pos):
                        if snd_select: snd_select.play()
                        perfil_activo = gestor_perfiles.cargar_perfil(ultimo_usuario)
                        estado_app = "MENU"
                    elif btn_crear_nuevo.collidepoint(evento.pos):
                        if snd_select: snd_select.play()
                        estado_app = "NUEVO_USUARIO"

            elif estado_app == "NUEVO_USUARIO":
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if btn_guardar_perfil.collidepoint(evento.pos):
                        if snd_select: snd_select.play()
                        nombre = inputs_nuevo["nombre"].strip()
                        if nombre:
                            elo = int(inputs_nuevo["elo"]) if inputs_nuevo[
                                "elo"].isdigit() else 1000
                            perfil_activo = {"nombre": nombre, "elo": elo, "resueltos": []}
                            gestor_perfiles.guardar_perfil(perfil_activo)
                            estado_app = "MENU"
                    elif rect_input_nombre.collidepoint(evento.pos):
                        input_activo = "nombre"
                        if snd_select: snd_select.play()
                    elif rect_input_elo.collidepoint(evento.pos):
                        input_activo = "elo"
                        if snd_select: snd_select.play()

                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_TAB:
                        input_activo = "elo" if input_activo == "nombre" else "nombre"
                    elif evento.key == pygame.K_RETURN:
                        nombre = inputs_nuevo["nombre"].strip()
                        if nombre:
                            elo = int(inputs_nuevo["elo"]) if inputs_nuevo[
                                "elo"].isdigit() else 1000
                            perfil_activo = {"nombre": nombre, "elo": elo, "resueltos": []}
                            gestor_perfiles.guardar_perfil(perfil_activo)
                            estado_app = "MENU"
                    elif evento.key == pygame.K_BACKSPACE:
                        inputs_nuevo[input_activo] = inputs_nuevo[input_activo][:-1]
                    elif evento.unicode.isprintable():
                        inputs_nuevo[input_activo] += evento.unicode

            elif estado_app == "MENU":
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if btn_salir.collidepoint(evento.pos):
                        if snd_select: snd_select.play()
                        corriendo = False
                    elif btn_empezar.collidepoint(evento.pos):
                        if snd_select: snd_select.play()

                        ui.dibujar_fondo(pantalla, elo_actual)
                        ui.dibujar_texto_centrado(pantalla, "Buscando tácticas...", ALTO // 2,
                                                  es_titulo=True)
                        pygame.display.flip()

                        puzzle_nuevo = gestor_puzzles.obtener_puzzle_aleatorio(perfil_activo["elo"],
                                                                               perfil_activo[
                                                                                   "resueltos"])

                        if puzzle_nuevo:
                            gestor_ajedrez.cargar_puzzle(puzzle_nuevo)
                            import chess
                            perspectiva_blancas = (gestor_ajedrez.board.turn != chess.WHITE)
                            mov_enemigo = gestor_ajedrez.ejecutar_movimiento_enemigo()
                            render_ajedrez.animar_movimiento(pantalla, gestor_ajedrez.board,
                                                             mov_enemigo, perspectiva_blancas,
                                                             reloj)
                            estado_app = "JUGANDO"
                        else:
                            print("No se encontraron puzles para este ELO.")

            elif estado_app == "JUGANDO":
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    casilla_clic = render_ajedrez.obtener_casilla_desde_raton(pos_raton,
                                                                              perspectiva_blancas)
                    if casilla_clic:
                        if gestor_ajedrez.casilla_seleccionada:
                            mov_str = gestor_ajedrez.casilla_seleccionada + casilla_clic
                            exito = gestor_ajedrez.intentar_movimiento_jugador(casilla_clic)

                            if exito:
                                render_ajedrez.animar_movimiento(pantalla, gestor_ajedrez.board,
                                                                 mov_str, perspectiva_blancas,
                                                                 reloj)
                                if snd_move: snd_move.play()

                                if gestor_ajedrez.estado_puzzle == "JUGANDO":
                                    pygame.time.delay(300)
                                    mov_resp = gestor_ajedrez.ejecutar_movimiento_enemigo()
                                    render_ajedrez.animar_movimiento(pantalla, gestor_ajedrez.board,
                                                                     mov_resp, perspectiva_blancas,
                                                                     reloj)
                                    if snd_move: snd_move.play()
                            else:
                                gestor_ajedrez.seleccionar_casilla(casilla_clic)
                        else:
                            gestor_ajedrez.seleccionar_casilla(casilla_clic)

                if gestor_ajedrez.estado_puzzle in ["VICTORIA", "DERROTA"]:
                    victoria = (gestor_ajedrez.estado_puzzle == "VICTORIA")

                    if victoria and snd_win:
                        snd_win.play()
                    elif not victoria and snd_lose:
                        snd_lose.play()

                    elo_puzzle = gestor_ajedrez.info_puzzle['rating']
                    variacion_reciente_elo = calcular_variacion_elo(perfil_activo["elo"],
                                                                    elo_puzzle, victoria)

                    perfil_activo["elo"] += variacion_reciente_elo
                    perfil_activo["resueltos"].append(gestor_ajedrez.info_puzzle['id'])
                    gestor_perfiles.guardar_perfil(perfil_activo)
                    estado_app = "RESULTADO"

            elif estado_app == "RESULTADO":
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if btn_menu.collidepoint(evento.pos):
                        if snd_select: snd_select.play()
                        estado_app = "MENU"
                    elif btn_continuar.collidepoint(evento.pos):
                        if snd_select: snd_select.play()

                        ui.dibujar_fondo(pantalla, elo_actual)
                        ui.dibujar_texto_centrado(pantalla, "Desplegando escenario...", ALTO // 2,
                                                  es_titulo=True)
                        pygame.display.flip()

                        puzzle_nuevo = gestor_puzzles.obtener_puzzle_aleatorio(perfil_activo["elo"],
                                                                               perfil_activo[
                                                                                   "resueltos"])
                        if puzzle_nuevo:
                            gestor_ajedrez.cargar_puzzle(puzzle_nuevo)
                            import chess
                            perspectiva_blancas = (gestor_ajedrez.board.turn != chess.WHITE)
                            mov_enemigo = gestor_ajedrez.ejecutar_movimiento_enemigo()
                            render_ajedrez.animar_movimiento(pantalla, gestor_ajedrez.board,
                                                             mov_enemigo, perspectiva_blancas,
                                                             reloj)
                            estado_app = "JUGANDO"

        if estado_app == "LOGIN":
            ui.dibujar_texto_centrado(pantalla, "SALA DE MANDO", 200, es_titulo=True,
                                      color=ui.COLOR_TEXTO)
            ui.dibujar_texto_centrado(pantalla, f"Último Comandante: {ultimo_usuario}", 260,
                                      color=ui.COLOR_ACCENTO)
            ui.dibujar_boton(pantalla, btn_entrar, "Iniciar Sesión", pos_raton)
            ui.dibujar_boton(pantalla, btn_crear_nuevo, "Crear Nuevo Perfil", pos_raton,
                             color_especial=(72, 84, 96))

        elif estado_app == "NUEVO_USUARIO":
            ui.dibujar_texto_centrado(pantalla, "NUEVO PERFIL", 150, es_titulo=True,
                                      color=ui.COLOR_ACCENTO)
            ui.dibujar_texto_centrado(pantalla, "Nombre del Comandante:", 260)
            ui.dibujar_input(pantalla, rect_input_nombre, inputs_nuevo["nombre"],
                             input_activo == "nombre")
            ui.dibujar_texto_centrado(pantalla, "ELO Inicial (Nivel):", 380)
            ui.dibujar_input(pantalla, rect_input_elo, inputs_nuevo["elo"], input_activo == "elo")
            ui.dibujar_boton(pantalla, btn_guardar_perfil, "Confirmar Reclutamiento", pos_raton,
                             color_especial=(0, 184, 148))

        elif estado_app == "MENU":
            ui.dibujar_texto_centrado(pantalla, f"¡Hola, {perfil_activo['nombre']}!", 200,
                                      es_titulo=True)
            ui.dibujar_texto_centrado(pantalla, "NIVEL DE HABILIDAD", 280, color=(160, 200, 220))
            ui.dibujar_texto_centrado(pantalla, f"{int(perfil_activo['elo'])} ELO", 320,
                                      es_titulo=True, color=ui.COLOR_ACCENTO)
            ui.dibujar_boton(pantalla, btn_empezar, "INICIAR ENTRENAMIENTO", pos_raton)
            ui.dibujar_boton(pantalla, btn_salir, "Salir al Sistema", pos_raton,
                             color_especial=(72, 84, 96))

        elif estado_app == "JUGANDO" or estado_app == "RESULTADO":
            render_ajedrez.dibujar_tablero(pantalla, gestor_ajedrez.board,
                                           gestor_ajedrez.casilla_seleccionada,
                                           gestor_ajedrez.movimientos_validos,
                                           perspectiva_blancas)

            if estado_app == "RESULTADO" and gestor_ajedrez.estado_puzzle == "DERROTA":
                mov_fallido = gestor_ajedrez.movimiento_fallado
                if len(mov_fallido) >= 4:
                    render_ajedrez.dibujar_flecha(pantalla, mov_fallido[:2], mov_fallido[2:4],
                                                  perspectiva_blancas)

            # CORRECCIÓN DE OVERLAPPING:
            # Aumentamos radicalmente el margen inferior para saltar todo el marco decorativo
            y_info = render_ajedrez.y_tablero + render_ajedrez.ancho_tablero + 85

            info = gestor_ajedrez.info_puzzle

            if estado_app == "JUGANDO":
                titulo_puzzle = f"Misión: ELO {info['rating']}"
                ui.dibujar_texto_centrado(pantalla, titulo_puzzle, 60, es_titulo=True,
                                          color=ui.COLOR_ACCENTO)

                color_turno = ui.COLOR_TEXTO if perspectiva_blancas else ui.COLOR_ALERTA
                bando = "BLANCAS" if perspectiva_blancas else "NEGRAS"
                ui.dibujar_texto_centrado(pantalla, f"Tu turno: {bando}", y_info, es_titulo=True,
                                          color=color_turno)

                ui.dibujar_texto_centrado(pantalla, f"Tu nivel: {int(perfil_activo['elo'])}",
                                          y_info + 40, color=(180, 210, 230))
                ui.dibujar_texto_centrado(pantalla,
                                          f"Popularidad: {info['popularity']}%  |  ID: {info['id']}",
                                          y_info + 70, color=(140, 160, 180))

            else:
                victoria = (gestor_ajedrez.estado_puzzle == "VICTORIA")
                titulo_res = "¡TACTICA BRILLANTE!" if victoria else "¡MOVIMIENTO ERRÓNEO!"
                color_res = ui.COLOR_EXITO if victoria else ui.COLOR_ALERTA

                ui.dibujar_texto_centrado(pantalla, titulo_res, 60, es_titulo=True, color=color_res)

                desplazamiento = 0
                if not victoria:
                    mov_fallido = gestor_ajedrez.movimiento_fallado.upper()
                    ui.dibujar_texto_centrado(pantalla,
                                              f"Debiste jugar: {mov_fallido[:2]}-{mov_fallido[2:]}",
                                              y_info, es_titulo=True, color=ui.COLOR_ALERTA)
                    desplazamiento = 40

                signo = "+" if variacion_reciente_elo >= 0 else ""
                texto_elo = f"Nivel: {int(perfil_activo['elo'])} ({signo}{int(variacion_reciente_elo)})"

                ui.dibujar_texto_centrado(pantalla, texto_elo, y_info + desplazamiento,
                                          es_titulo=True, color=ui.COLOR_ACCENTO)

                temas_lista = info['themes'].split(" ")[:3]
                txt_temas = " • ".join(temas_lista).replace("_", " ").title()
                ui.dibujar_texto_centrado(pantalla, txt_temas, y_info + desplazamiento + 35,
                                          color=(150, 180, 200))

                ui.dibujar_boton(pantalla, btn_continuar, "Siguiente Misión", pos_raton,
                                 color_especial=(0, 184, 148))
                ui.dibujar_boton(pantalla, btn_menu, "Volver a la Base", pos_raton,
                                 color_especial=(72, 84, 96))

        pygame.display.flip()
        reloj.tick(60)


if __name__ == "__main__":
    main()