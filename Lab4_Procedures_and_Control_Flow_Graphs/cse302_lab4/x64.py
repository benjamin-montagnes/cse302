#!/usr/bin/env python3

"""
X64 assembly
"""

# ------------------------------------------------------------------------------

class Instr:
    __slots__ = ('opcode', 'args', 'reads', 'writes', 'labels', '_fmt')
    def __init__(self, opcode, *args, reads=None, writes=None, labels=None):
        self.opcode = opcode
        self.args = args
        self.reads = reads or ()
        self.writes = writes or ()
        self.labels = labels or []
        self._fmt = None

    def formatted(self, fmt):
        self._fmt = fmt
        return self

    def __repr__(self):
        args = '' if len(self.args) == 0 else ', '.join(repr(arg) for arg in self.args) + ', '
        return f'Instr({self.opcode!r}, {args}reads={self.reads!r}, writes={self.writes!r}, labels={self.labels!r})'

    def __str__(self):
        if not self._fmt: return repr(self)
        prefix = '' if self.opcode == 'LABEL' else '\t'
        return prefix + self._fmt.format(*self.args).replace('\n', '\n\t')

# ------------------------------------------------------------------------------

all_regs = frozenset(('%rax', '%rbx', '%rcx', '%rdx', '%rsi', '%rsp', '%rbp', '%rdi',
                      '%r8', '%r9', '%r10', '%r11', '%r12', '%r13', '%r14', '%r15'))
callee_saves = frozenset(('%rbx', '%rsp', '%rbp', '%r12', '%r13', '%r14', '%r15'))
caller_saves = all_regs - callee_saves

def __isreg(arg):
    return arg in all_regs

def __isimm8(arg):
    return isinstance(arg, int) and \
           (-0x80 <= arg < 0x80)

def __isimm32(arg):
    return isinstance(arg, int) and \
           (-0x8000_0000 <= arg < 0x8000_0000)

def __isimm64(arg):
    return isinstance(arg, int) and \
           (-0x8000_0000_0000_0000 <= arg < 0x8000_0000_0000_0000)

def __ismem(arg):
    return isinstance(arg, tuple) and \
           isinstance(arg[0], int) and \
           (-0x80000000 <= arg[0] < 0x80000000) and \
           isinstance(arg[1], str) and \
           __isreg(arg[1])

def __islabel(arg):
    return isinstance(arg, str) and \
           (len(arg) > 0) and \
           (arg[0] != '%')

def __arith_binop(oproot, mnemonic):
    def op(arg1, arg2):
        """Represents: MNEMONIC `arg1', `arg2'"""
        if __isimm32(arg1):
            if __isreg(arg2):
                return Instr(oproot + '_IR', arg2, reads=(0,), writes=(0,))\
                       .formatted(f'{mnemonic} ${hex(arg1)}, {{0}}')
            else:
                assert __ismem(arg2)
                return Instr(oproot + '_IM', arg2[1], reads=(0,))\
                       .formatted(f'{mnemonic} ${hex(arg1)}, {hex(arg2[0])}({{0}})')
        elif __ismem(arg1):
            assert __isreg(arg2)
            return Instr(oproot + '_MR', arg1[1], arg2, reads=(0, 1), writes=(1,))\
                   .formatted(f'{mnemonic} {hex(arg1[0])}({{0}}), {{1}}')
        elif __ismem(arg2):
            assert __isreg(arg1)
            return Instr(oproot + '_RM', arg1, arg2[1], reads=(0, 1))\
                   .formatted(f'{mnemonic} {{0}}, {hex(arg2[0])}({{1}})')
        else:
            assert __isreg(arg1) and __isreg(arg2)
            return Instr(oproot + '_RR', arg1, arg2, reads=(0, 1), writes=(1,))\
                   .formatted(f'{mnemonic} {{0}}, {{1}}')
    op.__name__ = oproot
    op.__doc__ = op.__doc__.replace('MNEMONIC', mnemonic)
    globals()[oproot] = op

