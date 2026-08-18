import math
import re

class CalculadorElo:
    """
    Servicio matemático puro para la gestión de puntuaciones competitivas.

    Esta clase aísla completamente los cálculos estadísticos de la burocrática
    interfaz de Kivy y de los modelos de persistencia, asegurando un
    acoplamiento nulo (zero-coupling) y facilitando las pruebas unitarias.
    """

    @staticmethod
    def calcular_variacion(elo_jugador, elo_puzzle, victoria, partidas_jugadas):
        """
        Calcula la fluctuación de puntuación ELO tras resolver o fallar un puzle.

        Aplica una constante K adaptativa para estabilizar el progreso del usuario,
        evitando oscilaciones extremas en los rangos de clasificación a medida
        que el jugador acumula experiencia.

        Args:
            elo_jugador (float): Puntuación actual del usuario en la base de datos.
            elo_puzzle (float): Nivel de dificultad asignado a la táctica.
            victoria (bool): Verdadero si el usuario resolvió el desafío con éxito.
            partidas_jugadas (int): Cantidad histórica de puzles intentados por el perfil.

        Returns:
            float: Los puntos matemáticos exactos a sumar o restar al perfil.
        """
        # La miserable pero infalible fórmula de probabilidad de éxito
        esperabilidad = 1.0 / (1.0 + math.pow(10, (elo_puzzle - elo_jugador) / 400.0))
        puntuacion = 1.0 if victoria else 0.0

        # ¡Por los transistores quemados de un pentium! El ajuste dinámico
        constante_k = 40.0 if partidas_jugadas < 30 else 20.0

        return constante_k * (puntuacion - esperabilidad)

def compilar_markdown_a_kivy(texto: str) -> str:
    """
    Transmuta la elegante sintaxis Markdown en el arcaico Kivy Markup.

    Intercepta cabeceras, negritas, cursivas y listas, transformándolas
    dinámicamente para que el componente Label de Kivy no sufra un kernel panic.

    Args:
        texto (str): Papiro digital con sintaxis Markdown pura.

    Returns:
        str: Texto mutado con etiquetas '[b]', '[i]', '[size]' nativas de Kivy.
    """
    lineas = texto.split('\n')
    resultado = []
    contador_lista = 1

    for linea in lineas:
        # --- Cabeceras (Headings) ---
        if linea.startswith('# '):
            linea = f"[size=24sp][b][color=#8F86F3]{linea[2:].strip()}[/color][/b][/size]"
        elif linea.startswith('## '):
            linea = f"[size=20sp][b][color=#AFA6F3]{linea[3:].strip()}[/color][/b][/size]"
        elif linea.startswith('### '):
            linea = f"[size=18sp][b][color=#CFC6F3]{linea[4:].strip()}[/color][/b][/size]"

        # --- Listas Desordenadas (Unordered Lists) ---
        elif linea.strip().startswith('- ') or linea.strip().startswith('* '):
            contenido = linea.strip()[2:]
            linea = f"  • {contenido}"

        # --- Listas Ordenadas (Ordered Lists) ---
        elif re.match(r'^\s*\d+\.\s+', linea):
            partes = re.split(r'^\s*\d+\.\s+', linea, maxsplit=1)
            if len(partes) > 1:
                linea = f"  {contador_lista}. {partes[1]}"
                contador_lista += 1
        else:
            contador_lista = 1 # Reseteamos el contador si se rompe la lista

        # --- Negritas (Bold) ---
        linea = re.sub(r'\*\*(.*?)\*\*', r'[b][color=#F5A623]\1[/color][/b]', linea)

        # --- Cursivas (Italic) ---
        # Interceptamos asteriscos simples o guiones bajos
        linea = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'[i]\1[/i]', linea)
        linea = re.sub(r'_(.*?)_', r'[i]\1[/i]', linea)

        resultado.append(linea)

    return '\n'.join(resultado)