#include "alvz_runtime.h"
#include <ctype.h>

/* ---------------------------------------------------------------
 * Global VM state
 * --------------------------------------------------------------- */
static Stack value_stack;
static Stack frame_stack;  /* stores raw AlvzFrame as bytes in Value */
static Stack try_stack;    /* stores try-catch return addresses */
static int alvz_ip = 0;
static int* bc = NULL;
static int bc_len = 0;
static Value* consts = NULL;
static int const_cnt = 0;
static AlvzProgram* alvz_prog = NULL;

/* ---------------------------------------------------------------
 * Frame
 * --------------------------------------------------------------- */
typedef struct {
    int return_ip;
    Stack locals;
} AlvzFrame;

static AlvzFrame* current_frame(void) {
    if (frame_stack.count == 0) return NULL;
    return (AlvzFrame*)&frame_stack.data[frame_stack.count - 1];
}

static void push_frame(int return_ip, int nlocals) {
    AlvzFrame f;
    f.return_ip = return_ip;
    stack_init(&f.locals, nlocals > 0 ? nlocals : 8);
    for (int i = 0; i < nlocals; i++) stack_push(&f.locals, alvz_null());
    Value v;
    memset(&v, 0, sizeof(Value));
    memcpy(&v, &f, sizeof(AlvzFrame));
    v.type = VAL_NULL;
    stack_push(&frame_stack, v);
}

static void pop_frame(void) {
    if (frame_stack.count == 0) return;
    AlvzFrame* f = (AlvzFrame*)&frame_stack.data[frame_stack.count - 1];
    stack_free(&f->locals);
    frame_stack.count--;
}

/* ---------------------------------------------------------------
 * Value helpers
 * --------------------------------------------------------------- */
Value alvz_null(void)       { Value v; memset(&v, 0, sizeof(Value)); v.type = VAL_NULL; return v; }
Value alvz_bool(bool b)     { Value v; memset(&v, 0, sizeof(Value)); v.type = VAL_BOOL; v.as.boolean = b; return v; }
Value alvz_number(double n) { Value v; memset(&v, 0, sizeof(Value)); v.type = VAL_NUMBER; v.as.number = n; return v; }

Value alvz_string(const char* s) {
    Value v; memset(&v, 0, sizeof(Value));
    v.type = VAL_STRING;
    if (s) { v.as.string = (char*)malloc(strlen(s) + 1); strcpy(v.as.string, s); }
    return v;
}

Value alvz_copy(Value v) {
    Value c = v;
    if (v.type == VAL_STRING && v.as.string) {
        c.as.string = (char*)malloc(strlen(v.as.string) + 1);
        strcpy(c.as.string, v.as.string);
    }
    return c;
}

void alvz_free(Value* v) {
    if (!v) return;
    if (v->type == VAL_STRING && v->as.string) { free(v->as.string); v->as.string = NULL; }
    if (v->type == VAL_LIST && v->as.list.items) {
        for (int i = 0; i < v->as.list.count; i++) alvz_free(&v->as.list.items[i]);
        free(v->as.list.items); v->as.list.items = NULL;
    }
    if (v->type == VAL_DICT && v->as.dict.keys) {
        for (int i = 0; i < v->as.dict.count; i++) free(v->as.dict.keys[i]);
        free(v->as.dict.keys); v->as.dict.keys = NULL;
        free(v->as.dict.values); v->as.dict.values = NULL;
    }
    memset(v, 0, sizeof(Value));
    v->type = VAL_NULL;
}

