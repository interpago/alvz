import pytest
from alvz.core.bytecode import OpCode
from alvz.core.vm import VM


def make_vm(bc, consts=None, line_map=None, funcs=None):
    vm = VM(bc or [], consts or [], line_map or {}, funcs or {})
    return vm


class TestVMConstants:
    def test_constant_int(self):
        vm = make_vm([OpCode.OP_CONSTANT, 0, OpCode.OP_HALT], [42])
        vm.run()
        assert vm.stack == [42]

    def test_constant_string(self):
        vm = make_vm([OpCode.OP_CONSTANT, 0, OpCode.OP_HALT], ["hola"])
        vm.run()
        assert vm.stack == ["hola"]

    def test_constant_bool_true(self):
        vm = make_vm([OpCode.OP_CONSTANT, 0, OpCode.OP_HALT], [True])
        vm.run()
        assert vm.stack == [True]

    def test_constant_bool_false(self):
        vm = make_vm([OpCode.OP_CONSTANT, 0, OpCode.OP_HALT], [False])
        vm.run()
        assert vm.stack == [False]

    def test_multiple_constants(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_HALT,
        ], [10, 20])
        vm.run()
        assert vm.stack == [10, 20]


class TestVMVariables:
    def test_store_and_load_global(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,   # push 42
            OpCode.OP_STORE_GLOBAL, 0, # store in global[0]
            OpCode.OP_LOAD_GLOBAL, 0,  # load from global[0]
            OpCode.OP_HALT,
        ], [42])
        vm.run()
        assert vm.stack == [42]

    def test_store_and_load_local(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_STORE, 0,
            OpCode.OP_LOAD, 0,
            OpCode.OP_HALT,
        ], [42])
        vm.run()
        assert vm.stack == [42]


class TestVMArithmetic:
    def test_add(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_ADD,
            OpCode.OP_HALT,
        ], [3, 4])
        vm.run()
        assert vm.stack == [7]

    def test_sub(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_SUB,
            OpCode.OP_HALT,
        ], [10, 3])
        vm.run()
        assert vm.stack == [7]

    def test_mul(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_MUL,
            OpCode.OP_HALT,
        ], [3, 4])
        vm.run()
        assert vm.stack == [12]

    def test_div(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_DIV,
            OpCode.OP_HALT,
        ], [10, 2])
        vm.run()
        assert vm.stack == [5.0]

    def test_div_by_zero(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_DIV,
            OpCode.OP_HALT,
        ], [1, 0])
        with pytest.raises(RuntimeError, match="Division por cero"):
            vm.run()

    def test_mod(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_MOD,
            OpCode.OP_HALT,
        ], [10, 3])
        vm.run()
        assert vm.stack == [1]

    def test_string_concat(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_ADD,
            OpCode.OP_HALT,
        ], ["hola ", "mundo"])
        vm.run()
        assert vm.stack == ["hola mundo"]


class TestVMComparison:
    def test_eq_true(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 0,
            OpCode.OP_EQ, OpCode.OP_HALT,
        ], [5])
        vm.run()
        assert vm.stack == [True]

    def test_eq_false(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1,
            OpCode.OP_EQ, OpCode.OP_HALT,
        ], [5, 3])
        vm.run()
        assert vm.stack == [False]

    def test_ne(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1,
            OpCode.OP_NE, OpCode.OP_HALT,
        ], [5, 3])
        vm.run()
        assert vm.stack == [True]

    def test_gt(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1,
            OpCode.OP_GT, OpCode.OP_HALT,
        ], [5, 3])
        vm.run()
        assert vm.stack == [True]

    def test_lt(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1,
            OpCode.OP_LT, OpCode.OP_HALT,
        ], [3, 5])
        vm.run()
        assert vm.stack == [True]

    def test_gte_true(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 0,
            OpCode.OP_GTE, OpCode.OP_HALT,
        ], [5])
        vm.run()
        assert vm.stack == [True]

    def test_lte_true(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 0,
            OpCode.OP_LTE, OpCode.OP_HALT,
        ], [5])
        vm.run()
        assert vm.stack == [True]


class TestVMLogical:
    def test_and_true(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 0,
            OpCode.OP_AND, OpCode.OP_HALT,
        ], [True, True])
        vm.run()
        assert vm.stack == [True]

    def test_and_false(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1,
            OpCode.OP_AND, OpCode.OP_HALT,
        ], [True, False])
        vm.run()
        assert vm.stack == [False]

    def test_or_true(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1,
            OpCode.OP_OR, OpCode.OP_HALT,
        ], [False, True])
        vm.run()
        assert vm.stack == [True]

    def test_or_false(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 0,
            OpCode.OP_OR, OpCode.OP_HALT,
        ], [False, False])
        vm.run()
        assert vm.stack == [False]


