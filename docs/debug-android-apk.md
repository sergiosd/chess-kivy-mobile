# Herramienta de diagnóstico de Android
## Configuracion del móvil en modo depuración USB
En Android, el procedimiento general es el siguiente:
1. Abre Ajustes en el teléfono. 
2. Entra en Acerca del teléfono o Información del teléfono. Localiza Número de compilación.
3. En algunos fabricantes esta opción puede aparecer dentro de otro apartado. Por ejemplo:
   - Xiaomi: normalmente dentro de Versión de MIUI o Versión de HyperOS.
   - Samsung: normalmente en Información de software → Número de compilación.
4. Pulsa varias veces consecutivas sobre Número de compilación, normalmente siete veces. El sistema mostrará un mensaje indicando que las opciones de desarrollador han sido habilitadas. Es posible que solicite el PIN, patrón o contraseña del dispositivo.
5. Regresa a Ajustes y localiza Opciones de desarrollador. Dependiendo del fabricante, puede encontrarse dentro de apartados como:
```
Ajustes → Sistema → Opciones de desarrollador
o:
Ajustes → Ajustes adicionales → Opciones de desarrollador
```
6. Dentro de las opciones de desarrollador, activa:```Depuración USB```
7. Conecta el teléfono al ordenador mediante un cable USB que permita transferencia de datos.
8. Al conectar el dispositivo por primera vez con la depuración USB activada, Android debería mostrar un mensaje similar a: ```¿Permitir depuración USB?```
El aviso incluye la huella RSA del ordenador. Si se trata de tu propio ordenador, puedes marcar:```Permitir siempre desde este ordenador```
y pulsar Permitir.

## Conexión con el dispositivo Android desde Windows
WSL no siempre tiene acceso directo a los dispositivos USB conectados al sistema anfitrión. Por ello, aunque el teléfono esté conectado correctamente a Windows y tenga activada la depuración USB, puede no aparecer automáticamente dentro del entorno Linux.

**Instalar Android SDK Platform-Tools en Windows**

No es necesario instalar Android Studio completo. Google distribuye ADB dentro del paquete independiente SDK Platform-Tools. La página oficial de descarga es:

[Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools)

En esa página:
1. Localiza la opción:`Download SDK Platform-Tools for Windows`
2. Acepta las condiciones de licencia.
3. Descarga el archivo ZIP.
4. Extrae su contenido, por ejemplo, en:`C:\platform-tools`

La carpeta debería contener archivos como: adb.exe, fastboot.exe, AdbWinApi.dll, AdbWinUsbApi.dll.

## Comprobación conexión con teléfono
- Conecta el teléfono al PC en modo transferencia de archivos (no sólo cargar a través de USB)- Asegúrate que el cable USB permite transferencia de datos.
- Con el teléfono conectado mediante USB y la depuración USB activada, abre PowerShell en Windows.
- Accede al directorio de Platform-Tools:
```
 cd C:\platform-tools`
 ```
- Comprueba que ADB detecta el dispositivo:
```
.\adb devices
```
Debería aparecer un resultado similar a:
```
List of devices attached
XXXXXXXXXXXX    device
```
Si aparece: `unauthorized` desbloquea el teléfono y acepta la solicitud de autorización para la depuración USB.

Si el teléfono no muestra la ventana de autorización RSA para la depuración USB, puede ser útil revocar las autorizaciones existentes y forzar una nueva asociación entre el dispositivo Android y el ordenador.

Sigue estos pasos:

1. Desconecta físicamente el cable USB del teléfono o del ordenador.
2. En el teléfono, accede a:
```
Ajustes → Opciones de desarrollador
```
3. Busca la opción: `Revocar autorizaciones de depuración USB` y confirma la operación. Esto elimina las autorizaciones ADB almacenadas previamente en el dispositivo.
4. Mantén el teléfono desbloqueado y con la pantalla encendida.
5. Vuelve a conectar el teléfono al ordenador mediante un cable USB compatible con transferencia de datos.
6. Android debería mostrar nuevamente el cuadro de diálogo:`¿Permitir depuración USB?`
7. Si el ordenador es de confianza, marca:`Permitir siempre desde este ordenador` y pulsa Permitir.

Después, desde PowerShell, puede comprobarse el estado de la conexión ejecutando:
```
cd C:\platform-tools
.\adb devices
```
Si la autorización se ha realizado correctamente, el dispositivo debería aparecer con el estado: `device`
Si continúa apareciendo como:`unauthorized` puede reiniciarse el servidor ADB:
```
.\adb kill-server
.\adb start-server
.\adb devices
```
A continuación, vuelve a comprobar la pantalla del teléfono para aceptar la solicitud de autorización.

Si el dispositivo no aparece en absoluto, el problema probablemente no está relacionado con la autorización RSA, sino con la conexión USB, el modo USB seleccionado, los controladores de Windows o el propio cable.