void alvz_print_value(FILE* out, Value v) {
    switch (v.type) {
        case VAL_NULL:    fprintf(out, "nulo"); break;
        case VAL_BOOL:    fprintf(out, "%s", v.as.boolean ? "verdadero" : "falso"); break;
        case VAL_NUMBER:
            if (v.as.number == (long long)v.as.number)
                fprintf(out, "%lld", (long long)v.as.number);
            else
                fprintf(out, "%g", v.as.number);
            break;
        case VAL_STRING:  fprintf(out, "%s", v.as.string ? v.as.string : ""); break;
        case VAL_LIST:
            fprintf(out, "[");
            for (int i = 0; i < v.as.list.count; i++) {
                if (i > 0) fprintf(out, ", ");
                alvz_print_value(out, v.as.list.items[i]);
            }
            fprintf(out, "]");
            break;
        case VAL_DICT:
            fprintf(out, "{");
            for (int i = 0; i < v.as.dict.count; i++) {
                if (i > 0) fprintf(out, ", ");
                fprintf(out, "%s: ", v.as.dict.keys[i]);
                alvz_print_value(out, v.as.dict.values[i]);
            }
            fprintf(out, "}");
            break;
        case VAL_FUNC:    fprintf(out, "<funcion>"); break;
        case VAL_CLASS:   fprintf(out, "<clase %s>", v.as.klass ? v.as.klass->name : "?"); break;
        case VAL_INSTANCE:fprintf(out, "<objeto %s>", v.as.instance && v.as.instance->klass ? v.as.instance->klass->name : "?"); break;
        default:          fprintf(out, "<valor>"); break;
    }
}

/* ---------------------------------------------------------------
 * List
 * --------------------------------------------------------------- */
Value alvz_list(void) {
    Value v; memset(&v, 0, sizeof(Value));
    v.type = VAL_LIST;
    v.as.list.capacity = 8;
    v.as.list.count = 0;
    v.as.list.items = (Value*)malloc(sizeof(Value) * v.as.list.capacity);
    return v;
}

void alvz_list_append(Value* list, Value item) {
    if (list->type != VAL_LIST) return;
    if (list->as.list.count >= list->as.list.capacity) {
        list->as.list.capacity *= 2;
        list->as.list.items = (Value*)realloc(list->as.list.items, sizeof(Value) * list->as.list.capacity);
    }
    list->as.list.items[list->as.list.count++] = item;
}

Value alvz_list_get(Value list, int index) {
    if (list.type != VAL_LIST) return alvz_null();
    if (index < 0 || index >= list.as.list.count) return alvz_null();
    return list.as.list.items[index];
}

void alvz_list_set(Value* list, int index, Value item) {
    if (list->type != VAL_LIST) return;
    if (index < 0 || index >= list->as.list.count) return;
    alvz_free(&list->as.list.items[index]);
    list->as.list.items[index] = item;
}

int alvz_list_length(Value list) {
    return (list.type == VAL_LIST) ? list.as.list.count : 0;
}

/* ---------------------------------------------------------------
 * Dict
 * --------------------------------------------------------------- */
Value alvz_dict(void) {
    Value v; memset(&v, 0, sizeof(Value));
    v.type = VAL_DICT;
    v.as.dict.capacity = 8;
    v.as.dict.count = 0;
    v.as.dict.keys = (char**)malloc(sizeof(char*) * v.as.dict.capacity);
    v.as.dict.values = (Value*)malloc(sizeof(Value) * v.as.dict.capacity);
    return v;
}

static int dict_find(Value dict, const char* key) {
    for (int i = 0; i < dict.as.dict.count; i++) {
        if (strcmp(dict.as.dict.keys[i], key) == 0) return i;
    }
    return -1;
}

void alvz_dict_set(Value* dict, const char* key, Value val) {
    if (dict->type != VAL_DICT) return;
    int idx = dict_find(*dict, key);
    if (idx >= 0) {
        alvz_free(&dict->as.dict.values[idx]);
        dict->as.dict.values[idx] = val;
        return;
    }
    if (dict->as.dict.count >= dict->as.dict.capacity) {
        dict->as.dict.capacity *= 2;
        dict->as.dict.keys = (char**)realloc(dict->as.dict.keys, sizeof(char*) * dict->as.dict.capacity);
        dict->as.dict.values = (Value*)realloc(dict->as.dict.values, sizeof(Value) * dict->as.dict.capacity);
    }
    idx = dict->as.dict.count++;
    dict->as.dict.keys[idx] = (char*)malloc(strlen(key) + 1);
    strcpy(dict->as.dict.keys[idx], key);
    dict->as.dict.values[idx] = val;
}

