# Especificación Formal del Lenguaje Alvz

**Versión:** 0.18.0  
**Paradigma:** Multiparadigma (imperativo, orientado a objetos, funcional, asíncrono)  
**Tipado:** Dinámico con anotaciones opcionales y verificación estática  
**Implementación:** VM basada en pila + compilador WASM  

---

## 1. Gramática Léxica

### 1.1 Conjunto de Caracteres
Alvz acepta texto codificado en UTF-8. Los identificadores usan caracteres Unicode.

### 1.2 Tokens

```
IDENTIFICADOR ::= [a-zA-Z_áéíóúñÁÉÍÓÚÑüÜ] [a-zA-Z0-9_áéíóúñÁÉÍÓÚÑüÜ]*
NUMERO        ::= DIGITO+ ("." DIGITO+)?
CADENA        ::= '"' CARACTER* '"' | "'" CARACTER* "'"
CADENA_TRIPLE ::= '"""' CARACTER* '"""'
COMENTARIO    ::= "#" CARACTER* "\n"
```

### 1.3 Palabras Reservadas (Keywords)

```
variable     funcion      clase        nuevo        estatico
si           sino         mientras     para         cada
retornar     intentar     capturar     lanzar       importar
aguardar     async        global       romper       continuar
propiedad    obtener      establecer   super        instancia
de           a            en           y            o
verdadero    falso        nulo
```

### 1.4 Literales

```
VERDADERO    ::= "verdadero"
FALSO        ::= "falso"
NULO         ::= "nulo"
NUMERO       ::= DIGITO+ ("." DIGITO+)?
CADENA       ::= '"' CARACTER* '"'
               | "'" CARACTER* "'"
               | '"""' CARACTER* '"""'
```

### 1.5 Operadores

```
ARITMETICOS  ::= "+" | "-" | "*" | "/" | "%"
COMPARACION  ::= "==" | "!=" | ">" | "<" | ">=" | "<="
ASIGNACION   ::= "=" | "+=" | "-=" | "*=" | "/=" | "%="
LOGICOS      ::= "y" | "o"
OTROS        ::= "(" | ")" | "{" | "}" | "[" | "]" | "," | "."
```

---

## 2. Gramática Sintáctica (EBNF)

### 2.1 Programa

```
programa       ::= sentencia*
sentencia      ::= declaracion_variable
                 | asignacion
                 | asignacion_compuesta
                 | asignacion_indice
                 | llamada_funcion
                 | imprimir
                 | si_condicional
                 | mientras_bucle
                 | para_bucle
                 | definicion_funcion
                 | definicion_clase
                 | retornar
                 | importar
                 | intentar_capturar
                 | lanzar
                 | romper
                 | continuar
                 | global
                 | limpiar
                 | builtin_stmt
```

### 2.2 Declaraciones

```
declaracion_variable ::= "variable" IDENTIFICADOR (":" tipo)? "=" expresion
global               ::= "global" IDENTIFICADOR ("," IDENTIFICADOR)*
tipo                 ::= "numero" | "texto" | "booleano" | "lista" | "diccionario" | "funcion" | "cualquiera"
```

### 2.3 Asignaciones

```
asignacion            ::= IDENTIFICADOR "=" expresion
asignacion_compuesta  ::= IDENTIFICADOR ("+=" | "-=" | "*=" | "/=" | "%=") expresion
asignacion_indice     ::= expresion "[" expresion "]" "=" expresion
```

### 2.4 Funciones

```
definicion_funcion    ::= "funcion" "async"? IDENTIFICADOR "(" parametros? ")" (":" tipo)? bloque
funcion_anonima       ::= "funcion" "async"? "(" parametros? ")" (":" tipo)? bloque
parametros            ::= parametro ("," parametro)*
parametro             ::= IDENTIFICADOR (":" tipo)?
llamada_funcion       ::= IDENTIFICADOR "(" argumentos? ")"
argumentos            ::= expresion ("," expresion)*
retornar              ::= "retornar" expresion?
```

### 2.5 Control de Flujo

```
si_condicional  ::= "si" "("? expresion ")"? bloque
                     ("sino" "si" "("? expresion ")"? bloque)*
                     ("sino" bloque)?
mientras_bucle  ::= "mientras" "("? expresion ")"? bloque
para_bucle      ::= "para" "cada"? IDENTIFICADOR "de" expresion "a" expresion bloque
                 |  "para" "cada" IDENTIFICADOR "en" expresion bloque
romper          ::= "romper"
continuar       ::= "continuar"
```

