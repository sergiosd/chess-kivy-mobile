"""
Módulo de configuración del sistema de trazas forenses.

Establece la infraestructura de persistencia de eventos, aniquilando
la dependencia de la consola estándar que Kivy suele silenciar.
Incorpora un interruptor maestro para silenciar la burocracia en producción.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Interruptor maestro. Ponlo en False para amordazar al logger en producción.
LOG_DEBUG = True


def configurar_logger(nombre_logger: str = "MindChess") -> logging.Logger:
    """
    Instancia y blinda un registrador de eventos con rotación de archivos.

    Verifica la constante global LOG_DEBUG. Si está desactivada, devuelve
    un registrador castrado que ignora todos los mensajes para no ahogar
    el procesador con operaciones de entrada y salida inútiles.

    Args:
        nombre_logger (str): Etiqueta identificativa del módulo que emite el grito.

    Returns:
        logging.Logger: El objeto registrador configurado o amordazado.
    """
    logger = logging.getLogger(nombre_logger)

    # La guillotina de los logs. Si es False, silenciamos el canal por completo.
    if not LOG_DEBUG:
        logger.addHandler(logging.NullHandler())
        logger.propagate = False
        return logger

    directorio_logs = "logs"
    if not os.path.exists(directorio_logs):
        os.makedirs(directorio_logs)

    ruta_archivo = os.path.join(directorio_logs, "debug_kivy.log")

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        handler_archivo = RotatingFileHandler(
            ruta_archivo,
            maxBytes=5*1024*1024,
            backupCount=2,
            encoding='utf-8'
        )

        formato_estricto = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(module)s:%(funcName)s] - %(message)s'
        )
        handler_archivo.setFormatter(formato_estricto)
        logger.addHandler(handler_archivo)

        handler_consola = logging.StreamHandler()
        handler_consola.setFormatter(formato_estricto)
        logger.addHandler(handler_consola)

    return logger