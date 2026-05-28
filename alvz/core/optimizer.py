from .bytecode import OpCode

OPCODE_OPERANDS = {
    OpCode.OP_CONSTANT: 1,
    OpCode.OP_STORE: 1,
    OpCode.OP_LOAD: 1,
    OpCode.OP_STORE_GLOBAL: 1,
    OpCode.OP_LOAD_GLOBAL: 1,
    OpCode.OP_JUMP: 1,
    OpCode.OP_JUMP_IF_FALSE: 1,
    OpCode.OP_JUMP_IF_TRUE: 1,
    OpCode.OP_CALL: 3,
    OpCode.OP_ASYNC_CALL: 3,
    OpCode.OP_MAKE_FUNC: 2,
    OpCode.OP_LIST: 1,
    OpCode.OP_DICT: 1,
    OpCode.OP_CLASS: 2,
    OpCode.OP_NEW: 1,
    OpCode.OP_TRY_PUSH: 1,
    OpCode.OP_GET_ATTR: 1,
    OpCode.OP_SET_ATTR: 1,
    OpCode.OP_SLICE: 1,
}

def get_operand_count(op):
    return OPCODE_OPERANDS.get(op, 0)

def iter_instructions(bytecode):
    i = 0
    while i < len(bytecode):
        op = bytecode[i]
        n = get_operand_count(op)
        operands = bytecode[i+1:i+1+n]
        yield i, op, operands
        i += 1 + n

def fold_unary(op, val):
    try:
        if op == OpCode.OP_NEGATE and isinstance(val, (int, float)):
            return -val
        if op == OpCode.OP_LENGTH and isinstance(val, (str, list)):
            return len(val)
        if op == OpCode.OP_TYPE:
            if val is None:
                return "nulo"
            if isinstance(val, bool):
                return "booleano"
            if isinstance(val, (int, float)):
                return "numero"
            if isinstance(val, str):
                return "texto"
            if isinstance(val, list):
                return "lista"
            return "desconocido"
    except Exception:
        return None
    return None

def fold_binary(op, left, right):
    try:
        if op == OpCode.OP_ADD and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left + right
        if op == OpCode.OP_SUB and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left - right
        if op == OpCode.OP_MUL and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left * right
        if op == OpCode.OP_DIV and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left / right
        if op == OpCode.OP_MOD and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left % right
        if op == OpCode.OP_POW and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left ** right
        if op == OpCode.OP_EQ:
            return left == right
        if op == OpCode.OP_NE:
            return left != right
        if op == OpCode.OP_GT and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left > right
        if op == OpCode.OP_LT and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left < right
        if op == OpCode.OP_GTE and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left >= right
        if op == OpCode.OP_LTE and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left <= right
        if op == OpCode.OP_AND:
            return left and right
        if op == OpCode.OP_OR:
            return left or right
    except Exception:
        return None
    return None