__arith_binop('ADD', 'addq')
__arith_binop('SUB', 'subq')
__arith_binop('AND', 'andq')
__arith_binop('OR',  'orq' )
__arith_binop('XOR', 'xorq')

def IMUL(arg1, arg2):
    """Represents: imulq `arg1', 'arg2'"""
    if __isimm32(arg1):
        assert __isreg(arg2)
        return Instr('IMUL_IR', arg2, reads=(0,), writes=(0,)) \
               .formatted(f'imulq ${hex(arg1)}, {{0}}')
    elif __ismem(arg1):
        assert __isreg(arg2)
        return Instr('IMUL_MR', arg1[1], arg2, reads=(0, 1), writes=(1,))\
               .formatted(f'imulq {hex(arg1[0])}({{0}}), {{1}}')
    else:
        assert __isreg(arg1) and __isreg(arg2)
        return Instr('IMUL_RR', arg1, arg2, reads=(0, 1), writes=(1))\
               .formatted(f'imulq {{0}}, {{1}}')

def __arith_unop(oproot, mnemonic):
    def op(arg):
        """Represents: MNEMONIC `arg'"""
        if isinstance(arg, str):
            assert __isreg(arg)
            return Instr(oproot + '_R', arg, reads=(0,), writes=(0,))\
                   .formatted(f'{mnemonic} {{0}}')
        else:
            assert __ismem(arg)
            return Instr(oproot + '_M', arg[1], reads=(0,))\
                   .formatted(f'{mnemonic} {hex(arg[0])}({{0}})')
    op.__name__ = oproot
    op.__doc__ = op.__doc__.replace('MNEMONIC', mnemonic)
    globals()[oproot] = op

__arith_unop('NEG', 'negq')
__arith_unop('NOT', 'notq')

def IDIV(arg):
    """Represents: idivq `arg'"""
    if __ismem(arg):
        assert arg[1] != '%rdx' # RDX is obliterated by cqto
        return Instr('IDIV_M', '%rdx', '%rax', arg[1], reads=(1, 2), writes=(0, 1))\
               .formatted(f'cqto\nidivq {hex(arg[0])}({{2}})')
    else:
        assert __isreg(arg)
        assert arg != '%rdx'    # RDX is obliterated by cqto
        return Instr('IDIV_R', '%rdx', '%rax', arg, reads=(1, 2), writes=(0, 1))\
               .formatted(f'cqto\nidivq {{2}}')

def PUSH(arg):
    """Represents: pushq `arg'"""
    if __ismem(arg):
        return Instr('PUSH_M', arg[1], reads=(0,))\
               .formatted(f'pushq {hex(arg[0])}({{0}})')
    elif __isimm32(arg):
        return Instr('PUSH_I').formatted(f'pushq ${hex(arg)}')
    else:
        assert __isreg(arg)
        return Instr('PUSH_R', arg, reads=(0,))\
               .formatted(f'pushq {{0}}')

def POP(arg):
    """Represents: popq `arg'"""
    if __ismem(arg):
        return Instr('POP_M', arg[1], reads=(0,))\
               .formatted(f'popq {hex(arg[0])}({{0}})')
    else:
        assert __isreg(arg)
        return Instr('POP_R', arg, writes=(0,))\
               .formatted(f'popq {{0}}')

def __shift_op(oproot, mnemonic):
    def op(arg1, arg2):
        """Represents: MNEMONIC `arg1', `arg2'"""
        if __isimm8(arg1):
            if __ismem(arg2):
                return Instr(oproot + '_IM', arg2[1], reads=(0,))\
                       .formatted(f'{mnemonic} ${hex(arg1)}, {hex(arg2[0])}({{0}})')
            else:
                assert __isreg(arg2)
                return Instr(oproot + '_IR', arg2, reads=(0,), writes=(0,))\
                       .formatted(f'{mnemonic} ${hex(arg1)}, {{0}}')
        else:
            assert arg1 == '%rcx'
            if __ismem(arg2):
                return Instr(oproot + '_RM', '%rcx', arg2[1], reads=(0, 1))\
                       .formatted(f'{mnemonic} %cl, {hex(arg2[0])}({{1}})')
            else:
                assert __isreg(arg2)
                return Instr(oproot + '_RR', '%rcx', arg2, reads=(0, 1), writes=(1,))\
                       .formatted(f'{mnemonic} %cl, {{1}}')
    op.__name__ = oproot
    op.__doc__ = op.__doc__.replace('MNEMONIC', mnemonic)
    globals()[oproot] = op