Value alvz_dict_get(Value dict, const char* key) {
    if (dict.type != VAL_DICT) return alvz_null();
    int idx = dict_find(dict, key);
    if (idx < 0) return alvz_null();
    return dict.as.dict.values[idx];
}

/* ---------------------------------------------------------------
 * Classes / Instances
 * --------------------------------------------------------------- */
AlvzClass* alvz_class_new(const char* name, AlvzClass* parent) {
    AlvzClass* c = (AlvzClass*)calloc(1, sizeof(AlvzClass));
    c->name = (char*)malloc(strlen(name) + 1);
    strcpy(c->name, name);
    c->parent = parent;
    c->method_count = 0;
    c->method_names = NULL;
    c->method_addrs = NULL;
    c->instance_size = 0;
    return c;
}

void alvz_class_add_method(AlvzClass* klass, const char* name, int addr) {
    klass->method_count++;
    klass->method_names = (char**)realloc(klass->method_names, sizeof(char*) * klass->method_count);
    klass->method_addrs = (int*)realloc(klass->method_addrs, sizeof(int) * klass->method_count);
    klass->method_names[klass->method_count - 1] = (char*)malloc(strlen(name) + 1);
    strcpy(klass->method_names[klass->method_count - 1], name);
    klass->method_addrs[klass->method_count - 1] = addr;
}

AlvzClass* alvz_class_find_method(AlvzClass* klass, const char* name, int* out_addr) {
    while (klass) {
        for (int i = 0; i < klass->method_count; i++) {
            if (strcmp(klass->method_names[i], name) == 0) {
                *out_addr = klass->method_addrs[i];
                return klass;
            }
        }
        klass = klass->parent;
    }
    *out_addr = -1;
    return NULL;
}

Value alvz_instance_new(AlvzClass* klass) {
    AlvzInstance* inst = (AlvzInstance*)calloc(1, sizeof(AlvzInstance));
    inst->klass = klass;
    inst->field_count = klass->instance_size;
    inst->fields = (Value*)calloc(klass->instance_size > 0 ? klass->instance_size : 8, sizeof(Value));
    for (int i = 0; i < inst->field_count; i++) inst->fields[i] = alvz_null();
    Value v; memset(&v, 0, sizeof(Value));
    v.type = VAL_INSTANCE;
    v.as.instance = inst;
    return v;
}

Value alvz_instance_get_attr(Value instance, const char* name) {
    if (instance.type != VAL_INSTANCE || !instance.as.instance) return alvz_null();
    AlvzInstance* inst = instance.as.instance;
    /* Check methods first */
    int addr;
    AlvzClass* c = alvz_class_find_method(inst->klass, name, &addr);
    if (c) {
        Value v; memset(&v, 0, sizeof(Value));
        v.type = VAL_FUNC;
        v.as.func.addr = addr;
        v.as.func.num_params = 0;
        return v;
    }
    /* Check fields */
    for (int i = 0; i < inst->field_count; i++) {
        /* No field names stored; for now return null */
        (void)i;
    }
    return alvz_null();
}

void alvz_instance_set_attr(Value* instance, const char* name, Value val) {
    (void)instance; (void)name; (void)val;
    /* TODO: store field in instance */
}

/* ---------------------------------------------------------------
 * Stack
 * --------------------------------------------------------------- */
void stack_init(Stack* s, int cap) {
    s->data = (Value*)malloc(sizeof(Value) * (cap > 0 ? cap : 64));
    s->count = 0;
    s->capacity = cap > 0 ? cap : 64;
}

void stack_push(Stack* s, Value v) {
    if (s->count >= s->capacity) {
        s->capacity *= 2;
        s->data = (Value*)realloc(s->data, sizeof(Value) * s->capacity);
    }
    s->data[s->count++] = v;
}

Value stack_pop(Stack* s) {
    if (s->count == 0) return alvz_null();
    return s->data[--s->count];
}

Value stack_peek(Stack* s, int depth) {
    if (s->count == 0) return alvz_null();
    int idx = s->count - 1 - depth;
    return (idx >= 0) ? s->data[idx] : alvz_null();
}

