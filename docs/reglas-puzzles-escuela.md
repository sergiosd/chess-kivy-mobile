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
El perfil del jugador encapsulará el progreso de la práctica de forma aislada para no contaminar el rendimiento ni el ELO del modo de juego libre. Cada lección dispondrá de un `rating` táctico independiente, comprendido entre 0 y 100.

| Campo Local | Tipo de Dato | Función Arquitectónica |
| :--- | :--- | :--- |
| `rating` | Número (`float`) | Dominio de la táctica específica. Rango 0–100. Inicia en `0.0`. |
| `resueltos` | Lista [str] | Registro de IDs de puzles superados satisfactoriamente. |
| `fallados` | Lista [str] | Registro de IDs de puzles errados por el jugador. |

El valor se mantiene con decimales internamente para evitar bloqueos por redondeo, pero en la interfaz se muestra redondeado a un entero.

*Estructura Estándar:*
```json
"practica_lecciones": {
    "tac_02": {
        "rating": 27.35,
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

### 3.2. Sistema de puntuación táctico (Rating 0–100)

#### 3.2.1. Escala visible para el usuario
El rating representa el dominio del usuario en **una lección/táctica concreta** y no se mezcla con el ELO general de juego.

| Rating | Rango |
| :---: | :--- |
| 0–20 | Principiante |
| 21–40 | Intermedio |
| 41–60 | Avanzado |
| 61–80 | Experto |
| 81–94 | Maestro |
| 95–100 | Gran Maestro |

`0` es el valor inicial de una lección todavía no dominada. El rating queda siempre limitado al intervalo `[0, 100]`.

#### 3.2.2. Dificultad del puzzle por número de plies
Para el sistema de práctica, la dificultad principal del puzzle se obtiene de su **longitud en plies**, no de su ELO externo.

Cada longitud recibe una dificultad interna `D` en la misma escala 0–100:

| Longitud | Dificultad `D` |
| :---: | :---: |
| 2 plies | 10 |
| 4 plies | 20 |
| 6 plies | 40 |
| 8 plies | 60 |
| 10 plies | 80 |
| 12 plies | 85 |
| 14 plies | 90 |
| 16 plies | 95 |
| 18 plies o más | 100 |

Los puzzles de **2 plies no se seleccionan por defecto en el modo rankeado** cuando la táctica requiere al menos 4 plies para desarrollar su secuencia básica. Podrán reservarse para introducción, ejemplos o lecciones donde esa longitud sí sea válida.

A partir de 10 plies se mantiene la distinción entre longitudes: un puzzle de 16 plies debe poder aportar más rating que uno de 10 plies al mismo usuario.

#### 3.2.3. Variación de rating al acertar o fallar
Se utiliza una fórmula tipo ELO, comprimida al rango 0–100.

Variables:

- `R`: rating actual del usuario.
- `D`: dificultad del puzzle según sus plies.
- `S`: resultado (`1` si acierta, `0` si falla).
- `K = 5`: velocidad de variación del rating.

Probabilidad esperada de resolver el puzzle:

```text
E = 1 / (1 + 10 ** ((D - R) / 20))
```

Actualización:

```text
nuevo_rating = clamp(R + K * (S - E), 0, 100)
```

Consecuencias buscadas:

- Acertar un puzzle claramente más difícil que el nivel del usuario produce una subida grande.
- Fallar un puzzle claramente más difícil produce una bajada pequeña.
- Acertar un puzzle del mismo nivel produce aproximadamente `+2.5`.
- Fallar un puzzle del mismo nivel produce aproximadamente `-2.5`.
- Acertar un puzzle claramente más fácil produce una subida pequeña.
- Fallar un puzzle claramente más fácil produce una bajada grande.

Ejemplos orientativos con `K = 5`:

| Usuario `R` | Puzzle | `D` | Resultado | Cambio aprox. |
| :---: | :---: | :---: | :---: | :---: |
| 20 | 4 plies | 20 | Acierta | `+2.50` |
| 20 | 4 plies | 20 | Falla | `-2.50` |
| 40 | 4 plies | 20 | Acierta | `+0.45` |
| 40 | 4 plies | 20 | Falla | `-4.55` |
| 40 | 6 plies | 40 | Acierta | `+2.50` |
| 40 | 6 plies | 40 | Falla | `-2.50` |
| 60 | 8 plies | 60 | Acierta | `+2.50` |
| 80 | 10 plies | 80 | Acierta | `+2.50` |
| 95 | 16 plies | 95 | Acierta | `+2.50` |

El rating se guarda con decimales. El redondeo se realiza únicamente para mostrarlo al usuario.

#### 3.2.4. Selección de puzzles según el rating
La selección se realiza por zonas de rating y por longitud. Primero se elige el grupo de plies aplicando los pesos definidos y después un puzzle aleatorio disponible dentro de dicho grupo.

| Rating | Rango | Distribución de longitudes |
| :---: | :--- | :--- |
| 0–20 | Principiante | 4 plies: **100%** |
| 21–40 | Intermedio | 4 plies: **80%** · 6 plies: **20%** |
| 41–60 | Avanzado | 4 plies: **60%** · 6 plies: **35%** · 8 plies: **5%** |
| 61–80 | Experto | 4 plies: **45%** · 6 plies: **40%** · 8 plies: **10%** · 10+ plies: **5%** |
| 81–94 | Maestro | 4 plies: **30%** · 6 plies: **45%** · 8 plies: **20%** · 10+ plies: **5%** |
| 95–100 | Gran Maestro | 4 plies: **20%** · 6 plies: **40%** · 8 plies: **30%** · 10+ plies: **10%** |

Dentro del grupo `10+ plies`, la selección se realiza entre todos los puzzles disponibles de 10, 12, 14, 16, 18... plies. Su impacto posterior sobre el rating utiliza la dificultad `D` correspondiente a su longitud real.

Si el grupo seleccionado no contiene puzzles disponibles porque todos sus IDs están excluidos, su peso se redistribuye entre los demás grupos disponibles del rango. La selección nunca debe resolverse mediante reintentos indefinidos.

#### 3.2.5. Criterio de diseño
El rating mide **rendimiento frente a dificultad táctica**, no cantidad de puzzles completados.

Por ello:

- Resolver muchos puzzles fáciles deja de producir grandes subidas cuando el usuario supera claramente su dificultad.
- Un fallo en material muy por debajo del nivel del usuario tiene un coste relevante.
- Resolver correctamente secuencias más largas permite progresar hacia Maestro y Gran Maestro.
- La distribución por zonas mantiene una parte de consolidación con puzzles inferiores y añade progresivamente secuencias más largas.
- El ELO original del puzzle puede conservarse como metadato, pero no interviene en el cálculo de dificultad de este sistema.

## 4. Áreas de Mejora y Riesgos Detectados (Crítica de Diseño)
* **Agotamiento del Material:** El sistema actual excluye permanentemente tanto los puzles acertados como los fallados. Esto garantiza que el jugador consuma las bases de datos enteras, pero **impide el aprendizaje de los errores**.
* **Propuesta Técnica a Futuro:** Evaluar la implementación de un mecanismo de *Spaced Repetition* (Repetición Espaciada) donde los IDs de la lista de `fallados` tengan un tiempo de retención, o incorporar un botón global de "Reiniciar Lección" para vaciar el historial y permitir reintentos.