__shift_op('SAR', 'sarq')
__shift_op('SAL', 'salq')

def __jump_op(oproot, mnemonic):
    def op(arg):
        """Represents: MNEMONIC `arg'"""
        assert __islabel(arg)
        return Instr(oproot, arg, labels=(arg,)).formatted(f'{mnemonic} {{0}}')
    op.__name__ = oproot
    op.__doc__ = op.__doc__.replace('MNEMONIC', mnemonic)
    globals()[oproot] = op

__jump_op('JMP', 'jmp')
__jump_op('JZ',  'jz')
__jump_op('JNZ', 'jnz')
__jump_op('JL',  'jl')
__jump_op('JLE', 'jle')

def __nullary_op(oproot, mnemonic):
    globals()[oproot] = Instr(oproot).formatted(f'{mnemonic}')

__nullary_op('RET', 'retq')
__nullary_op('NOP', 'nop')

def __compare_op(oproot, mnemonic):
    def op(arg1, arg2):
        """Represents: MNEMONIC `arg1', `arg2'"""
        if __isimm32(arg1):
            if __isreg(arg2):
                return Instr(oproot + '_IR', arg2, reads=(0,))\
                       .formatted(f'{mnemonic} ${hex(arg1)}, {{0}}')
            elif __ismem(arg2):
                return Instr(oproot + '_IM', arg2[1], reads=(0,))\
                       .formatted(f'{mnemonic} ${hex(arg1)}, {hex(arg2[0])}({{0}})')
            else:
                raise ValueError(f'{oproot}: {arg2} must be r64 or m64')
        elif __isreg(arg1):
            if __isreg(arg2):
                return Instr(oproot + '_RR', arg1, arg2, reads=(0, 1))\
                       .formatted(f'{mnemonic} {{0}}, {{1}}')
            elif __ismem(arg2):
                return Instr(oproot + '_RM', arg1, arg2[1], reads=(0,1))\
                       .formatted(f'{mnemonic} {{0}}, {hex(arg2[0])}({{1}})')
            else:
                raise ValueError(f'{oproot}: {arg2} must be r64 or m64')
        elif __ismem(arg1):
            if __isreg(arg2):
                return Instr(oproot + '_MR', arg1[1], arg2, reads=(0, 1))\
                       .formatted(f'{mnemonic} {hex(arg1[0])}({{0}}), {{1}}')
            else:
                raise ValueError(f'{oproot}: {arg2} must be r64')
        else:
            raise ValueError(f'{oproot}: {arg1} must be imm32, r64, or m64')
    op.__name__ = oproot
    op.__doc__ = op.__doc__.replace('MNEMONIC', mnemonic)
    globals()[oproot] = op

__compare_op('TEST', 'testq')
__compare_op('CMP',  'cmpq')

