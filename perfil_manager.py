import json
import os

import os
import json
from kivy.uix.screenmanager import Screen

class PerfilManager:
    """
    Gestiona la persistencia de usuarios distribuyendo los datos en múltiples archivos.

    Implementa el Modelo del patrón MVC aislando cada perfil en su propio
    archivo JSON dentro de un directorio dedicado.
    """

    def __init__(self, directorio_perfiles="perfiles"):
        """
        Inicializa el gestor y asegura la existencia de la estructura de carpetas.

        Args:
            directorio_perfiles (str): Ruta al directorio donde vivirán los JSON.
        """
        self.directorio = directorio_perfiles
        if not os.path.exists(self.directorio):
            os.makedirs(self.directorio)

        self.archivo_global = os.path.join(self.directorio, "_estado_global.json")

    def obtener_ultimo_usuario(self) -> str | None:
        """
        Recupera el identificador del último jugador que utilizó la aplicación.

        Returns:
            str o None: Nombre del usuario o None si el archivo no existe.
        """
        if os.path.exists(self.archivo_global):
            with open(self.archivo_global, "r", encoding="utf-8") as f:
                try:
                    return json.load(f).get("ultimo_usuario")
                except json.JSONDecodeError:
                    pass
        return None

    def fijar_ultimo_usuario(self, nombre: str) -> None:
        """
        Registra un usuario como el último activo en el archivo de estado global.

        Args:
            nombre (str): Identificador del perfil.
        """
        datos = {}
        if os.path.exists(self.archivo_global):
            with open(self.archivo_global, "r", encoding="utf-8") as f:
                try:
                    datos = json.load(f)
                except json.JSONDecodeError:
                    pass

        datos["ultimo_usuario"] = nombre
        with open(self.archivo_global, "w", encoding="utf-8") as f:
            json.dump(datos, f)

    def obtener_lista_usuarios(self) -> list:
        """
        Escanea el directorio físico para listar todos los perfiles existentes.

        Returns:
            list: Lista de nombres de usuario.
        """
        usuarios = []
        if os.path.exists(self.directorio):
            for archivo in os.listdir(self.directorio):
                if archivo.endswith(".json") and archivo != "_estado_global.json":
                    usuarios.append(archivo.replace(".json", ""))
        return usuarios

    def cargar_perfil(self, nombre_usuario: str) -> dict:
        """
        Busca y carga la información de progreso de un jugador específico.

        Args:
            nombre_usuario (str): Nombre del perfil a buscar en disco.

        Returns:
            dict: Diccionario completo con las métricas del jugador.
        """
        ruta = os.path.join(self.directorio, f"{nombre_usuario}.json")
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    pass

        return {
            "nombre": nombre_usuario,
            "elo": 0,
            "resueltos": [],
            "partidas_jugadas": 0,
            "escala_pop": 0,
            "victorias_100": 0,
            "progreso_escuela": {},
            "practica_lecciones": {}
        }

    def guardar_perfil(self, perfil_dict: dict) -> None:
        """
        Persiste los datos de un usuario sobrescribiendo su archivo local.

        Args:
            perfil_dict (dict): Datos del jugador a serializar.
        """
        nombre = perfil_dict["nombre"]
        ruta = os.path.join(self.directorio, f"{nombre}.json")

        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(perfil_dict, f, indent=4)

        self.fijar_ultimo_usuario(nombre)

    def inicializar_practica_leccion(self, perfil: dict, id_leccion: str) -> None:
        """
        Inyecta la estructura de datos obligatoria para una lección específica.

        Modifica el diccionario en memoria. Debes llamar a guardar_perfil()
        posteriormente para persistir el estado.

        Args:
            perfil (dict): Diccionario en memoria del usuario activo.
            id_leccion (str): Identificador de la unidad didáctica.
        """
        if "practica_lecciones" not in perfil:
            perfil["practica_lecciones"] = {}

        if id_leccion not in perfil["practica_lecciones"]:
            perfil["practica_lecciones"][id_leccion] = {
                "rating": 0.0,
                "resueltos": [],
                "fallados": []
            }
            return

        estado_local = perfil["practica_lecciones"][id_leccion]
        estado_local.setdefault("rating", 0.0)
        estado_local.setdefault("resueltos", [])
        estado_local.setdefault("fallados", [])