class TestVMControlFlow:
    def test_jump(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,   # 0-1: push 1
            OpCode.OP_JUMP, 6,       # 2-3: jump to HALT at index 6
            OpCode.OP_CONSTANT, 1,   # 4-5: push 99 (skipped)
            OpCode.OP_HALT,          # 6: halt
        ], [1, 99])
        vm.run()
        assert vm.stack == [1]

    def test_jump_if_false_taken(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,   # 0-1: push False
            OpCode.OP_JUMP_IF_FALSE, 6,  # 2-3: jump to HALT at index 6
            OpCode.OP_CONSTANT, 1,   # 4-5: push 99 (skipped)
            OpCode.OP_HALT,          # 6: halt
        ], [False, 99])
        vm.run()
        assert vm.stack == []

    def test_jump_if_false_not_taken(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,   # push True
            OpCode.OP_JUMP_IF_FALSE, 5,  # not taken
            OpCode.OP_CONSTANT, 1,   # push 99
            OpCode.OP_HALT,
        ], [True, 99])
        vm.run()
        assert vm.stack == [99]


class TestVMPrint:
    def test_print(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_PRINT,
            OpCode.OP_HALT,
        ], ["hola"])
        vm.run()
        assert vm.output_buffer == ["hola"]

    def test_print_multiple(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_PRINT,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_PRINT,
            OpCode.OP_HALT,
        ], ["a", "b"])
        vm.run()
        assert vm.output_buffer == ["a", "b"]


class TestVMList:
    def test_create_empty_list(self):
        vm = make_vm([
            OpCode.OP_LIST, 0,
            OpCode.OP_HALT,
        ])
        vm.run()
        assert vm.stack == [[]]

    def test_create_list(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_LIST, 2,
            OpCode.OP_HALT,
        ], [1, 2])
        vm.run()
        assert vm.stack == [[1, 2]]

    def test_get_index(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,  # [10, 20]
            OpCode.OP_CONSTANT, 1,  # 0
            OpCode.OP_GET_INDEX,
            OpCode.OP_HALT,
        ], [[10, 20], 0])
        vm.run()
        assert vm.stack == [10]

    def test_set_index(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,  # [10, 20]
            OpCode.OP_CONSTANT, 1,  # 0
            OpCode.OP_CONSTANT, 2,  # 99
            OpCode.OP_SET_INDEX,
            OpCode.OP_HALT,
        ], [[10, 20], 0, 99])
        vm.run()

    def test_length(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_LENGTH,
            OpCode.OP_HALT,
        ], [[1, 2, 3]])
        vm.run()
        assert vm.stack == [3]

    def test_append(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,  # list
            OpCode.OP_CONSTANT, 1,  # value
            OpCode.OP_APPEND,
            OpCode.OP_HALT,
        ], [[1], 2])
        vm.run()
        assert vm.stack == [[1, 2]]

    def test_length_on_string(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_LENGTH,
            OpCode.OP_HALT,
        ], ["hola"])
        vm.run()
        assert vm.stack == [4]


class TestVMDict:
    def test_create_empty_dict(self):
        vm = make_vm([
            OpCode.OP_DICT, 0,
            OpCode.OP_HALT,
        ])
        vm.run()
        assert vm.stack == [{}]

    def test_create_dict(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 1,  # "a"
            OpCode.OP_CONSTANT, 0,  # 1
            OpCode.OP_DICT, 1,
            OpCode.OP_HALT,
        ], [1, "a"])
        vm.run()
        assert vm.stack == [{"a": 1}]