### 2.6 Excepciones

```
intentar_capturar ::= "intentar" bloque "capturar" IDENTIFICADOR? bloque
lanzar            ::= "lanzar" expresion
```

### 2.7 Clases y Objetos

```
definicion_clase  ::= "clase" IDENTIFICADOR ("de" IDENTIFICADOR)? "{" miembro* "}"
miembro           ::= declaracion_propiedad
                    | definicion_metodo
                    | definicion_propiedad_acceso
declaracion_propiedad ::= "variable" IDENTIFICADOR "=" expresion
definicion_metodo     ::= "funcion" "estatico"? IDENTIFICADOR "(" parametros? ")" (":" tipo)? bloque
definicion_propiedad_acceso ::= "propiedad" IDENTIFICADOR "{" (obtener | establecer)* "}"
obtener           ::= "obtener" bloque
establecer        ::= "establecer" "(" IDENTIFICADOR ")" bloque
instanciacion     ::= "nuevo" IDENTIFICADOR "(" argumentos? ")"
super             ::= "super" "." IDENTIFICADOR "(" argumentos? ")"
instanceof        ::= expresion "instancia" IDENTIFICADOR
```

### 2.8 Importación

```
importar ::= "importar" CADENA
```

### 2.9 Expresiones (Precedencia descendente)

```
expresion      ::= expresion_y_logico ("o" expresion_y_logico)*
expresion_y_logico  ::= comparacion ("y" comparacion)*
comparacion    ::= aritmetica (operador_comparacion aritmetica)*
                 | aritmetica "instancia" IDENTIFICADOR
operador_comparacion ::= "==" | "!=" | ">" | "<" | ">=" | "<="
aritmetica     ::= termino (("+" | "-") termino)*
termino        ::= factor (("*" | "/" | "%") factor)*
factor         ::= NUMERO
                 | CADENA
                 | "verdadero" | "falso" | "nulo"
                 | "-" factor
                 | "(" expresion ")"
                 | "[" elementos? "]"
                 | "[" expresion "para" "cada" IDENTIFICADOR "en" expresion "]"
                 | "{" pares? "}"
                 | IDENTIFICADOR
                 | builtin_call
                 | funcion_anonima
                 | instanciacion
                 | "super" "." IDENTIFICADOR "(" argumentos? ")"
                 | factor "[" expresion (":" expresion)? "]"
                 | factor "." IDENTIFICADOR
                 | factor "." IDENTIFICADOR "(" argumentos? ")"
                 | factor "(" argumentos? ")"

elementos      ::= expresion ("," expresion)*
pares          ::= expresion ":" expresion ("," expresion ":" expresion)*
```

### 2.10 Built-in Calls

```
builtin_call  ::= "leer" "(" ")"
                | "leer_numero" "(" ")"
                | "imprimir" "(" expresion ")"
                | "azar" "(" expresion "," expresion ")"
                | "longitud" "(" expresion ")"
                | "agregar" "(" expresion "," expresion ")"
                | "esperar" "(" expresion ")"
                | "enviar_web" "(" expresion "," expresion ")"
                | "leer_archivo" "(" expresion ")"
                | "escribir_archivo" "(" expresion "," expresion ")"
                | "limpiar" "(" ")"
                | "tipo" "(" expresion ")"
                | "tiempo" "(" ")"
                | "json_codificar" "(" expresion ")"
                | "json_decodificar" "(" expresion ")"
                | "reemplazar" "(" expresion "," expresion "," expresion ")"
                | "absoluto" "(" expresion ")"
                | "redondear" "(" expresion ")"
                | "potencia" "(" expresion "," expresion ")"
                | "raiz" "(" expresion ")"
                | "mayusculas" "(" expresion ")"
                | "minusculas" "(" expresion ")"
                | "obtener_salida" "(" ")"
                | "error_msj" "(" ")"
                | "fecha_actual" "(" expresion ")"
                | "dividir" "(" expresion "," expresion ")"
                | "unir" "(" expresion "," expresion ")"
                | "a_numero" "(" expresion ")"
                | "regex_buscar" "(" expresion "," expresion ")"
                | "supabase_insertar" "(" expresion "," expresion "," expresion "," expresion ")"
                | "supabase_consultar" "(" expresion "," expresion "," expresion ")"
                | "iniciar_servidor" "(" expresion "," expresion ")"
                | "solicitud_http" "(" expresion "," expresion "," expresion ")"
                | "sqlite_abrir" "(" expresion ")"
                | "sqlite_ejecutar" "(" expresion "," expresion ")"
                | "sqlite_consultar" "(" expresion "," expresion ")"
                | "aguardar" "(" expresion ")"
```

