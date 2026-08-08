import math

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