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


class CalculadorRatingTactico:
    """Gestiona el rating 0–100 de la práctica de cada lección."""

    K = 10.0
    ESCALA_PROBABILIDAD = 20.0
    GANANCIA_MINIMA_VICTORIA = 1.0
    PERDIDA_MAXIMA_DERROTA = 2.0

    DIFICULTAD_POR_PLIES = {
        2: 10.0,
        4: 20.0,
        6: 40.0,
        8: 60.0,
        10: 80.0,
        12: 85.0,
        14: 90.0,
        16: 95.0,
        18: 100.0,
    }

    @classmethod
    def normalizar_rating(cls, rating: float) -> float:
        """Limita un rating al intervalo válido de 0 a 100."""
        return max(0.0, min(100.0, float(rating)))

    @classmethod
    def dificultad_por_plies(cls, plies: int) -> float:
        """Convierte la longitud real del puzzle en dificultad de rating."""
        plies = max(0, int(plies))
        if plies >= 18:
            return 100.0
        if plies in cls.DIFICULTAD_POR_PLIES:
            return cls.DIFICULTAD_POR_PLIES[plies]

        for limite in (2, 4, 6, 8, 10, 12, 14, 16, 18):
            if plies <= limite:
                return cls.DIFICULTAD_POR_PLIES[limite]
        return 100.0

    @classmethod
    def calcular_variacion(cls, rating_usuario: float, dificultad: float,
                           victoria: bool) -> float:
        """Calcula una variación tipo ELO comprimida a la escala 0–100."""
        rating_usuario = cls.normalizar_rating(rating_usuario)
        dificultad = cls.normalizar_rating(dificultad)
        esperabilidad = 1.0 / (
            1.0 + math.pow(
                10.0,
                (dificultad - rating_usuario) / cls.ESCALA_PROBABILIDAD
            )
        )
        resultado = 1.0 if victoria else 0.0
        variacion = cls.K * (resultado - esperabilidad)

        if victoria:
            return max(cls.GANANCIA_MINIMA_VICTORIA, variacion)

        return max(-cls.PERDIDA_MAXIMA_DERROTA, variacion)

    @classmethod
    def actualizar_rating(cls, rating_usuario: float, dificultad: float,
                          victoria: bool) -> tuple[float, float]:
        """Devuelve la variación aplicada y el nuevo rating limitado a 0–100."""
        rating_actual = cls.normalizar_rating(rating_usuario)
        variacion_teorica = cls.calcular_variacion(
            rating_actual, dificultad, victoria
        )
        nuevo_rating = cls.normalizar_rating(rating_actual + variacion_teorica)
        variacion_aplicada = nuevo_rating - rating_actual
        return variacion_aplicada, nuevo_rating

    @staticmethod
    def obtener_rango(rating: float) -> str:
        """Devuelve el nombre visible correspondiente al rating de la lección."""
        rating = max(0.0, min(100.0, float(rating)))
        if rating <= 20:
            return "Principiante"
        if rating <= 40:
            return "Intermedio"
        if rating <= 60:
            return "Avanzado"
        if rating <= 80:
            return "Experto"
        if rating < 95:
            return "Maestro"
        return "Gran Maestro"

    @staticmethod
    def obtener_pesos_seleccion(rating: float) -> dict[str, int]:
        """Obtiene la distribución de longitudes definida para el rating actual."""
        rating = max(0.0, min(100.0, float(rating)))
        if rating <= 20:
            return {"4": 100}
        if rating <= 40:
            return {"4": 80, "6": 20}
        if rating <= 60:
            return {"4": 70, "6": 30}
        if rating <= 80:
            return {"4": 60, "6": 40, "8": 10, "10+": 5}
        if rating < 95:
            return {"4": 50, "6": 50, "8": 20, "10+": 5}
        return {"4": 33, "6": 50, "8+": 17}

    @staticmethod
    def obtener_dificultad_visible(plies: int) -> str:
        """Devuelve la dificultad visible del puzzle segun su longitud."""
        plies = max(0, int(plies))
        if plies <= 4:
            return "PUZZLE NORMAL"
        if plies <= 6:
            return "PUZZLE DIFICIL"
        if plies <= 8:
            return "PUZZLE MUY DIFICIL"
        return "PUZZLE DE MAESTRO"

def compilar_markdown_a_kivy(texto: str, escala_fuente: float = 1.0) -> str:
    """
    Transmuta la elegante sintaxis Markdown en el arcaico Kivy Markup.

    Intercepta cabeceras, negritas, cursivas y listas, transformándolas
    dinámicamente para que el componente Label de Kivy no sufra un kernel panic.

    Args:
        texto (str): Papiro digital con sintaxis Markdown pura.
        escala_fuente (float): Factor aplicado a los tamaños de las cabeceras.

    Returns:
        str: Texto mutado con etiquetas '[b]', '[i]', '[size]' nativas de Kivy.
    """
    lineas = texto.split('\n')
    resultado = []
    contador_lista = 1
    escala_fuente = max(0.1, float(escala_fuente))

    tamano_h1 = 24.0 * escala_fuente
    tamano_h2 = 20.0 * escala_fuente
    tamano_h3 = 18.0 * escala_fuente

    for linea in lineas:
        # --- Cabeceras (Headings) ---
        if linea.startswith('# '):
            linea = f"[size={tamano_h1:.2f}sp][b][color=#8F86F3]{linea[2:].strip()}[/color][/b][/size]"
        elif linea.startswith('## '):
            linea = f"[size={tamano_h2:.2f}sp][b][color=#AFA6F3]{linea[3:].strip()}[/color][/b][/size]"
        elif linea.startswith('### '):
            linea = f"[size={tamano_h3:.2f}sp][b][color=#CFC6F3]{linea[4:].strip()}[/color][/b][/size]"

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