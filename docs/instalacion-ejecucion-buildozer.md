# Instalacion de buildozer en WSL
## Guia completa de instalación de Buildozer
La guia completa se encuentra en:
[Buildozer Installation Guide](https://buildozer.readthedocs.io/en/latest/installation/)

## Comprobaciones de Seguridad
- Si te fijas en la sección Notes for WSL users, nunca debes compilar en el disco de Windows (/mnt/c/). Como tú eres un fenómeno y tienes una visión estructural perfecta, ya alojaste tu código en ~/kivychess (dentro del sistema de archivos nativo de Linux). Lo bordas siempre. Ese paso ya lo tienes dominado.
- Asegurate de no estar nunca en un entorno de anaconda. Por seguridad para salir de un posible entorno de anaconda ejecuta:
```
deactivate
```
*Da igual si devuelve el error de comando no encontrado.*

## Verificación de la Infraestructura Base
Antes de lanzar el chorro de dependencias de C, Java y Rust que exige la guía, necesitamos saber a qué versión de Ubuntu nos enfrentamos. La guía varía los paquetes requeridos dependiendo de si estás en la 24.04 o la 22.04.

Abre sesión en WSL y lanza este comando para obligar al sistema operativo a confesar su identidad:
```
lsb_release -a
```
Ejemplo:
```
sergio@DESKTOP-16I5MKA:~$ lsb_release -a
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 26.04 LTS
Release:        26.04
Codename:       resolute
```

## Instalación en Ubuntu 26.04
### Instalación de las dependencias nativas del sistema operativo
Lanza este comando para inyectar todas las dependencias nativas del sistema operativo.
```
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-virtualenv autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo6 cmake libffi-dev libssl-dev automake autopoint gettext
```
### Configuración de Java
Antes de continuar con la instalación de Rust, conviene revisar la configuración de Java.

Aunque la guía sitúa la configuración de Java justo antes de instalar Rust, ambos componentes son independientes durante esta fase, por lo que el orden entre estas operaciones no es relevante.

El comando:
```
sudo update-alternatives --config java
```
abre un menú interactivo en el que es necesario seleccionar manualmente la versión de Java que se desea utilizar. Si ya conocemos la ruta de Java 17, podemos evitar ese paso y establecer directamente Java 17 como versión predeterminada mediante los siguientes comandos:
```
sudo update-alternatives --set java /usr/lib/jvm/java-17-openjdk-amd64/bin/java
sudo update-alternatives --set javac /usr/lib/jvm/java-17-openjdk-amd64/bin/javac
```
De esta forma, tanto java como javac quedarán configurados para utilizar OpenJDK 17.

Esta versión es adecuada para el entorno de compilación de Android que se está configurando con Buildozer.

Si alguno de los comandos devuelve un error indicando que la ruta especificada no existe, será necesario comprobar qué versiones de Java están instaladas. En ese caso puede utilizarse:
```
sudo update-alternatives --config java``
```
### Instalación de Rust
A continuación, se debe instalar Rust utilizando el instalador oficial `rustup`.

La guía original propone ejecutar:

```bash
curl https://sh.rustup.rs -sSf | sh
```

Este comando inicia el instalador de Rust de forma interactiva y solicita seleccionar una de las opciones disponibles. Si se desea utilizar directamente la configuración predeterminada sin intervención manual, puede ejecutarse:

```bash
curl https://sh.rustup.rs -sSf | sh -s -- -y
```

La opción `-y` hace que `rustup` acepte automáticamente la instalación con los valores predeterminados.

Una vez finalizada la instalación, es necesario cargar en la sesión actual las variables de entorno configuradas por Rust:

```bash
source "$HOME/.cargo/env"
```

También puede utilizarse la sintaxis equivalente:

```bash
. "$HOME/.cargo/env"
```

El punto inicial de esta segunda forma es importante, ya que indica al shell que ejecute el archivo dentro de la sesión actual.

Normalmente, `rustup` configura el entorno necesario para que herramientas como `rustc` y `cargo` estén disponibles. Cargar `$HOME/.cargo/env` permite utilizarlas inmediatamente sin necesidad de cerrar y abrir una nueva terminal.

Para comprobar que la instalación se ha realizado correctamente, pueden ejecutarse:

```bash
rustc --version
cargo --version
```

Si ambos comandos muestran sus respectivas versiones, Rust y Cargo están correctamente instalados y disponibles en el entorno actual.

### Creación de un entorno virtual
Antes de instalar las herramientas de compilación de Python, es recomendable crear un entorno virtual específico para el proyecto.

En sistemas Linux modernos, algunas instalaciones de Python pueden estar configuradas como entornos administrados externamente. En estos casos, `pip` puede impedir la instalación directa de paquetes en el entorno global del sistema para evitar conflictos con los paquetes gestionados por el propio sistema operativo.

Utilizar un entorno virtual permite instalar Buildozer y sus dependencias de forma aislada, sin modificar la instalación global de Python.

Si se va a utilizar Python 3.14 y esta versión ya está instalada en el sistema, primero puede instalarse el módulo necesario para crear entornos virtuales:

```bash
sudo apt install -y python3.14-venv
```

A continuación, se crea un entorno virtual denominado `entorno_android`:

```bash
python3.14 -m venv entorno_android
```

El entorno se activa mediante:

```bash
source entorno_android/bin/activate
```

La forma abreviada equivalente es:

```bash
. entorno_android/bin/activate
```

Una vez activado, el intérprete de Python y los paquetes instalados mediante `pip` quedarán asociados a este entorno virtual en lugar de a la instalación global del sistema.

Se puede comprobar que el entorno está activo porque normalmente aparecerá su nombre al principio del prompt de la terminal:

```text
(entorno_android) usuario@equipo:~$
```

También puede verificarse mediante:

```bash
which python
python --version
```

El primer comando debería mostrar una ruta correspondiente al entorno virtual, por ejemplo:

```text
.../entorno_android/bin/python
```

A partir de este punto, las dependencias necesarias para Buildozer pueden instalarse dentro de `entorno_android`, manteniéndolas aisladas del Python gestionado por el sistema operativo.

### Instalación de buildozer
A continuación, se debe instalar la versión actual de Buildozer directamente desde su repositorio oficial, junto con los paquetes de Python necesarios para este entorno de compilación.

Antes de ejecutar los comandos, conviene comprobar que el entorno virtual está activo:

```
source venv_p4a_develop/bin/activate
```
Si el entorno virtual se creó con otro nombre, debe utilizarse la ruta correspondiente.

Una vez activado, se instala Buildozer desde GitHub:
```
pip install git+https://github.com/kivy/buildozer
```
A continuación, se instalan las dependencias Python requeridas:
```
pip install legacy-cgi setuptools cython==0.29.34
```

### Creacion y modificacion inicial del fichero buildozer.spec

Después de completar la instalación, debe crearse y editarse el archivo buildozer.spec del proyecto.

Crea y navega al proyecto. El directorio del proyecto debe estar ubicado bajo el directorio del entorno.

Ejecuta:
```
buildozer init
```
Ejemplo:
```
(entorno_android) sergio@DESKTOP-16I5MKA:~/entorno_android/kivychess$ buildozer init
# Copy /home/sergio/entorno_android/lib/python3.14/site-packages/buildozer/default.spec to buildozer.spec
File buildozer.spec created, ready to customize!
```

y establecer los siguientes parámetros:
```
p4a.branch = develop
android.api = 36
android.ndk = 29
```
Estos valores tienen las siguientes funciones:
- p4a.branch = develop hace que Buildozer utilice la rama develop de python-for-android.
- android.api = 36 establece la API de Android utilizada como objetivo de compilación.
- android.ndk = 29 especifica la versión del Android NDK utilizada durante el proceso de compilación.

La guía indica que también puede utilizarse:
```
android.ndk = 28c
```

como alternativa compatible.

Estos cambios en buildozer.spec son necesarios cuando se trabaja con Ubuntu 26.04 y su versión predeterminada de Python 3.14, ya que los valores predeterminados generados por Buildozer no son adecuados para esta configuración.

Antes de iniciar la compilación, puede verificarse que Buildozer y Python están ejecutándose desde el entorno virtual mediante:
```
which python
which buildozer
python --version
buildozer --version
```
Las rutas mostradas por which python y which buildozer deberían apuntar al directorio del entorno virtual activo.

### Ejemplo de parámetros a modificar en buildozer.spec
```
title = Mind Chess

package.name = kivychess

package.domain = org.sergiosd

source.include_exts = py,png,jpg,kv,atlas,wav,json,csv,ttf,txt

source.exclude_dirs = tests, bin, venv, entorno_android

source.include_patterns = assets/*, assets/fonts/*, assets/pieces/*, assets/squares/*, assets/ui/*, assets/sounds/*

requirements = python3,kivy,chess

icon.filename = %(source.dir)s/assets/icon.png

orientation = portrait

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

android.accept_sdk_license = True
```

### Ejecución

Se debe copiar primero todo el proyecto en python al directorio de linux donde está ubicado el proyecto con el archivo buildozer.spec. Los directorios de trabajo de python como assets/ o perfiles/ también deben ser copiados. La forma más fácil es quizás usar el explorer de archivos de windows:
```
explorer.exe .
```
Una vez copiados los archivos se puede lanzar buildozer con:
```
buildozer -v android debug
```
Al final del proceso (de media hora a una hora) se habrá creado el paquete apk para android en el directorio bin/ del directorio de trabajo de linux-