class TestVMBuiltins:
    def test_type_int(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_TYPE,
            OpCode.OP_HALT,
        ], [42])
        vm.run()
        assert vm.stack == ["numero"]

    def test_type_string(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_TYPE,
            OpCode.OP_HALT,
        ], ["hola"])
        vm.run()
        assert vm.stack == ["texto"]

    def test_type_bool(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_TYPE,
            OpCode.OP_HALT,
        ], [True])
        vm.run()
        assert vm.stack == ["booleano"]

    def test_type_null(self):
        vm = make_vm([
            OpCode.OP_NULL,
            OpCode.OP_TYPE,
            OpCode.OP_HALT,
        ], [])
        vm.run()
        assert vm.stack == ["nulo"]

    def test_type_list(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_TYPE,
            OpCode.OP_HALT,
        ], [[1, 2]])
        vm.run()
        assert vm.stack == ["lista"]

    def test_type_dict(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_TYPE,
            OpCode.OP_HALT,
        ], [{"a": 1}])
        vm.run()
        assert vm.stack == ["diccionario"]

    def test_lower(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_LOWER,
            OpCode.OP_HALT,
        ], ["HOLA"])
        vm.run()
        assert vm.stack == ["hola"]

    def test_upper(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_UPPER,
            OpCode.OP_HALT,
        ], ["hola"])
        vm.run()
        assert vm.stack == ["HOLA"]

    def test_abs(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_ABS,
            OpCode.OP_HALT,
        ], [-5])
        vm.run()
        assert vm.stack == [5]

    def test_round(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_ROUND,
            OpCode.OP_HALT,
        ], [3.7])
        vm.run()
        assert vm.stack == [4]

    def test_pow(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_POW,
            OpCode.OP_HALT,
        ], [2, 3])
        vm.run()
        assert vm.stack == [8]

    def test_sqrt(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_SQRT,
            OpCode.OP_HALT,
        ], [9])
        vm.run()
        assert vm.stack == [3.0]

    def test_replace(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_CONSTANT, 2,
            OpCode.OP_REPLACE,
            OpCode.OP_HALT,
        ], ["hola mundo", "mundo", "alvz"])
        vm.run()
        assert vm.stack == ["hola alvz"]

    def test_json_encode(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_JSON_ENCODE,
            OpCode.OP_HALT,
        ], [{"a": 1}])
        vm.run()
        import json
        assert vm.stack == [json.dumps({"a": 1})]

    def test_json_decode(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_JSON_DECODE,
            OpCode.OP_HALT,
        ], ['{"a": 1}'])
        vm.run()
        assert vm.stack == [{"a": 1}]

    def test_get_output(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_PRINT,
            OpCode.OP_GET_OUTPUT,
            OpCode.OP_HALT,
        ], ["test"])
        vm.run()
        assert vm.stack == ["test"]

    def test_time(self):
        vm = make_vm([
            OpCode.OP_TIME,
            OpCode.OP_HALT,
        ])
        import time
        before = time.time()
        vm.run()
        after = time.time()
        val = vm.stack[0]
        assert isinstance(val, float)
        assert before <= val <= after

    def test_error_msg_no_error(self):
        vm = make_vm([
            OpCode.OP_ERROR_MSG,
            OpCode.OP_HALT,
        ])
        vm.run()
        assert vm.stack == [""]


class TestVMFunctionCalls:
    def test_function_call_and_return(self):
        # bytecode layout:
        # 0: CONSTANT 0      -> push 42
        # 2: CALL 7 1 0      -> call func at addr 7 with 1 arg
        # 6: HALT
        # 7: LOAD 0          -> function body: load arg 0
        # 9: RETURN
        vm = make_vm(
            bc=[
                OpCode.OP_CONSTANT, 0,
                OpCode.OP_CALL, 7, 1, 0,
                OpCode.OP_HALT,
                OpCode.OP_LOAD, 0,
                OpCode.OP_RETURN,
            ],
            consts=[42],
            funcs={"foo": (7, 1, ["x"])},
        )
        vm.run()
        assert vm.stack == [42]

    def test_function_no_args(self):
        # bytecode layout:
        # 0: CALL 5 0 0      -> call func at addr 5 with 0 args
        # 4: HALT
        # 5: CONSTANT 0      -> function body: push 99
        # 7: RETURN
        vm = make_vm(
            bc=[
                OpCode.OP_CALL, 5, 0, 0,
                OpCode.OP_HALT,
                OpCode.OP_CONSTANT, 0,
                OpCode.OP_RETURN,
            ],
            consts=[99],
            funcs={"foo": (5, 0, [])},
        )
        vm.run()
        assert vm.stack == [99]


class TestVMClass:
    def test_class_new_no_constructor(self):
        class_data = {'props': {'x': 1}, 'methods': {}, 'parent': None}
        vm = make_vm(
            bc=[
                OpCode.OP_CLASS, 0, 1,  # define class
                OpCode.OP_CONSTANT, 0,  # class name
                OpCode.OP_NEW, 0,  # 0 args
                OpCode.OP_HALT,
            ],
            consts=["MiClase", class_data],
        )
        vm.run()
        instance = vm.stack[0]
        assert isinstance(instance, dict)
        assert instance.get('x') == 1
        assert instance.get('_clase') == "MiClase"


