#ifndef ALVZ_RUNTIME_H
#define ALVZ_RUNTIME_H

#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ---------------------------------------------------------------
 * Value type
 * --------------------------------------------------------------- */
typedef enum {
    VAL_NULL,
    VAL_BOOL,
    VAL_NUMBER,
    VAL_STRING,
    VAL_LIST,
    VAL_DICT,
    VAL_FUNC,
    VAL_CLASS,
    VAL_INSTANCE,
} ValueType;

/* Forward declarations */
struct AlvzClass;
struct AlvzInstance;

typedef struct Value {
    ValueType type;
    int refcount;
    union {
        bool boolean;
        double number;
        char* string;
        struct {
            struct Value** items;
            int count;
            int capacity;
        } list;
        struct {
            char** keys;
            struct Value* values;
            int count;
            int capacity;
        } dict;
        struct {
            int addr;
            int num_params;
        } func;
        struct AlvzClass* klass;
        struct AlvzInstance* instance;
    } as;
} Value;

/* Class metadata */
typedef struct AlvzClass {
    char* name;
    char** method_names;
    int* method_addrs;
    int method_count;
    struct AlvzClass* parent;
    int instance_size; /* number of attribute slots */
} AlvzClass;

/* Instance */
typedef struct AlvzInstance {
    AlvzClass* klass;
    Value* fields;
    int field_count;
} AlvzInstance;

/* Stack */
typedef struct {
    Value* data;
    int count;
    int capacity;
} Stack;

/* ---------------------------------------------------------------
 * Value API
 * --------------------------------------------------------------- */
Value alvz_null(void);
Value alvz_bool(bool b);
Value alvz_number(double n);
Value alvz_string(const char* s);
Value alvz_copy(Value v);
void   alvz_free(Value* v);
void   alvz_print_value(FILE* out, Value v);

/* ---------------------------------------------------------------
 * List API
 * --------------------------------------------------------------- */
Value alvz_list(void);
void  alvz_list_append(Value* list, Value item);
Value alvz_list_get(Value list, int index);
void  alvz_list_set(Value* list, int index, Value item);
int   alvz_list_length(Value list);

/* ---------------------------------------------------------------
 * Dict API
 * --------------------------------------------------------------- */
Value alvz_dict(void);
void  alvz_dict_set(Value* dict, const char* key, Value val);
Value alvz_dict_get(Value dict, const char* key);

/* ---------------------------------------------------------------
 * Class / Instance API
 * --------------------------------------------------------------- */
AlvzClass* alvz_class_new(const char* name, AlvzClass* parent);
void       alvz_class_add_method(AlvzClass* klass, const char* name, int addr);
AlvzClass* alvz_class_find_method(AlvzClass* klass, const char* name, int* out_addr);
Value      alvz_instance_new(AlvzClass* klass);
Value      alvz_instance_get_attr(Value instance, const char* name);
void       alvz_instance_set_attr(Value* instance, const char* name, Value val);

/* ---------------------------------------------------------------
 * Stack
 * --------------------------------------------------------------- */
void   stack_init(Stack* s, int cap);
void   stack_push(Stack* s, Value v);
Value  stack_pop(Stack* s);
Value  stack_peek(Stack* s, int depth);
void   stack_free(Stack* s);
void   stack_clear(Stack* s);

/* ---------------------------------------------------------------
 * Built-in functions
 * --------------------------------------------------------------- */
void   builtin_imprimir(Value v);
void   builtin_limpiar(void);
void   builtin_agregar(Value* list, Value item);
double builtin_longitud(Value v);
Value  builtin_tipo(Value v);
void   builtin_esperar(double segundos);

/* ---------------------------------------------------------------
 * Bytecode opcodes (must match Python OpCode enum)
 * --------------------------------------------------------------- */
#define OP_CONSTANT      1
#define OP_STORE         2
#define OP_LOAD          3
#define OP_STORE_GLOBAL  4
#define OP_LOAD_GLOBAL   5
#define OP_PRINT         6
#define OP_ADD           7
#define OP_SUB           8
#define OP_MUL           9
#define OP_DIV          10
#define OP_EQ           11
#define OP_NE           12
#define OP_GT           13
#define OP_LT           14
#define OP_GTE          15
#define OP_LTE          16
#define OP_AND          17
#define OP_OR           18
#define OP_JUMP         19
#define OP_JUMP_IF_FALSE 20
#define OP_INPUT        21
#define OP_RANDOM       22
#define OP_CLEAR        23
#define OP_CALL         24
#define OP_RETURN       25
#define OP_POP          26
#define OP_HALT         27
#define OP_LIST         28
#define OP_GET_INDEX    29
#define OP_SET_INDEX    30
#define OP_LENGTH       31
#define OP_APPEND       32
#define OP_WAIT         33
#define OP_WEB_SEND     34
#define OP_WRITE_FILE   35
#define OP_LOWER        36
#define OP_UPPER        37
#define OP_GET_OUTPUT   38
#define OP_DICT         39
#define OP_SUPABASE_INSERT 40
#define OP_ROUND        41
#define OP_POW          42
#define OP_SQRT         43
#define OP_TRY_PUSH     44
#define OP_TRY_POP      45
#define OP_THROW        46
#define OP_CLASS        47
#define OP_NEW          48
#define OP_GET_ATTR     49
#define OP_SET_ATTR     50
#define OP_MOD          51
#define OP_ERROR_MSG    52
#define OP_READ_FILE    53
#define OP_SUPABASE_SELECT 54
#define OP_JSON_DECODE  55
#define OP_IMPORT       56
#define OP_TIME         57
#define OP_JSON_ENCODE  58
#define OP_TYPE         59
#define OP_REPLACE      60
#define OP_ABS          61
#define OP_INPUT_NUM    62
#define OP_START_SERVER 63
#define OP_SLICE        64
#define OP_NEGATE       65
#define OP_JUMP_IF_TRUE 66
#define OP_MAKE_FUNC    67
#define OP_SUPER_ATTR   68
#define OP_INSTANCEOF   69
#define OP_DATE_FORMAT  70
#define OP_STRING_SPLIT 71
#define OP_STRING_JOIN  72
#define OP_TO_NUMBER    73
#define OP_REGEX_SEARCH 74
#define OP_NULL         75
#define OP_ASYNC_CALL   76
#define OP_AWAIT        77

/* ---------------------------------------------------------------
 * Program structure
 * --------------------------------------------------------------- */
typedef struct {
    int* bytecode;
    int bc_len;
    Value* constants;
    int const_count;
    char** func_names;
    int* func_addrs;
    int* func_nparams;
    int func_count;
    AlvzClass** classes;
    int class_count;
} AlvzProgram;

void alvz_run_program(AlvzProgram* prog);

#endif /* ALVZ_RUNTIME_H */