### 2.11 Bloques

```
bloque ::= "{" sentencia* "}"
```

---

## 3. Sistema de Tipos

### 3.1 Tipos Primitivos

| Tipo       | Descripción                  | Ejemplo              |
|------------|------------------------------|----------------------|
| `numero`   | Entero o punto flotante      | `42`, `3.14`         |
| `texto`    | Cadena de caracteres         | `"hola"`, `'mundo'`  |
| `booleano` | Valor lógico                 | `verdadero`, `falso` |
| `nulo`     | Ausencia de valor            | `nulo`               |
| `lista`    | Secuencia ordenada mutable   | `[1, 2, 3]`          |
| `diccionario` | Colección clave-valor     | `{"a": 1}`           |
| `funcion`  | Función de primera clase     | `funcion(x) { x }`   |
| `cualquiera` | Tipo comodín               | —                    |

### 3.2 Anotaciones de Tipo

```
variable x: numero = 42
funcion suma(a: numero, b: numero): numero {
    retornar a + b
}
```

### 3.3 Reglas de Tipado

- Compatibilidad: dos tipos son compatibles si son iguales o uno es `cualquiera`
- Coerción implícita: `numero` → `numero` en operaciones aritméticas
- Sin coerción automática entre texto y número (usar `a_numero()`)
- Las listas y diccionarios no tienen tipo de elemento genérico

---

## 4. Especificación de Bytecode (82 Opcodes)

### 4.1 Convenciones

- Cada instrucción tiene 1 byte de opcode
- Los operandos inmediatos usan enteros de 1 byte (0-255)
- Las constantes se referencian por índice en el pool de constantes
- Las variables locales/globales se referencian por índice

### 4.2 Opcodes