void stack_free(Stack* s) {
    if (s->data) {
        for (int i = 0; i < s->count; i++) alvz_free(&s->data[i]);
        free(s->data); s->data = NULL;
    }
    s->count = s->capacity = 0;
}

void stack_clear(Stack* s) {
    for (int i = 0; i < s->count; i++) alvz_free(&s->data[i]);
    s->count = 0;
}

/* ---------------------------------------------------------------
 * Built-in functions
 * --------------------------------------------------------------- */
void builtin_imprimir(Value v) { alvz_print_value(stdout, v); printf("\n"); fflush(stdout); }
void builtin_limpiar(void) { printf("\033[2J\033[H"); fflush(stdout); }

void builtin_agregar(Value* list, Value item) {
    alvz_list_append(list, item);
}

double builtin_longitud(Value v) {
    if (v.type == VAL_STRING) return (double)strlen(v.as.string ? v.as.string : "");
    if (v.type == VAL_LIST) return (double)v.as.list.count;
    return 0;
}

Value builtin_tipo(Value v) {
    switch (v.type) {
        case VAL_NULL:    return alvz_string("nulo");
        case VAL_BOOL:    return alvz_string("booleano");
        case VAL_NUMBER:  return alvz_string("numero");
        case VAL_STRING:  return alvz_string("texto");
        case VAL_LIST:    return alvz_string("lista");
        case VAL_DICT:    return alvz_string("diccionario");
        case VAL_FUNC:    return alvz_string("funcion");
        case VAL_CLASS:   return alvz_string("clase");
        case VAL_INSTANCE:return alvz_string("objeto");
        default:          return alvz_string("cualquiera");
    }
}

void builtin_esperar(double segundos) {
#ifdef _WIN32
    Sleep((DWORD)(segundos * 1000));
#else
    struct timespec ts;
    ts.tv_sec = (time_t)segundos;
    ts.tv_nsec = (long)((segundos - ts.tv_sec) * 1e9);
    nanosleep(&ts, NULL);
#endif
}

/* ---------------------------------------------------------------
 * Value stack helpers
 * --------------------------------------------------------------- */
static Value pop_val(void) { return stack_pop(&value_stack); }
static void push_val(Value v) { stack_push(&value_stack, v); }

/* ---------------------------------------------------------------
 * Main bytecode interpreter
 * --------------------------------------------------------------- */
