"""
Módulo de procesamiento de texto para paginación automática.

Automatiza la inserción de directivas de control para el motor de Kivy.
Calcula el peso visual masivo de los tableros FEN para evitar
el desbordamiento de los componentes en la interfaz gráfica.
"""

import os
import re

import os
import re


def auto_paginar_leccion(ruta_entrada: str, ruta_salida: str, limite_palabras: int = 120) -> None:
    """
    Forja un archivo de lección paginado dinámicamente evaluando el peso léxico real.

    Intercepta las cabeceras de los capítulos y fuerza un salto de página absoluto
    antes de saturar la memoria gráfica de Kivy. Cuantifica el volumen de
    palabras integrando el costo visual de los bloques tácticos interactivos.

    Args:
        ruta_entrada (str): Origen del texto crudo.
        ruta_salida (str): Destino de la lección purificada.
        limite_palabras (int): Capacidad máxima tolerada por la vista gráfica.
    """
    if not os.path.exists(ruta_entrada):
        print(f"Error fatal: El archivo {ruta_entrada} ha desaparecido del disco.")
        return

    with open(ruta_entrada, 'r', encoding='utf-8') as archivo:
        texto_crudo = archivo.read()

    lineas_crudas = texto_crudo.split('\n')
    texto_preprocesado = []

    for linea in lineas_crudas:
        if linea.strip().startswith('## '):
            texto_preprocesado.append('[PAGINA]')
        texto_preprocesado.append(linea)

    texto_crudo = '\n'.join(texto_preprocesado)
    texto_crudo = re.sub(r'\[PAGINA\]\s*\[PAGINA\]', '[PAGINA]', texto_crudo)

    bloques_maestros = texto_crudo.split('[PAGINA]')
    paginas_procesadas = []
    PESO_TABLERO = 75

    for bloque in bloques_maestros:
        patron = re.compile(r'(\s+|\[FEN:.*?\]|\[PUZZLE\].*?\[FIN\])', re.DOTALL)
        fragmentos = patron.split(bloque)

        texto_pagina_actual = []
        contador_palabras = 0

        for frag in fragmentos:
            if not frag:
                continue

            if frag.isspace():
                if texto_pagina_actual:
                    texto_pagina_actual.append(frag)
            elif frag.startswith('[FEN:') or frag.startswith('[PUZZLE]'):
                if contador_palabras > 0 and contador_palabras + PESO_TABLERO > limite_palabras:
                    paginas_procesadas.append("".join(texto_pagina_actual).strip())
                    texto_pagina_actual = [frag]
                    contador_palabras = PESO_TABLERO
                else:
                    texto_pagina_actual.append(frag)
                    contador_palabras += PESO_TABLERO
            else:
                texto_pagina_actual.append(frag)
                contador_palabras += 1

                if contador_palabras >= limite_palabras:
                    paginas_procesadas.append("".join(texto_pagina_actual).strip())
                    texto_pagina_actual = []
                    contador_palabras = 0

        texto_restante = "".join(texto_pagina_actual).strip()
        if texto_restante:
            paginas_procesadas.append(texto_restante)

    paginas_procesadas = [p for p in paginas_procesadas if p.strip()]
    resultado_final = "\n\n[PAGINA]\n\n".join(paginas_procesadas)

    with open(ruta_salida, 'w', encoding='utf-8') as archivo_salida:
        archivo_salida.write(resultado_final)

    print(f"Paginación completada con éxito. Archivo protegido en: {ruta_salida}")


if __name__ == "__main__":
    # Ejecución aislada. Modifica las rutas según el sistema de archivos.
    ruta_origen = os.path.join("lecciones", "tactica_indefensa_teoria.txt")
    ruta_destino = os.path.join("lecciones", "tactica_indefensa_teoria.txt")

    # Creamos un archivo dummy de prueba si no existe la estructura
    if not os.path.exists(ruta_origen):
        os.makedirs("lecciones", exist_ok=True)
        with open(ruta_origen, 'w', encoding='utf-8') as f:
            f.write("Texto inicial...\n\n[FEN:8/8/8/8/8/8/8/8 w - - 0 1]\n\nMás teoría.")

    auto_paginar_leccion(ruta_origen, ruta_destino, 150)