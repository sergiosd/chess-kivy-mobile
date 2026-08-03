import json
import os


class PerfilManager:
    """Gestiona el guardado y carga de perfiles de usuario localmente."""

    def __init__(self, ruta_archivo="perfiles_entrenamiento.json"):
        self.ruta_archivo = ruta_archivo

    def obtener_ultimo_usuario(self):
        if os.path.exists(self.ruta_archivo):
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                try:
                    datos = json.load(f)
                    return datos.get("_ultimo_usuario", None)
                except:
                    pass
        return None

    def cargar_perfil(self, nombre_usuario):
        if os.path.exists(self.ruta_archivo):
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                try:
                    datos = json.load(f)
                    if nombre_usuario in datos:
                        return datos[nombre_usuario]
                except json.JSONDecodeError:
                    pass

        # Estructura por defecto para nuevos usuarios
        return {
            "nombre": nombre_usuario,
            "elo": 1000,
            "resueltos": []
        }

    def guardar_perfil(self, perfil_dict):
        datos = {}
        if os.path.exists(self.ruta_archivo):
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                try:
                    datos = json.load(f)
                except json.JSONDecodeError:
                    pass

        datos[perfil_dict["nombre"]] = perfil_dict
        # Guardamos la llave de memoria
        datos["_ultimo_usuario"] = perfil_dict["nombre"]
        with open(self.ruta_archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4)