class TestVMExceptionHandling:
    def test_no_exception(self):
        vm = make_vm([
            OpCode.OP_TRY_PUSH, 5,  # handler at 5
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_TRY_POP,
            OpCode.OP_HALT,
            # handler (unused)
            OpCode.OP_HALT,
        ], [42])
        vm.run()
        assert vm.stack == [42]

    def test_exception_caught(self):
        # bytecode layout:
        # 0: TRY_PUSH 7      -> handler at index 7
        # 2: CONSTANT 0      -> push 1
        # 4: CONSTANT 1      -> push 0
        # 6: DIV             -> division by zero -> exception
        # 7: TRY_POP
        # 8: JUMP 11         -> skip handler (goto halt)
        # 10: (jump arg)
        # 11: HALT
        # handler at index 7 redirects here -> no, TRY_PUSH sets handler=7
        # but index 7 is TRY_POP... need to restructure:
        vm = make_vm(
            [
                OpCode.OP_TRY_PUSH, 10,  # 0-1: handler at index 10
                OpCode.OP_CONSTANT, 0,   # 2-3: push 1
                OpCode.OP_CONSTANT, 1,   # 4-5: push 0
                OpCode.OP_DIV,           # 6: division by zero -> exception
                OpCode.OP_TRY_POP,       # 7
                OpCode.OP_JUMP, 12,      # 8-9: skip handler
                OpCode.OP_CONSTANT, 2,   # 10-11: handler: push -1
                OpCode.OP_HALT,          # 12
            ],
            [1, 0, -1],
        )
        vm.run()
        assert vm.stack == [-1]


class TestVMHalt:
    def test_halt_stops_execution(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_HALT,
            OpCode.OP_CONSTANT, 1,
            OpCode.OP_HALT,
        ], [1, 2])
        vm.run()
        assert vm.stack == [1]

    def test_empty_bytecode(self):
        vm = make_vm([])
        vm.run()
        assert vm.stack == []


class TestVMNegate:
    def test_negate_positive(self):
        vm = make_vm([OpCode.OP_CONSTANT, 0, OpCode.OP_NEGATE, OpCode.OP_HALT], [5])
        vm.run()
        assert vm.stack == [-5]

    def test_negate_negative(self):
        vm = make_vm([OpCode.OP_CONSTANT, 0, OpCode.OP_NEGATE, OpCode.OP_HALT], [-3])
        vm.run()
        assert vm.stack == [3]

    def test_negate_twice(self):
        vm = make_vm([
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_NEGATE,
            OpCode.OP_NEGATE,
            OpCode.OP_HALT,
        ], [5])
        vm.run()
        assert vm.stack == [5]


class TestVMMakeFunc:
    def test_make_func_creates_descriptor(self):
        vm = make_vm(
            [OpCode.OP_MAKE_FUNC, 5, 2, OpCode.OP_HALT],
            [],
        )
        vm.run()
        assert len(vm.stack) == 1
        assert vm.stack[0] == ('FUNC', 5, 2)

    def test_call_through_func_descriptor(self):
        make_vm = VM  # Use raw VM contructor to avoid alias shadowing
        bc = [
            OpCode.OP_MAKE_FUNC, 12, 2,   # 0: create func desc for addr 12, 2 params
            OpCode.OP_CONSTANT, 0,         # 3: push 3
            OpCode.OP_CONSTANT, 1,         # 4: push 4
            OpCode.OP_CALL, 0, 2, 0,      # 5: call (desc on stack), 2 args
            OpCode.OP_HALT,                # 9
            # Funcion interna:
            OpCode.OP_LOAD, 0,             # 12: load param 0
            OpCode.OP_LOAD, 1,             # 13: load param 1
            OpCode.OP_ADD,                 # 14: add
            OpCode.OP_RETURN,              # 15: return
        ]
        # 16: ADD                  3+4=7
        # 17: RETURN               return 7
        vm = make_vm(
            [
                OpCode.OP_MAKE_FUNC, 12, 2,
                OpCode.OP_CONSTANT, 0,
                OpCode.OP_CONSTANT, 1,
                OpCode.OP_CALL, 0, 2, 0,
                OpCode.OP_HALT,
                OpCode.OP_LOAD, 0,
                OpCode.OP_LOAD, 1,
                OpCode.OP_ADD,
                OpCode.OP_RETURN,
            ],
            [3, 4],
        )
        vm.run()
        assert vm.stack == [7]


