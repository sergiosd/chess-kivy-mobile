# Especificaciones Técnicas: Módulo de Práctica (Escuela)
*Documento vivo de arquitectura y diseño para la integración en Android (Kivy)*

## 1. Objetivo y Alcance
Definir la arquitectura de datos, el flujo de información y las reglas de negocio para el módulo de "Práctica" vinculado a las lecciones individuales en la Escuela de Ajedrez, asegurando un rendimiento óptimo y sin bloqueos de interfaz (ANR) en dispositivos móviles.

## 2. Arquitectura de Datos (Modelo)

### 2.1. Definición del Temario (`temario.json`)
El índice maestro de lecciones se expande para mapear explícitamente el archivo CSV que contiene la base de datos de puzles (aislada por tema). Este archivo servirá como fuente de verdad para el enrutamiento local en el directorio `databases/` o `lecciones/`.

```json
"tac_02": {
    "teoria": "tactica_doble_teoria.txt",
    "ejemplos": null,
    "practica": "doble_db_puzzle.csv"
}
```

### 2.2. Estado del Usuario (`[nombre_usuario].json`)
El perfil del jugador encapsulará el progreso de la práctica de forma aislada para no contaminar el rendimiento ni el ELO del modo de juego libre. Se forjará un nuevo nodo raíz llamado `practica_lecciones`.

| Campo Local | Tipo de Dato | Función Arquitectónica |
| :--- | :--- | :--- |
| `elo` | Entero (int) | Nivel de habilidad local en la táctica específica. Inicia en 1000. |
| `resueltos` | Lista [str] | Registro de IDs de puzles superados satisfactoriamente. |
| `fallados` | Lista [str] | Registro de IDs de puzles errados por el jugador. |

*Estructura Estándar:*
```json
"practica_lecciones": {
    "tac_02": {
        "elo": 1050,
        "resueltos": ["001a", "005f"],
        "fallados": ["002b"]
    }
}
```

## 3. Lógica de Negocio y Algoritmos (Controlador)

### 3.1. Algoritmo de Extracción Aleatoria Segura
**Requisito:** Seleccionar un puzle aleatorio verificando que su ID no resida en el historial del usuario.
**Peligro Crítico:** Utilizar un bucle condicional (`while True` extrayendo al azar hasta encontrar uno libre) congelará el hilo principal (Main Thread) en Kivy cuando el *pool* de puzles se reduzca, paralizando la aplicación Android.
**Solución Algorítmica (Teoría de Conjuntos):**
1. Extraer los identificadores disponibles del CSV.
2. Calcular la unión de exclusiones en memoria RAM: `excluidos = set(resueltos) | set(fallados)`.
3. Filtrar candidatos disponibles mediante una criba matemática O(1) de verificación.
4. Aplicar `random.choice()` directamente sobre el conjunto purificado resultante.

### 3.2. Motor Estadístico Local
El servicio matemático `CalculadorElo` actuará de forma agnóstica. El controlador de la vista extraerá el `elo` local (ej. 1050) en lugar del global, lo inyectará en la fórmula, y persistirá la variación (`delta`) estrictamente dentro de la jerarquía de `practica_lecciones`.

## 4. Áreas de Mejora y Riesgos Detectados (Crítica de Diseño)
* **Agotamiento del Material:** El sistema actual excluye permanentemente tanto los puzles acertados como los fallados. Esto garantiza que el jugador consuma las bases de datos enteras, pero **impide el aprendizaje de los errores**.
* **Propuesta Técnica a Futuro:** Evaluar la implementación de un mecanismo de *Spaced Repetition* (Repetición Espaciada) donde los IDs de la lista de `fallados` tengan un tiempo de retención, o incorporar un botón global de "Reiniciar Lección" para vaciar el historial y permitir reintentos.