class BytecodeOptimizer:
    def __init__(self, bytecode, constants, funcs):
        self.bc = list(bytecode)
        self.consts = list(constants)
        self.funcs = funcs.copy()

    def run(self):
        changed = True
        while changed:
            changed = False
            instrs = list(iter_instructions(self.bc))
            old_instrs = [(op, list(operands)) for _, op, operands in instrs]

            folded = self._fold_constants(instrs)
            if folded:
                new_instrs = list(folded)
                mapping = self._build_old_to_new(old_instrs, new_instrs)
                self._remap_jumps(new_instrs, old_instrs, mapping)
                self.bc = self._patch(new_instrs)
                changed = True

            if not changed:
                removed = self._remove_dead_after_halt(list(old_instrs))
                if len(removed) < len(old_instrs):
                    self.bc = self._patch(removed)
                    changed = True

        return self.bc, self.consts, self.funcs

    def _patch(self, instrs):
        bc = []
        for op, operands in instrs:
            bc.append(op)
            bc.extend(operands)
        return bc

    def _old_addr_of(self, instr_idx, instrs):
        """Compute old bytecode address given instr index and original instr list."""
        addr = 0
        for i in range(instr_idx):
            op, operands = instrs[i]
            addr += 1 + get_operand_count(op)
        return addr

    def _new_addr_of(self, instr_idx, instrs):
        """Compute new bytecode address for instruction at index in new instr list."""
        addr = 0
        for i in range(instr_idx):
            op, operands = instrs[i]
            addr += 1 + get_operand_count(op)
        return addr

    def _build_old_to_new(self, old_instrs, new_instrs):
        """Build mapping from old bytecode offsets to new bytecode offsets."""
        mapping = {}
        for old_idx in range(len(old_instrs) + 1):
            old_addr = self._old_addr_of(old_idx, old_instrs)
            new_addr = self._new_addr_of(min(old_idx, len(new_instrs)), new_instrs)
            mapping[old_addr] = new_addr
        return mapping

    def _remap_jumps(self, instrs, old_instrs, mapping):
        for i, (op, operands) in enumerate(instrs):
            if op in (OpCode.OP_JUMP, OpCode.OP_JUMP_IF_FALSE, OpCode.OP_JUMP_IF_TRUE):
                old_target = operands[0]
                operands[0] = mapping.get(old_target, old_target)
            elif op == OpCode.OP_MAKE_FUNC:
                addr = operands[0]
                operands[0] = mapping.get(addr, addr)
        for name in self.funcs:
            finfo = list(self.funcs[name])
            old_addr = finfo[0]
            finfo[0] = mapping.get(old_addr, old_addr)
            self.funcs[name] = tuple(finfo)

    def _fix_func_addrs(self, mapping):
        for name in self.funcs:
            finfo = list(self.funcs[name])
            old_addr = finfo[0]
            finfo[0] = mapping.get(old_addr, old_addr)
            self.funcs[name] = tuple(finfo)

    def _fold_constants(self, instrs):
        """Fold constant expressions. Returns list of (op, operands) or None if no changes."""
        const_map = {i: v for i, v in enumerate(self.consts)}
        new_instrs = []
        changed = False
        i = 0

        while i < len(instrs):
            idx, op, operands = instrs[i]
            consumed = False

            if op == OpCode.OP_CONSTANT:
                val = const_map.get(operands[0])
                if val is not None and i + 1 < len(instrs):
                    nidx1, nop1, nop1_ops = instrs[i + 1]

                    if nop1 in (OpCode.OP_NEGATE, OpCode.OP_LENGTH, OpCode.OP_TYPE):
                        result = fold_unary(nop1, val)
                        if result is not None:
                            self.consts.append(result)
                            new_instrs.append((OpCode.OP_CONSTANT, [len(self.consts) - 1]))
                            i += 2
                            consumed = True
                            changed = True
                            continue

                    if nop1 == OpCode.OP_CONSTANT and i + 2 < len(instrs):
                        nidx2, nop2, _ = instrs[i + 2]
                        if nop2 in (OpCode.OP_ADD, OpCode.OP_SUB, OpCode.OP_MUL, OpCode.OP_DIV,
                                    OpCode.OP_MOD, OpCode.OP_POW, OpCode.OP_EQ, OpCode.OP_NE,
                                    OpCode.OP_GT, OpCode.OP_LT, OpCode.OP_GTE, OpCode.OP_LTE,
                                    OpCode.OP_AND, OpCode.OP_OR):
                            val2 = const_map.get(nop1_ops[0])
                            if val2 is not None:
                                result = fold_binary(nop2, val, val2)
                                if result is not None:
                                    self.consts.append(result)
                                    new_instrs.append((OpCode.OP_CONSTANT, [len(self.consts) - 1]))
                                    i += 3
                                    consumed = True
                                    changed = True
                                    continue

            if not consumed:
                new_instrs.append((op, list(operands)))
                i += 1

        if changed:
            return new_instrs
        return None

    def _remove_dead_after_halt(self, instrs):
        """Remove instructions after OP_HALT."""
        result = list(instrs)
        for i, (op, _) in enumerate(result):
            if op in (OpCode.OP_HALT,):
                result = result[:i + 1]
                break
        return result

    def _remove_jump_to_next(self, instrs):
        """Remove OP_JUMP that jumps to the immediately next instruction."""
        result = []
        i = 0
        while i < len(instrs):
            op, operands = instrs[i]
            if op == OpCode.OP_JUMP:
                cur_addr = self._new_addr_of(len(result), result)
                target = operands[0]
                next_addr = cur_addr + 1 + get_operand_count(op)
                if target == next_addr:
                    i += 1
                    continue
            result.append((op, list(operands)))
            i += 1
        return result


def optimize(bytecode, constants, funcs):
    if not bytecode:
        return bytecode, constants, funcs
    opt = BytecodeOptimizer(bytecode, constants, funcs)
    return opt.run()