| Code | Nombre                  | Operandos     | Descripción                          |
|------|-------------------------|---------------|--------------------------------------|
| 1    | `OP_CONSTANT`           | idx (1)       | Carga constante[idx] a la pila       |
| 2    | `OP_STORE`              | idx (1)       | Pop → variable local[idx]            |
| 3    | `OP_LOAD`               | idx (1)       | Variable local[idx] → pila           |
| 4    | `OP_STORE_GLOBAL`       | idx (1)       | Pop → variable global[idx]           |
| 5    | `OP_LOAD_GLOBAL`        | idx (1)       | Variable global[idx] → pila          |
| 6    | `OP_PRINT`              | —             | Pop e imprime                        |
| 7    | `OP_ADD`                | —             | Pop b, a → push(a + b)               |
| 8    | `OP_SUB`                | —             | Pop b, a → push(a - b)               |
| 9    | `OP_MUL`                | —             | Pop b, a → push(a * b)               |
| 10   | `OP_DIV`                | —             | Pop b, a → push(a / b)               |
| 11   | `OP_EQ`                 | —             | Pop b, a → push(a == b)              |
| 12   | `OP_NE`                 | —             | Pop b, a → push(a != b)              |
| 13   | `OP_GT`                 | —             | Pop b, a → push(a > b)               |
| 14   | `OP_LT`                 | —             | Pop b, a → push(a < b)               |
| 15   | `OP_GTE`                | —             | Pop b, a → push(a >= b)              |
| 16   | `OP_LTE`                | —             | Pop b, a → push(a <= b)              |
| 17   | `OP_AND`                | —             | Pop b, a → push(a and b)             |
| 18   | `OP_OR`                 | —             | Pop b, a → push(a or b)              |
| 19   | `OP_JUMP`               | addr (1)      | Salto incondicional a addr           |
| 20   | `OP_JUMP_IF_FALSE`      | addr (1)      | Pop; si falso → salto a addr         |
| 21   | `OP_INPUT`              | —             | Lee entrada → pila                   |
| 22   | `OP_RANDOM`             | —             | Pop max, min → push(randint)         |
| 23   | `OP_CLEAR`              | —             | Limpia terminal                      |
| 24   | `OP_CALL`               | addr (2)      | Llama función en addr con n args     |
| 25   | `OP_RETURN`             | —             | Retorna de función                   |
| 26   | `OP_POP`                | —             | Descarta tope de pila                |
| 27   | `OP_HALT`               | —             | Detiene ejecución                    |
| 28   | `OP_LIST`               | n (1)         | Pop n elementos → push(lista)        |
| 29   | `OP_GET_INDEX`          | —             | Pop idx, obj → push(obj[idx])        |
| 30   | `OP_SET_INDEX`          | —             | Pop val, idx, obj → obj[idx] = val   |
| 31   | `OP_LENGTH`             | —             | Pop obj → push(len(obj))             |
| 32   | `OP_APPEND`             | —             | Pop val, lista → push(lista + val)   |
| 33   | `OP_WAIT`               | —             | Pop seg → time.sleep(seg)            |
| 34   | `OP_WEB_SEND`           | —             | Pop data, url → HTTP POST            |
| 35   | `OP_WRITE_FILE`         | —             | Pop content, path → escribe archivo  |
| 36   | `OP_LOWER`              | —             | Pop str → push(str.lower())          |
| 37   | `OP_UPPER`              | —             | Pop str → push(str.upper())          |
| 38   | `OP_GET_OUTPUT`         | —             | Push(output_buffer)                  |
| 39   | `OP_DICT`               | n (1)         | Pop n pares → push(dict)             |
| 40   | `OP_SUPABASE_INSERT`    | —             | Pop data, table, key, url → POST     |
| 41   | `OP_ROUND`              | —             | Pop n → push(round(n))               |
| 42   | `OP_POW`                | —             | Pop exp, base → push(base**exp)      |
| 43   | `OP_SQRT`               | —             | Pop n → push(sqrt(n))                |
| 44   | `OP_TRY_PUSH`           | addr (1)      | Inicia bloque try con handler addr   |
| 45   | `OP_TRY_POP`            | —             | Termina bloque try                   |
| 46   | `OP_THROW`              | —             | Pop msg → raise RuntimeError(msg)    |
| 47   | `OP_CLASS`              | —             | Define clase                         |
| 48   | `OP_NEW`                | n (1)         | Crea instancia de clase              |
| 49   | `OP_GET_ATTR`           | —             | Pop obj, attr → push(obj.attr)       |
| 50   | `OP_SET_ATTR`           | —             | Pop val, obj, attr → obj.attr = val  |
| 51   | `OP_MOD`                | —             | Pop b, a → push(a % b)               |
| 52   | `OP_ERROR_MSG`          | —             | Push(último mensaje de error)        |
| 53   | `OP_READ_FILE`          | —             | Pop path → push(contenido)           |
| 54   | `OP_SUPABASE_SELECT`    | —             | Pop table, key, url → push(json)     |
| 55   | `OP_JSON_DECODE`        | —             | Pop str → push(json.loads(str))      |
| 56   | `OP_IMPORT`             | —             | Importa módulo                       |
| 57   | `OP_TIME`               | —             | Push(time.time())                    |
| 58   | `OP_JSON_ENCODE`        | —             | Pop val → push(json.dumps(val))      |
| 59   | `OP_TYPE`               | —             | Pop val → push(nombre_del_tipo)      |
| 60   | `OP_REPLACE`            | —             | Pop new, old, str → push(replace)    |
| 61   | `OP_ABS`                | —             | Pop n → push(abs(n))                 |
| 62   | `OP_INPUT_NUM`          | —             | Lee y asegura número                 |
| 63   | `OP_START_SERVER`       | —             | Inicia servidor FastAPI              |
| 64   | `OP_SLICE`              | —             | Pop end, start, obj → push(obj[start:end]) |
| 65   | `OP_NEGATE`             | —             | Pop n → push(-n)                     |
| 66   | `OP_JUMP_IF_TRUE`       | addr (1)      | Pop; si verdadero → salto            |
| 67   | `OP_MAKE_FUNC`          | addr, n (2)   | Crea descriptor de función           |
| 68   | `OP_SUPER_ATTR`         | —             | super.method() → clase padre         |
| 69   | `OP_INSTANCEOF`         | —             | Pop obj, cls → push(es instancia)    |
| 70   | `OP_DATE_FORMAT`        | —             | Pop fmt → push(fecha formateada)     |
| 71   | `OP_STRING_SPLIT`       | —             | Pop sep, str → push(split)           |
| 72   | `OP_STRING_JOIN`        | —             | Pop sep, list → push(join)           |
| 73   | `OP_TO_NUMBER`          | —             | Pop str → push(numero)               |
| 74   | `OP_REGEX_SEARCH`       | —             | Pop pattern, str → push(matches)     |
| 75   | `OP_NULL`               | —             | Push(None)                           |
| 76   | `OP_ASYNC_CALL`         | addr, n (2)   | Llama async → crea corutina          |
| 77   | `OP_AWAIT`              | —             | Aguarda corutina                     |
| 78   | `OP_SQLITE_ABRIR`       | —             | Abre base SQLite                     |
| 79   | `OP_SQLITE_EJECUTAR`    | —             | Ejecuta SQL (INSERT/UPDATE/DELETE)   |
| 80   | `OP_SQLITE_CONSULTAR`   | —             | Ejecuta SELECT                       |
| 81   | `OP_SOLICITUD_HTTP`     | —             | Cliente HTTP completo                |
| 82   | `OP_DICT_KEYS`          | —             | dict → push(lista de claves)         |