def MOV(arg1, arg2):
    """Represents: movq `arg1', `arg2'"""
    if __isreg(arg1):
        if __isreg(arg2):
            return Instr('MOV_RR', arg1, arg2, reads=(0,), writes=(1,))\
                   .formatted('movq {0}, {1}')
        elif __ismem(arg2):
            return Instr('MOV_RM', arg1, arg2[1], reads=(0,1))\
                   .formatted(f'movq {{0}}, {hex(arg2[0])}({{1}})')
        else:
            raise ValueError(f'MOV: {arg2} must be r64 or m64')
    elif __ismem(arg1):
        if __isreg(arg2):
            return Instr('MOV_MR', arg1[1], arg2, reads=(0,), writes=(1,))\
                   .formatted(f'movq {hex(arg1[0])}({{0}}), {{1}}')
        else:
            raise ValueError(f'MOV: {arg2} must be r64')
    elif __isimm32(arg1):
        if __isreg(arg2):
            return Instr('MOV_IR', arg2, writes=(0,))\
                   .formatted(f'movq ${hex(arg1)}, {{0}}')
        elif __ismem(arg2):
            return Instr('MOV_IM', arg2[1], reads=(0,))\
                   .formatted(f'movq ${hex(arg1)}, {hex(arg2[0])}({{0}})')
        else:
            raise ValueError(f'MOV: {arg2} must be r64 or m64')
    elif __isimm64(arg1):
        if __isreg(arg2):
            return Instr('MOVABS_IR', arg2, writes=(0,))\
                   .formatted(f'movabsq ${hex(arg1)}, {{0}}')
        if __ismem(arg2):
            return Instr('MOVABS_IM', arg2[1], '%r11', reads=(0,), writes=(1,))\
                   .formatted(f'movabsq ${hex(arg1)}, %r11\nmovq %r11, {hex(arg2[0])}({{0}})')
        else:
            raise ValueError(f'MOV: {arg2} must be r/m64')
    else:
        raise ValueError(f'MOV: {arg1} must be r64, m64, imm32, or imm64')

def LABEL(lbl):
    """Represents: `lbl':"""
    return Instr('LABEL', lbl).formatted(f'{lbl}:')

def CALL(func):
    """Represents: call `func'"""
    return Instr('CALL', func, labels=(func,))\
           .formatted(f'callq {func}')