class TestVMImport:
    def test_import_runtime(self):
        with open('_test_vm_import.alvz', 'w', encoding='utf-8') as f:
            f.write('variable x = 42\nimprimir(x)\n')
        try:
            constants = ['_test_vm_import.alvz']
            bytecode = [
                OpCode.OP_CONSTANT, 0,
                OpCode.OP_IMPORT,
                OpCode.OP_HALT,
            ]
            vm = VM(bytecode, constants, {})
            vm.run()
            assert vm.output_buffer == ["42"]
        finally:
            import os
            try:
                os.remove('_test_vm_import.alvz')
            except Exception:
                pass

    def test_import_error_file_not_found(self):
        bytecode = [
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_IMPORT,
            OpCode.OP_HALT,
        ]
        vm = VM(bytecode, ['_test_non_existent.alvz'], {})
        try:
            vm.run()
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "Error al importar" in str(e)


class TestVMTypeErrors:
    def _expect_type_error(self, bc, consts, expected_msg):
        vm = VM(bc, consts, {})
        try:
            vm.run()
            assert False, "Should have raised TypeError"
        except RuntimeError as e:
            assert "Error de tipo" in str(e), f"Expected type error, got: {e}"
            assert expected_msg in str(e), f"Expected '{expected_msg}' in '{e}'"

    def test_sub_string(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1, OpCode.OP_SUB, OpCode.OP_HALT],
            ["hola", "mundo"],
            "resta"
        )

    def test_mul_string(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1, OpCode.OP_MUL, OpCode.OP_HALT],
            ["hola", 3],
            "multiplicacion"
        )

    def test_div_bool(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1, OpCode.OP_DIV, OpCode.OP_HALT],
            [10, "dos"],
            "division"
        )

    def test_mod_list(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1, OpCode.OP_MOD, OpCode.OP_HALT],
            [[1, 2], 2],
            "modulo"
        )

    def test_negate_string(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_NEGATE, OpCode.OP_HALT],
            ["hola"],
            "negacion"
        )

    def test_gt_cross_type(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1, OpCode.OP_GT, OpCode.OP_HALT],
            [5, "tres"],
            "comparacion mayor"
        )

    def test_lower_number(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_LOWER, OpCode.OP_HALT],
            [42],
            "minusculas"
        )

    def test_upper_list(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_UPPER, OpCode.OP_HALT],
            [[1, 2]],
            "mayusculas"
        )

    def test_replace_number(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1, OpCode.OP_CONSTANT, 2, OpCode.OP_REPLACE, OpCode.OP_HALT],
            [42, "a", "b"],
            "reemplazar"
        )

    def test_abs_string(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_ABS, OpCode.OP_HALT],
            ["hola"],
            "absoluto"
        )

    def test_pow_string(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1, OpCode.OP_POW, OpCode.OP_HALT],
            [2, "tres"],
            "potencia"
        )

    def test_round_string(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_ROUND, OpCode.OP_HALT],
            ["hola"],
            "redondear"
        )

    def test_sqrt_string(self):
        self._expect_type_error(
            [OpCode.OP_CONSTANT, 0, OpCode.OP_SQRT, OpCode.OP_HALT],
            ["hola"],
            "raiz"
        )

    def test_get_index_on_string(self):
        bc = [OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1, OpCode.OP_GET_INDEX, OpCode.OP_HALT]
        vm = VM(bc, ["hola", 0], {})
        vm.run()
        assert vm.stack == ["h"]

    def test_get_index_on_string_out_of_range(self):
        bc = [OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1, OpCode.OP_GET_INDEX, OpCode.OP_HALT]
        vm = VM(bc, ["hola", 10], {})
        try:
            vm.run()
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "fuera de rango" in str(e)

    def test_set_index_on_string(self):
        bc = [OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1, OpCode.OP_CONSTANT, 2, OpCode.OP_SET_INDEX, OpCode.OP_HALT]
        vm = VM(bc, ["hola", 0, "x"], {})
        try:
            vm.run()
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "lista" in str(e)

    def test_append_on_number(self):
        bc = [OpCode.OP_CONSTANT, 0, OpCode.OP_CONSTANT, 1, OpCode.OP_APPEND, OpCode.OP_HALT]
        vm = VM(bc, [42, 1], {})
        try:
            vm.run()
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "agregar" in str(e)

    def test_length_on_number(self):
        bc = [OpCode.OP_CONSTANT, 0, OpCode.OP_LENGTH, OpCode.OP_HALT]
        vm = VM(bc, [42], {})
        try:
            vm.run()
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "longitud" in str(e)
