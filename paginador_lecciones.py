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

    Castiga severamente el tamaño colosal de las cabeceras Markdown y listas.
    Asigna pesos virtuales a los elementos que consumen exceso de píxeles verticales
    para evitar el desbordamiento del Label en Kivy.

    Args:
        ruta_entrada (str): Origen del papiro digital crudo.
        ruta_salida (str): Destino de la lección purificada y formateada.
        limite_palabras (int): Capacidad máxima tolerada por la vista gráfica.
    """
    if not os.path.exists(ruta_entrada):
        print(f"Error letal: El archivo {ruta_entrada} ha desaparecido del disco.")
        return

    with open(ruta_entrada, 'r', encoding='utf-8') as archivo:
        texto_crudo = archivo.read()

    bloques_maestros = texto_crudo.split('[PAGINA]')
    paginas_procesadas = []

    PESO_TABLERO = 50

    for bloque in bloques_maestros:
        # Partimos por líneas físicas para poder detectar la sintaxis al inicio
        lineas = bloque.split('\n')
        texto_pagina_actual = []
        contador_palabras = 0

        for linea in lineas:
            peso_fantasma = 0
            linea_limpia = linea.strip()

            # Castigamos los píxeles extra convirtiéndolos en "palabras virtuales"
            if linea_limpia.startswith('# '):
                peso_fantasma = 30
            elif linea_limpia.startswith('## '):
                peso_fantasma = 20
            elif linea_limpia.startswith('### '):
                peso_fantasma = 15
            elif linea_limpia.startswith('- ') or linea_limpia.startswith('* '):
                peso_fantasma = 5

            # El motor léxico original
            patron = re.compile(r'(\s+|\[FEN:.*?\]|\[PUZZLE\].*?\[FIN\])', re.DOTALL)
            fragmentos = patron.split(linea)

            linea_buffer = []

            for frag in fragmentos:
                if not frag:
                    continue

                incremento = 0
                if frag.startswith('[FEN:') or frag.startswith('[PUZZLE]'):
                    incremento = PESO_TABLERO
                elif not frag.isspace():
                    incremento = 1

                # La primera palabra útil de la línea se traga el peso fantasma del heading
                if incremento > 0 and peso_fantasma > 0:
                    incremento += peso_fantasma
                    peso_fantasma = 0

                # Comprobamos si reventamos el límite
                if incremento > 0 and (contador_palabras + incremento > limite_palabras) and (
                        texto_pagina_actual or linea_buffer):
                    if linea_buffer:
                        texto_pagina_actual.append("".join(linea_buffer))

                    paginas_procesadas.append("\n".join(texto_pagina_actual).strip())
                    texto_pagina_actual = []
                    linea_buffer = [frag]
                    contador_palabras = incremento
                else:
                    linea_buffer.append(frag)
                    if incremento > 0:
                        contador_palabras += incremento

            if linea_buffer:
                texto_pagina_actual.append("".join(linea_buffer))

        texto_restante = "\n".join(texto_pagina_actual).strip()
        if texto_restante:
            paginas_procesadas.append(texto_restante)

    resultado_final = "\n\n[PAGINA]\n\n".join(paginas_procesadas)

    with open(ruta_salida, 'w', encoding='utf-8') as archivo_salida:
        archivo_salida.write(resultado_final)

    print(f"Paginación quirúrgica completada. Protegido en: {ruta_salida}")


if __name__ == "__main__":
    # Ejecución aislada. Modifica las rutas según el sistema de archivos.
    ruta_origen = os.path.join("lecciones", "El ataque doble en ajedrez.txt")
    ruta_destino = os.path.join("lecciones", "tactica_doble_teoria.txt")

    # Creamos un archivo dummy de prueba si no existe la estructura
    if not os.path.exists(ruta_origen):
        os.makedirs("lecciones", exist_ok=True)
        with open(ruta_origen, 'w', encoding='utf-8') as f:
            f.write("Texto inicial...\n\n[FEN:8/8/8/8/8/8/8/8 w - - 0 1]\n\nMás teoría.")

    auto_paginar_leccion(ruta_origen, ruta_destino, 150)