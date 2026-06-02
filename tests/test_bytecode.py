"""Tests para el sistema de opcodes del bytecode Alvz."""

from alvz.core.bytecode import OpCode


def test_opcode_enum_values():
    """Verifica que los opcodes principales tengan los valores correctos."""
    assert OpCode.OP_CONSTANT == 1
    assert OpCode.OP_STORE == 2
    assert OpCode.OP_LOAD == 3
    assert OpCode.OP_PRINT == 6
    assert OpCode.OP_CALL == 24
    assert OpCode.OP_RETURN == 25
    assert OpCode.OP_HALT == 27
    assert OpCode.OP_CLASS == 47
    assert OpCode.OP_NEW == 48
    assert OpCode.OP_NULL == 75
    assert OpCode.OP_DEBUG_BREAK == 83


def test_opcode_round_trip():
    assert OpCode(1) == OpCode.OP_CONSTANT
    assert OpCode(83) == OpCode.OP_DEBUG_BREAK


def test_opcode_count():
    """Hay 83 opcodes, del 1 al 83 (omitiendo el 0)."""
    values = [m.value for m in OpCode]
    assert min(values) == 1
    assert max(values) == 83
    assert len(values) == 83


def test_all_opcodes_unique():
    """No debe haber opcodes duplicados."""
    values = [m.value for m in OpCode]
    assert len(values) == len(set(values))