void alvz_run_program(AlvzProgram* prog) {
    bc = prog->bytecode;
    bc_len = prog->bc_len;
    consts = prog->constants;
    const_cnt = prog->const_count;
    alvz_prog = prog;

    stack_init(&value_stack, 256);
    stack_init(&frame_stack, 64);
    stack_init(&try_stack, 16);

    /* Global frame */
    push_frame(-1, 0);

    alvz_ip = 0;
    bool running = true;

    while (running && alvz_ip < bc_len) {
        int op = bc[alvz_ip++];

        switch (op) {
            case OP_CONSTANT: {
                int idx = bc[alvz_ip++];
                push_val((idx >= 0 && idx < const_cnt) ? alvz_copy(consts[idx]) : alvz_null());
                break;
            }

            case OP_NULL:
                push_val(alvz_null());
                break;

            case OP_NEGATE: {
                Value v = pop_val();
                if (v.type == VAL_NUMBER) v.as.number = -v.as.number;
                push_val(v);
                break;
            }

            case OP_ADD: {
                Value b = pop_val(); Value a = pop_val(); Value r = alvz_null();
                if (a.type == VAL_STRING || b.type == VAL_STRING) {
                    const char* sa = (a.type == VAL_STRING && a.as.string) ? a.as.string : "";
                    const char* sb = (b.type == VAL_STRING && b.as.string) ? b.as.string : "";
                    char* buf = (char*)malloc(strlen(sa) + strlen(sb) + 1);
                    strcpy(buf, sa); strcat(buf, sb);
                    r = alvz_string(buf); free(buf);
                } else if (a.type == VAL_NUMBER && b.type == VAL_NUMBER)
                    r = alvz_number(a.as.number + b.as.number);
                alvz_free(&a); alvz_free(&b); push_val(r); break;
            }

            case OP_SUB: { Value b = pop_val(); Value a = pop_val(); push_val((a.type == VAL_NUMBER && b.type == VAL_NUMBER) ? alvz_number(a.as.number - b.as.number) : alvz_null()); alvz_free(&a); alvz_free(&b); break; }
            case OP_MUL: { Value b = pop_val(); Value a = pop_val(); push_val((a.type == VAL_NUMBER && b.type == VAL_NUMBER) ? alvz_number(a.as.number * b.as.number) : alvz_null()); alvz_free(&a); alvz_free(&b); break; }
            case OP_DIV: { Value b = pop_val(); Value a = pop_val(); push_val((a.type == VAL_NUMBER && b.type == VAL_NUMBER && b.as.number != 0) ? alvz_number(a.as.number / b.as.number) : alvz_null()); alvz_free(&a); alvz_free(&b); break; }
            case OP_MOD: { Value b = pop_val(); Value a = pop_val(); push_val((a.type == VAL_NUMBER && b.type == VAL_NUMBER) ? alvz_number(fmod(a.as.number, b.as.number)) : alvz_null()); alvz_free(&a); alvz_free(&b); break; }

            case OP_EQ: { Value b = pop_val(); Value a = pop_val(); bool eq = (a.type == b.type && a.type == VAL_NUMBER && a.as.number == b.as.number) || (a.type == VAL_BOOL && a.as.boolean == b.as.boolean) || (a.type == VAL_STRING && strcmp(a.as.string ? a.as.string : "", b.as.string ? b.as.string : "") == 0); alvz_free(&a); alvz_free(&b); push_val(alvz_bool(eq)); break; }
            case OP_NE: { Value b = pop_val(); Value a = pop_val(); bool ne = !((a.type == b.type && a.type == VAL_NUMBER && a.as.number == b.as.number) || (a.type == VAL_BOOL && a.as.boolean == b.as.boolean) || (a.type == VAL_STRING && strcmp(a.as.string ? a.as.string : "", b.as.string ? b.as.string : "") == 0)); alvz_free(&a); alvz_free(&b); push_val(alvz_bool(ne)); break; }

            case OP_GT: { Value a = pop_val(); Value b = pop_val(); push_val((a.type == VAL_NUMBER) ? alvz_bool(a.as.number > b.as.number) : alvz_bool(false)); alvz_free(&a); alvz_free(&b); break; }
            case OP_LT: { Value a = pop_val(); Value b = pop_val(); push_val((a.type == VAL_NUMBER) ? alvz_bool(a.as.number < b.as.number) : alvz_bool(false)); alvz_free(&a); alvz_free(&b); break; }
            case OP_GTE:{ Value a = pop_val(); Value b = pop_val(); push_val((a.type == VAL_NUMBER) ? alvz_bool(a.as.number >= b.as.number) : alvz_bool(false)); alvz_free(&a); alvz_free(&b); break; }
            case OP_LTE:{ Value a = pop_val(); Value b = pop_val(); push_val((a.type == VAL_NUMBER) ? alvz_bool(a.as.number <= b.as.number) : alvz_bool(false)); alvz_free(&a); alvz_free(&b); break; }

            case OP_AND: { Value b = pop_val(); Value a = pop_val(); push_val(alvz_bool(a.as.boolean && b.as.boolean)); alvz_free(&a); alvz_free(&b); break; }
            case OP_OR:  { Value b = pop_val(); Value a = pop_val(); push_val(alvz_bool(a.as.boolean || b.as.boolean)); alvz_free(&a); alvz_free(&b); break; }

            case OP_PRINT: { Value v = pop_val(); builtin_imprimir(v); alvz_free(&v); break; }
            case OP_POP:   { Value v = pop_val(); alvz_free(&v); break; }

            case OP_JUMP:
                alvz_ip = bc[alvz_ip];
                break;

            case OP_JUMP_IF_FALSE: {
                Value v = pop_val();
                if (!v.as.boolean) alvz_ip = bc[alvz_ip]; else alvz_ip++;
                alvz_free(&v); break;
            }

            case OP_JUMP_IF_TRUE: {
                Value v = pop_val();
                if (v.as.boolean) alvz_ip = bc[alvz_ip]; else alvz_ip++;
                alvz_free(&v); break;
            }

            case OP_STORE: {
                int idx = bc[alvz_ip++];
                Value v = pop_val();
                AlvzFrame* f = current_frame();
                while (f && f->locals.count <= idx) stack_push(&f->locals, alvz_null());
                if (f) { alvz_free(&f->locals.data[idx]); f->locals.data[idx] = v; }
                else alvz_free(&v);
                break;
            }

            case OP_LOAD: {
                int idx = bc[alvz_ip++];
                AlvzFrame* f = current_frame();
                push_val((f && idx >= 0 && idx < f->locals.count) ? alvz_copy(f->locals.data[idx]) : alvz_null());
                break;
            }

            case OP_STORE_GLOBAL: {
                int idx = bc[alvz_ip++];
                Value v = pop_val();
                AlvzFrame* gf = (AlvzFrame*)&frame_stack.data[0];
                while (gf->locals.count <= idx) stack_push(&gf->locals, alvz_null());
                alvz_free(&gf->locals.data[idx]); gf->locals.data[idx] = v;
                break;
            }

            case OP_LOAD_GLOBAL: {
                int idx = bc[alvz_ip++];
                AlvzFrame* gf = (AlvzFrame*)&frame_stack.data[0];
                push_val((idx >= 0 && idx < gf->locals.count) ? alvz_copy(gf->locals.data[idx]) : alvz_null());
                break;
            }

            case OP_CALL: {
                int addr = bc[alvz_ip++];
                int nargs = bc[alvz_ip++];
                alvz_ip++; /* skip padding */
                Value* args = (Value*)malloc(sizeof(Value) * nargs);
                for (int i = nargs - 1; i >= 0; i--) args[i] = pop_val();
                int return_ip = alvz_ip;
                push_frame(return_ip, nargs);
                AlvzFrame* f = current_frame();
                for (int i = 0; i < nargs && i < f->locals.count; i++) {
                    alvz_free(&f->locals.data[i]);
                    f->locals.data[i] = args[i];
                }
                free(args);
                alvz_ip = addr;
                break;
            }

            case OP_RETURN: {
                Value result = pop_val();
                int return_ip = -1;
                AlvzFrame* f = current_frame();
                if (f) return_ip = f->return_ip;
                pop_frame();
                if (frame_stack.count == 0) { running = false; alvz_free(&result); }
                else { push_val(result); if (return_ip >= 0) alvz_ip = return_ip; }
                break;
            }

            case OP_HALT:
                running = false;
                break;

            case OP_LIST: {
                int num = bc[alvz_ip++];
                Value lst = alvz_list();
                for (int i = 0; i < num; i++) {
                    Value item = pop_val();
                    alvz_list_append(&lst, item);
                }
                push_val(lst);
                break;
            }

            case OP_DICT: {
                int num = bc[alvz_ip++];
                Value d = alvz_dict();
                /* Items on stack as key, val, key, val... */
                for (int i = 0; i < num; i++) {
                    Value val = pop_val();
                    Value key = pop_val();
                    if (key.type == VAL_STRING) {
                        alvz_dict_set(&d, key.as.string, val);
                    }
                    alvz_free(&key);
                }
                push_val(d);
                break;
            }

            case OP_GET_INDEX: {
                Value idx = pop_val();
                Value container = pop_val();
                if (container.type == VAL_LIST && idx.type == VAL_NUMBER) {
                    push_val(alvz_list_get(container, (int)idx.as.number));
                } else if (container.type == VAL_DICT && idx.type == VAL_STRING) {
                    push_val(alvz_dict_get(container, idx.as.string));
                } else push_val(alvz_null());
                alvz_free(&idx); alvz_free(&container);
                break;
            }

            case OP_SET_INDEX: {
                Value val = pop_val();
                Value idx = pop_val();
                Value* container = &value_stack.data[value_stack.count - 1];
                if (container->type == VAL_LIST && idx.type == VAL_NUMBER) {
                    alvz_list_set(container, (int)idx.as.number, val);
                } else if (container->type == VAL_DICT && idx.type == VAL_STRING) {
                    alvz_dict_set(container, idx.as.string, val);
                }
                alvz_free(&idx);
                break;
            }

            case OP_LENGTH: {
                Value v = pop_val();
                push_val(alvz_number(builtin_longitud(v)));
                alvz_free(&v); break;
            }

            case OP_APPEND: {
                Value item = pop_val();
                Value* lst = &value_stack.data[value_stack.count - 1];
                builtin_agregar(lst, item);
                alvz_free(&item); alvz_free(lst);
                push_val(alvz_null());
                break;
            }

            case OP_TYPE: {
                Value v = pop_val();
                push_val(builtin_tipo(v));
                alvz_free(&v); break;
            }

            case OP_CLASS: {
                int name_idx = bc[alvz_ip++];
                int parent_idx = bc[alvz_ip++];
                const char* name = (consts && name_idx < const_cnt && consts[name_idx].type == VAL_STRING) ? consts[name_idx].as.string : "Clase";
                (void)parent_idx;
                push_val(alvz_null()); /* TODO: store class */
                break;
            }

            case OP_NEW: {
                int nargs = bc[alvz_ip++];
                Value klass_val = pop_val();
                (void)klass_val;
                for (int i = 0; i < nargs; i++) pop_val();
                push_val(alvz_null());
                break;
            }

            case OP_GET_ATTR: {
                Value prop = pop_val();
                Value obj = pop_val();
                const char* pname = (prop.type == VAL_STRING) ? prop.as.string : "";
                if (obj.type == VAL_INSTANCE) {
                    push_val(alvz_instance_get_attr(obj, pname));
                } else push_val(alvz_null());
                alvz_free(&prop); alvz_free(&obj);
                break;
            }

            case OP_SET_ATTR: {
                Value val = pop_val();
                Value prop = pop_val();
                Value* obj = &value_stack.data[value_stack.count - 1];
                const char* pname = (prop.type == VAL_STRING) ? prop.as.string : "";
                if (obj->type == VAL_INSTANCE) alvz_instance_set_attr(obj, pname, val);
                alvz_free(&prop);
                break;
            }

            case OP_MAKE_FUNC: {
                int addr = bc[alvz_ip++];
                int nparams = bc[alvz_ip++];
                Value v; memset(&v, 0, sizeof(Value));
                v.type = VAL_FUNC;
                v.as.func.addr = addr;
                v.as.func.num_params = nparams;
                push_val(v);
                break;
            }

            case OP_ASYNC_CALL: {
                /* Treat as sync call for native compilation */
                int addr = bc[alvz_ip++];
                int nargs = bc[alvz_ip++];
                alvz_ip++;
                Value* args = (Value*)malloc(sizeof(Value) * nargs);
                for (int i = nargs - 1; i >= 0; i--) args[i] = pop_val();
                int return_ip = alvz_ip;
                push_frame(return_ip, nargs);
                AlvzFrame* f = current_frame();
                for (int i = 0; i < nargs && i < f->locals.count; i++) {
                    alvz_free(&f->locals.data[i]);
                    f->locals.data[i] = args[i];
                }
                free(args);
                alvz_ip = addr;
                break;
            }

            case OP_AWAIT:
                /* No-op in sync mode, value already on stack */
                break;

            case OP_TRY_PUSH: {
                int handler_addr = bc[alvz_ip++];
                stack_push(&try_stack, alvz_number((double)handler_addr));
                break;
            }

            case OP_TRY_POP:
                if (try_stack.count > 0) pop_val(); /* remove from try_stack */
                stack_pop(&try_stack);
                break;

            case OP_THROW: {
                Value err = pop_val();
                alvz_free(&err);
                /* Jump to try handler */
                if (try_stack.count > 0) {
                    Value handler = try_stack.data[try_stack.count - 1];
                    alvz_ip = (int)handler.as.number;
                } else {
                    running = false;
                }
                break;
            }

            case OP_INSTANCEOF: {
                Value klass = pop_val();
                Value obj = pop_val();
                bool result = false;
                if (obj.type == VAL_INSTANCE && obj.as.instance && klass.type == VAL_CLASS && klass.as.klass) {
                    AlvzClass* c = obj.as.instance->klass;
                    while (c) {
                        if (c == klass.as.klass) { result = true; break; }
                        c = c->parent;
                    }
                }
                alvz_free(&klass); alvz_free(&obj);
                push_val(alvz_bool(result));
                break;
            }

            /* Stubs for less common ops */
            case OP_INPUT:
            case OP_INPUT_NUM: {
                push_val(alvz_number(0));
                break;
            }
            case OP_RANDOM: {
                push_val(alvz_number((double)rand() / RAND_MAX));
                break;
            }
            case OP_CLEAR: builtin_limpiar(); break;
            case OP_WAIT: { double secs = pop_val().as.number; builtin_esperar(secs); break; }
            case OP_TIME: { push_val(alvz_number((double)time(NULL))); break; }
            case OP_ROUND: { Value v = pop_val(); if (v.type == VAL_NUMBER) v.as.number = round(v.as.number); push_val(v); break; }
            case OP_POW: { Value b = pop_val(); Value a = pop_val(); push_val(alvz_number(pow(a.as.number, b.as.number))); alvz_free(&a); alvz_free(&b); break; }
            case OP_SQRT: { Value v = pop_val(); if (v.type == VAL_NUMBER) v.as.number = sqrt(v.as.number); push_val(v); break; }
            case OP_ABS: { Value v = pop_val(); if (v.type == VAL_NUMBER) v.as.number = fabs(v.as.number); push_val(v); break; }
            case OP_LOWER: { Value v = pop_val(); if (v.type == VAL_STRING) { for (char* p = v.as.string; *p; p++) *p = tolower(*p); } push_val(v); break; }
            case OP_UPPER: { Value v = pop_val(); if (v.type == VAL_STRING) { for (char* p = v.as.string; *p; p++) *p = toupper(*p); } push_val(v); break; }
            case OP_REPLACE: {
                Value new_s = pop_val(); Value old_s = pop_val(); Value text = pop_val();
                push_val(text); alvz_free(&old_s); alvz_free(&new_s);
                break;
            }
            case OP_STRING_SPLIT: {
                Value sep = pop_val(); Value text = pop_val();
                push_val(alvz_null()); alvz_free(&sep); alvz_free(&text);
                break;
            }
            case OP_STRING_JOIN: {
                Value sep = pop_val(); Value lst = pop_val();
                push_val(alvz_null()); alvz_free(&sep); alvz_free(&lst);
                break;
            }
            case OP_TO_NUMBER: {
                Value v = pop_val();
                if (v.type == VAL_STRING) push_val(alvz_number(atof(v.as.string)));
                else push_val(v);
                alvz_free(&v);
                break;
            }
            case OP_REGEX_SEARCH: {
                pop_val(); pop_val();
                push_val(alvz_null());
                break;
            }
            case OP_DATE_FORMAT: {
                pop_val();
                push_val(alvz_string(""));
                break;
            }
            case OP_WEB_SEND:
            case OP_WRITE_FILE:
            case OP_READ_FILE:
            case OP_GET_OUTPUT:
            case OP_SUPABASE_INSERT:
            case OP_SUPABASE_SELECT:
            case OP_JSON_DECODE:
            case OP_JSON_ENCODE:
            case OP_START_SERVER:
            case OP_SLICE:
            case OP_ERROR_MSG:
            case OP_SUPER_ATTR:
            case OP_IMPORT:
                push_val(alvz_null());
                break;

            default:
                break;
        }
    }

    /* Cleanup */
    while (frame_stack.count > 0) pop_frame();
    stack_free(&frame_stack);
    stack_free(&value_stack);
    stack_free(&try_stack);
}
