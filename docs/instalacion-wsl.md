# Instalacion de WSL

## Que es WSL?
WSL es el Subsistema de Windows para Linux. Permite ejecutar un entorno GNU/Linux completo directamente dentro de tu sistema operativo de Microsoft. Es una capa de compatibilidad que elimina la necesidad de instalar máquinas virtuales pesadas. No tienes que particionar tu disco duro. Olvídate de configurar arranques duales complicados. Tienes acceso inmediato a herramientas de línea de comandos y utilidades nativas de Linux.

La tecnología actual esconde un núcleo de Linux real ejecutándose en segundo plano. Utiliza una arquitectura de hipervisor extremadamente ligera. El rendimiento al leer o escribir datos es altísimo. La integración entre ambos sistemas es absoluta. Puedes abrir un documento guardado en tu escritorio de Windows desde la terminal de Ubuntu. Modificas ese mismo archivo usando comandos exclusivos de Linux al instante.

Su diseño busca servir a programadores y administradores de sistemas. Un desarrollador web puede crear y probar su código en un entorno idéntico al servidor final. Ejecutas aplicaciones gráficas de Linux sin configuraciones extrañas. Aprovechas la potencia de tu tarjeta de vídeo para tareas complejas. Trabajas con contenedores Docker de forma nativa.

## Instalación

### 1. Abrir PowerShell como administrador
Haz clic en el botón de Inicio de Windows. Escribe "PowerShell". Haz clic derecho sobre el primer resultado y selecciona "Ejecutar como administrador". El sistema te pedirá permisos de seguridad. Acéptalos

### 2.Ejecutar el comando principal
Copia y pega este comando en la ventana azul que acaba de aparecer:

```wsl --install```

Pulsa Enter. Esta instrucción descarga el núcleo de Linux. Instalará la distribución Ubuntu por defecto. Tardará unos minutos dependiendo de tu conexión a internet.

### 3. Reiniciar el ordenador
La consola mostrará un mensaje indicando que la operación se ha completado con éxito. Cierra todos tus programas abiertos. Reinicia tu máquina por completo. Windows necesita el reinicio para habilitar las nuevas características del sistema operativo.

### 4. Crear las credenciales de Linux
Tras el reinicio aparecerá una terminal negra de Ubuntu de forma automática. Si no salta sola, busca "Ubuntu" en el menú de Inicio y ábrelo. Te pedirá que escribas un nombre de usuario nuevo. A continuación deberás escribir una contraseña. Los caracteres no se verán en la pantalla mientras tecleas. Pulsa Enter al terminar.