def MISC(info):
    """Represents: metadata"""
    return Instr('MISC').formatted(info)

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import unittest, random

    class _Tests(unittest.TestCase):
        def setUp(self):
            self.regs = list(all_regs)

        def randReg(self):
            return random.choice(self.regs)

        def randImm32(self):
            return random.randrange(-0x8000_0000, 0x8000_0000)

        def randImm64(self):
            return random.randrange(-0x8000_0000_0000_0000, -0x8000_0000) \
                   if random.randint(0, 1) == 0 else \
                   random.randrange(0x8000_0000, 0x8000_0000_0000_0000)

        def assertInstr(self, instr, target):
            # print(str(instr))
            self.assertEqual(str(instr).strip(), target)

        def testArithBinop(self):
            OPS = [(ADD, "addq"), (SUB, "subq"),
                   (AND, "andq"), (OR,  "orq"), (XOR, "xorq")]
            for OP, mnem in OPS:
                r1, r2 = self.randReg(), self.randReg()
                i = self.randImm32()
                self.assertInstr(OP(r1, r2),          f'{mnem} {r1}, {r2}')
                self.assertInstr(OP(i, r1) ,          f'{mnem} ${hex(i)}, {r1}')
                self.assertInstr(OP((i, '%rsp'), r1), f'{mnem} {hex(i)}(%rsp), {r1}')
                self.assertInstr(OP(r1, (i, '%rsp')), f'{mnem} {r1}, {hex(i)}(%rsp)')

        def testMul(self):
                r1, r2 = self.randReg(), self.randReg()
                i = self.randImm32()
                self.assertInstr(IMUL(r1, r2),          f'imulq {r1}, {r2}')
                self.assertInstr(IMUL(i, r1) ,          f'imulq ${hex(i)}, {r1}')
                self.assertInstr(IMUL((i, '%rsp'), r1), f'imulq {hex(i)}(%rsp), {r1}')

        def testArithUnop(self):
            OPS = [(NEG, "negq"), (NOT, "notq")]
            for OP, mnem in OPS:
                r = self.randReg()
                i = self.randImm32()
                self.assertInstr(OP(r),           f'{mnem} {r}')
                self.assertInstr(OP((i, '%rsp')), f'{mnem} {hex(i)}(%rsp)')

        def testDiv(self):
            r1 = self.randReg()
            while r1 == '%rdx': r1 = self.randReg()
            i = self.randImm32()
            self.assertInstr(IDIV((i, '%rsp')), f'cqto\n\tidivq {hex(i)}(%rsp)')
            self.assertInstr(IDIV(r1), f'cqto\n\tidivq {r1}')

        def testPush(self):
            r = self.randReg()
            i = self.randImm32()
            self.assertInstr(PUSH(i),           f'pushq ${hex(i)}')
            self.assertInstr(PUSH((i, '%rsp')), f'pushq {hex(i)}(%rsp)')
            self.assertInstr(PUSH(r),           f'pushq {r}')

        def testPop(self):
            r = self.randReg()
            i = self.randImm32()
            self.assertInstr(POP((i, '%rsp')), f'popq {hex(i)}(%rsp)')
            self.assertInstr(POP(r),           f'popq {r}')

        def testShift(self):
            OPS = [(SAR, 'sarq'), (SAL, 'salq')]
            for OP, mnem in OPS:
                r = self.randReg()
                i32 = self.randImm32()
                i8 = random.randrange(-0x80, 0x80)
                self.assertInstr(OP(i8, r), f'{mnem} ${hex(i8)}, {r}')
                self.assertInstr(OP(i8, (i32, '%rsp')), f'{mnem} ${hex(i8)}, {hex(i32)}(%rsp)')
                self.assertInstr(OP('%rcx', r), f'{mnem} %cl, {r}')
                self.assertInstr(OP('%rcx', (i32, '%rsp')), f'{mnem} %cl, {hex(i32)}(%rsp)')

        def testJump(self):
            OPS = [(JMP, 'jmp'), (JZ, 'jz'), (JNZ, 'jnz'), (JL, 'jl'), (JLE, 'jle')]
            for OP, mnem in OPS:
                lab = 'Ltest'
                self.assertInstr(OP(lab), f'{mnem} {lab}')

        def testNull(self):
            OPS = [(RET, 'retq'), (NOP, 'nop')]
            for OP, mnem in OPS:
                self.assertInstr(OP, f'{mnem}')

        def testCompare(self):
            OPS = [(TEST, 'testq'), (CMP, 'cmpq')]
            for OP, mnem in OPS:
                r1, r2 = self.randReg(), self.randReg()
                i1, i2 = self.randImm32(), self.randImm32()
                self.assertInstr(OP(i1, r1), f'{mnem} ${hex(i1)}, {r1}')
                self.assertInstr(OP(i1, (i2, '%rsp')), f'{mnem} ${hex(i1)}, {hex(i2)}(%rsp)')
                self.assertInstr(OP(r1, r2), f'{mnem} {r1}, {r2}')
                self.assertInstr(OP(r1, (i1, '%rsp')), f'{mnem} {r1}, {hex(i1)}(%rsp)')
                self.assertInstr(OP((i1, '%rsp'), r1), f'{mnem} {hex(i1)}(%rsp), {r1}')

        def testMov(self):
            r1, r2 = self.randReg(), self.randReg()
            i32, i32_2 = self.randImm32(), self.randImm32()
            i64 = self.randImm64()
            self.assertInstr(MOV(r1, r2), f'movq {r1}, {r2}')
            self.assertInstr(MOV(r1, (i32, '%rsp')), f'movq {r1}, {hex(i32)}(%rsp)')
            self.assertInstr(MOV((i32, '%rsp'), r1), f'movq {hex(i32)}(%rsp), {r1}')
            self.assertInstr(MOV(i32, r1), f'movq ${hex(i32)}, {r1}')
            self.assertInstr(MOV(i32, (i32_2, '%rsp')), f'movq ${hex(i32)}, {hex(i32_2)}(%rsp)')
            self.assertInstr(MOV(i64, r1), f'movabsq ${hex(i64)}, {r1}')

        def testCall(self):
            self.assertInstr(CALL('bx_foo'), f'callq bx_foo')

    unittest.main()
