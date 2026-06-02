"""
Definicion de bytecode para la Maquina Virtual de Alvz.
"""

import enum


class OpCode(enum.IntEnum):
    """Conjunto completo de instrucciones de la VM de pila de Alvz."""
    # Constantes y variables
    OP_CONSTANT = 1      # Carga una constante a la pila
    OP_STORE = 2         # Guarda en variable local
    OP_LOAD = 3          # Carga desde variable local
    OP_STORE_GLOBAL = 4  # Guarda en variable global
    OP_LOAD_GLOBAL = 5   # Carga desde variable global

    # Aritmetica
    OP_ADD = 7           # Suma
    OP_SUB = 8           # Resta
    OP_MUL = 9           # Multiplicacion
    OP_DIV = 10          # Division
    OP_MOD = 51          # Modulo

    # Comparacion
    OP_EQ = 11           # Igual
    OP_NE = 12           # Diferente
    OP_GT = 13           # Mayor que
    OP_LT = 14           # Menor que
    OP_GTE = 15          # Mayor o igual
    OP_LTE = 16          # Menor o igual

    # Logica
    OP_AND = 17          # AND logico
    OP_OR = 18           # OR logico

    # Control de flujo
    OP_JUMP = 19         # Salto incondicional
    OP_JUMP_IF_FALSE = 20  # Salto si falso
    OP_CALL = 24         # Llamada a funcion
    OP_RETURN = 25       # Retorno de funcion
    OP_POP = 26          # Descarta tope de pila
    OP_HALT = 27         # Detener ejecucion

    # Entrada/Salida
    OP_PRINT = 6         # Imprime valor
    OP_INPUT = 21        # Lee entrada (convierte a tipo)
    OP_INPUT_NUM = 62    # Lee y asegura numero
    OP_CLEAR = 23        # Limpia terminal

    # Numeros aleatorios
    OP_RANDOM = 22       # Numero aleatorio [min, max]

    # Listas
    OP_LIST = 28         # Crea lista de N elementos
    OP_GET_INDEX = 29    # Obtiene elemento por indice
    OP_SET_INDEX = 30    # Establece elemento por indice
    OP_LENGTH = 31       # Longitud de lista/texto
    OP_APPEND = 32       # Agrega al final de lista
    OP_SLICE = 64        # Slicing de lista/texto

    # Tiempo
    OP_WAIT = 33         # Pausa N segundos
    OP_TIME = 57         # Tiempo actual (epoch)

    # Web
    OP_WEB_SEND = 34     # HTTP POST
    OP_START_SERVER = 63 # Inicia servidor FastAPI

    # Archivos
    OP_WRITE_FILE = 35   # Escribe archivo
    OP_READ_FILE = 53    # Lee archivo

    # Texto
    OP_LOWER = 36        # A minusculas
    OP_UPPER = 37        # A mayusculas
    OP_REPLACE = 60      # Reemplaza subcadena
    OP_GET_OUTPUT = 38   # Captura salida impresa

    # Diccionarios
    OP_DICT = 39         # Crea diccionario

    # Supabase
    OP_SUPABASE_INSERT = 40   # Inserta en Supabase
    OP_SUPABASE_SELECT = 54   # Consulta Supabase

    # Matematicas
    OP_ROUND = 41        # Redondear
    OP_POW = 42          # Potencia
    OP_SQRT = 43         # Raiz cuadrada
    OP_ABS = 61          # Valor absoluto

    # Manejo de excepciones
    OP_TRY_PUSH = 44     # Inicia bloque try
    OP_TRY_POP = 45      # Termina bloque try
    OP_THROW = 46        # Lanza excepcion
    OP_ERROR_MSG = 52    # Mensaje del ultimo error

    # Clases y objetos
    OP_CLASS = 47        # Define clase
    OP_NEW = 48          # Crea instancia
    OP_GET_ATTR = 49     # Obtiene atributo
    OP_SET_ATTR = 50     # Establece atributo

    # JSON y tiempo
    OP_JSON_DECODE = 55  # JSON a estructura
    OP_JSON_ENCODE = 58  # Estructura a JSON
    OP_TYPE = 59         # Obtiene tipo

    # Modulos
    OP_IMPORT = 56       # Importa archivo .alvz

    # Nuevas caracteristicas
    OP_NEGATE = 65       # Negacion unaria
    OP_JUMP_IF_TRUE = 66 # Salto si verdadero (para romper/continuar)
    OP_MAKE_FUNC = 67    # Crea descriptor de funcion en pila

    # Clases - super e instanceof
    OP_SUPER_ATTR = 68   # super.method -> busca en clase padre
    OP_INSTANCEOF = 69   # obj instancia Clase

    # StdLib
    OP_DATE_FORMAT = 70  # fecha_actual(formato)
    OP_STRING_SPLIT = 71 # dividir(texto, separador)
    OP_STRING_JOIN = 72  # unir(lista, separador)
    OP_TO_NUMBER = 73    # a_numero(texto)
    OP_REGEX_SEARCH = 74 # regex_buscar(texto, patron)
    OP_NULL = 75         # Carga nulo (None) a la pila
    OP_ASYNC_CALL = 76   # Llama a funcion async, crea corutina
    OP_AWAIT = 77        # Aguarda una corutina

    # StdLib avanzada
    OP_SQLITE_ABRIR = 78     # Abre base de datos SQLite
    OP_SQLITE_EJECUTAR = 79  # Ejecuta sentencia SQL (INSERT/UPDATE/DELETE)
    OP_SQLITE_CONSULTAR = 80 # Ejecuta consulta SELECT
    OP_SOLICITUD_HTTP = 81   # Cliente HTTP completo (GET, POST, PUT, DELETE)
    OP_DICT_KEYS = 82        # Convierte diccionario a lista de claves

    # Depuracion (DAP)
    OP_DEBUG_BREAK = 83      # Breakpoint insertado por el depurador

