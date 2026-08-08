import json
import os


class PerfilManager:
    """
    Gestiona la persistencia y carga de perfiles de usuario en almacenamiento local.

    Esta clase actúa como el 'Modelo' de datos en la arquitectura MVC, encapsulando
    completamente la lógica de acceso a disco (archivos JSON) para que la interfaz
    gráfica y los controladores de Kivy no tengan que lidiar con la inestable
    lectura/escritura de archivos[cite: 4].
    """

    def __init__(self, ruta_archivo="perfiles_entrenamiento.json"):
        """
        Inicializa el gestor de perfiles.

        Args:
            ruta_archivo (str): Ruta relativa o absoluta al archivo JSON donde
                                se persistirán los datos de los jugadores. Por defecto
                                apunta a 'perfiles_entrenamiento.json'[cite: 4].
        """
        self.ruta_archivo = ruta_archivo

    def obtener_ultimo_usuario(self):
        """
        Recupera el identificador del último jugador que utilizó la aplicación.

        Abre el archivo JSON y busca la clave global y especial '_ultimo_usuario',
        la cual se utiliza para recordar qué perfil debe autologuearse al iniciar[cite: 4].

        Returns:
            str o None: El nombre del usuario si existe en el archivo. Devuelve
                        None si el archivo no existe o está corrupto[cite: 4].
        """
        if os.path.exists(self.ruta_archivo):
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                try:
                    datos = json.load(f)
                    return datos.get("_ultimo_usuario", None)
                except:
                    pass
        return None

    def obtener_lista_usuarios(self):
        """
        Genera una lista con los nombres de todos los jugadores registrados.

        Escanea las claves principales del diccionario JSON en disco y purga
        cualquier metadato interno del sistema para devolver únicamente los perfiles[cite: 1].

        Returns:
            list: Lista de cadenas de texto (strings) con los nombres de usuario.
                  Devuelve una lista vacía si ocurre un error de lectura o el
                  archivo no existe[cite: 1].
        """
        if os.path.exists(self.ruta_archivo):
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                try:
                    datos = json.load(f)
                    # Excluimos la clave especial de seguimiento del sistema[cite: 1]
                    return [k for k in datos.keys() if k != "_ultimo_usuario"]
                except json.JSONDecodeError:
                    pass
        return []

    def cargar_perfil(self, nombre_usuario):
        """
        Busca y carga la información de progreso de un jugador específico.

        Inyecta un parche de retrocompatibilidad para perfiles antiguos que
        no tengan el contador de popularidad[cite: 7].

        Args:
            nombre_usuario (str): Nombre del perfil que se desea cargar[cite: 7].

        Returns:
            dict: Diccionario completo con las métricas del jugador[cite: 7].
        """
        if os.path.exists(self.ruta_archivo):
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                try:
                    datos = json.load(f)
                    if nombre_usuario in datos:
                        perfil = datos[nombre_usuario]

                        # Parcheamos la asquerosa base de datos si es antigua
                        if "escala_pop" not in perfil:
                            perfil["escala_pop"] = 0
                            perfil["victorias_100"] = 0
                        if "partidas_jugadas" not in perfil:
                            perfil["partidas_jugadas"] = len(perfil.get("resueltos", []))

                        return perfil
                except json.JSONDecodeError:
                    pass

        # Estructura por defecto para nuevos usuarios dictada por tu intelecto[cite: 7]
        return {
            "nombre": nombre_usuario,
            "elo": 0,  # ¡Arrancamos desde el fango absoluto!
            "resueltos": [],
            "partidas_jugadas": 0,
            "escala_pop": 0,
            "victorias_100": 0
        }

    def guardar_perfil(self, perfil_dict):
        """
        Persiste los datos de un usuario en el almacenamiento local.

        Actualiza la entrada del jugador en el archivo JSON. Además, registra a
        este usuario como el último jugador activo en la clave global del sistema[cite: 4].

        Args:
            perfil_dict (dict): Diccionario con los datos actualizados del jugador,
                                incluyendo obligatoriamente la clave 'nombre'[cite: 4].
        """
        datos = {}
        if os.path.exists(self.ruta_archivo):
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                try:
                    datos = json.load(f)
                except json.JSONDecodeError:
                    pass

        datos[perfil_dict["nombre"]] = perfil_dict
        # Guardamos la llave de memoria[cite: 4]
        datos["_ultimo_usuario"] = perfil_dict["nombre"]

        with open(self.ruta_archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4)