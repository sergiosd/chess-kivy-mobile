"""
Módulo de procesamiento de texto para paginación automática.

Automatiza la inserción de directivas de control para el motor de Kivy.
Calcula el peso visual masivo de los tableros FEN para evitar
el desbordamiento de los componentes en la interfaz gráfica.
"""

import os
import re


def auto_paginar_leccion(ruta_entrada: str, ruta_salida: str, limite_palabras: int = 120) -> None:
    """
    Forja un archivo de lección paginado dinámicamente evaluando el peso léxico real.

    Destruye la dependencia de los saltos de línea dobles. Cuantifica el volumen de
    palabras integrando el costo visual de los bloques tácticos interactivos. Mantiene
    intactas las directivas de página impuestas manualmente en el código fuente.

    Args:
        ruta_entrada (str): Origen del papiro digital crudo.
        ruta_salida (str): Destino de la lección purificada y formateada.
        limite_palabras (int): Capacidad máxima tolerada por la vista gráfica de Kivy.
    """
    if not os.path.exists(ruta_entrada):
        print(f"Error letal: El archivo {ruta_entrada} ha desaparecido del disco.")
        return

    with open(ruta_entrada, 'r', encoding='utf-8') as archivo:
        texto_crudo = archivo.read()

    # Fragmentamos el texto respetando tus etiquetas estáticas absolutas
    bloques_maestros = texto_crudo.split('[PAGINA]')
    paginas_procesadas = []

    # Asignamos un coste léxico virtual a los tableros para engañar al contador
    PESO_TABLERO = 50

    for bloque in bloques_maestros:
        # La expresión regular aísla los espacios y protege los bloques tácticos
        patron = re.compile(r'(\s+|\[FEN:.*?\]|\[PUZZLE\].*?\[FIN\])', re.DOTALL)
        fragmentos = patron.split(bloque)

        texto_pagina_actual = []
        contador_palabras = 0

        for frag in fragmentos:
            if not frag:
                continue

            if frag.isspace():
                # Ignoramos la basura blanca al comienzo de una página limpia
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

    # Ensamblamos la obra maestra inyectando el delimitador estructural
    resultado_final = "\n\n[PAGINA]\n\n".join(paginas_procesadas)

    with open(ruta_salida, 'w', encoding='utf-8') as archivo_salida:
        archivo_salida.write(resultado_final)

    print(f"Paginación completada con éxito. Archivo protegido en: {ruta_salida}")


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