---

## 5. Estructura de la VM

### 5.1 Memoria

```
Stack de valores:   Pila principal (valores tipados)
Frames de llamadas: Pila de llamadas a función (return_ip, locales)
Pool de constantes: Array de valores literales
Mapa de líneas:     IP → número de línea (para stack traces)
Globals:            Diccionario de variables globales
Classes:            Diccionario de definiciones de clase
```

### 5.2 Formato del Valor en Pila

Cada valor en la pila es un objeto Python (int, float, str, bool, None, list, dict, tuple).

---

## 6. Librería Estándar (13 Módulos)

| Módulo       | Funciones principales                           |
|--------------|--------------------------------------------------|
| `matematicas`  | `factorial`, `maximo`, `minimo`, `promedio`, `es_par`, `es_impar` |
| `cadenas`      | `reversa`, `capitalizar`, `contiene`, `empieza_con`, `termina_con`, `recortar` |
| `colecciones`  | `vacio`, `primero`, `ultimo`, `contiene`, `sin_duplicados`, `invertir` |
| `testing`      | `describir`, `probar`, `afirmar`, `afirmar_igual`, `afirmar_error`, `resumen` |
| `json`         | `json_a_texto`, `texto_a_json`, `json_leer_archivo`, `json_escribir_archivo`, `json_valido` |
| `csv`          | `csv_a_listas`, `csv_a_diccionarios`, `csv_leer`, `csv_escribir`, `csv_listas_a_texto` |
| `sistema`      | `archivo_existe`, `archivo_leer`, `archivo_escribir`, `archivo_copiar` |
| `fecha`        | `ahora`, `hoy`, `hora_actual`, `timestamp_actual`, `formatear_fecha` |
| `http`         | `http_obtener`, `http_post`, `http_put`, `http_eliminar`, `http_exito`, `http_cuerpo`, `http_json` |
| `sqlite`       | `base_abrir`, `base_ejecutar`, `base_consultar`, `base_crear_tabla`, `base_insertar`, `base_seleccionar` |
| `aleatorio`    | `aleatorio_numero`, `aleatorio_flotante`, `aleatorio_escoger`, `aleatorio_mezclar`, `aleatorio_cadena` |
| `expresiones_regulares` | `regex_coincide`, `regex_extraer`, `regex_todas`, `regex_contar` |
| `consola`      | `consola_color`, `consola_preguntar`, `consola_confirmar`, `consola_menu`, `consola_progreso`, `consola_separador` |

---

## 7. Seguridad

### 7.1 Modo Seguro (`--safe`)

Restricciones al ejecutar con `alvz --safe archivo.alvz`:

| Recurso       | Comportamiento en modo seguro                     |
|---------------|----------------------------------------------------|
| Sistema de archivos | Solo lectura/escritura dentro de `alvz_sandbox/` |
| Red           | Bloqueado (HTTP, Supabase)                         |
| Terminal      | `limpiar()` deshabilitado                          |
| Importaciones | Solo módulos de la stdlib                          |
| Tiempo        | Límite de 30 segundos por ejecución                |
| Recursión     | Máximo 200 niveles de profundidad                  |
| Pila          | Máximo 10,000 elementos                            |

---

## 8. Compilación WASM

Alvz compila bytecode a WebAssembly (wasmtime 45+):

- Memoria lineal compartida entre host y módulo
- Layout: stack (0x0000), bytecode (0x4000), constantes (0x5000), strings (0x6000), variables (0x8000), listas (0xA000), heap listas (0xC000), pila de llamadas (0xE000)
- 33+ funciones host para E/S, archivos, HTTP, SQLite, JSON, etc.

```
alvz build programa.alvz --wasm -o salida.wasm
```
