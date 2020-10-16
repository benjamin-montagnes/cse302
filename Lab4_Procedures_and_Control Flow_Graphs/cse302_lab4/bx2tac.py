#!/usr/bin/env python3

import ast
import tac
from tac import Instr, execute

binop_code = {
    '+': 'add',
    '-': 'sub',
    '*': 'mul',
    '/': 'div',
    '%': 'mod',
    '&': 'and',
    '|': 'or',
    '^': 'xor',
    '<<': 'shl',
    '>>': 'shr',
}
unop_code = {
    'u-': 'neg',
    '~': 'not',
}
relop_code = {
    '==': (lambda l, r: ('jz', l, r)),
    '!=': (lambda l, r: ('jnz', l, r)),
    '<':  (lambda l, r: ('jl', l, r)),
    '<=': (lambda l, r: ('jle', l, r)),
    '>':  (lambda l, r: ('jl', r, l)),
    '>=': (lambda l, r: ('jle', r, l)),
}

class Munch:
    def __init__(self, prog):
        self._varmap = dict()
        self._count = -1
        self._instrs = []
        self._saved_prog = prog
        self.munch_prog(prog)

    def ship(self):
        return self._instrs

    def _emit(self, instr):
        self._instrs.append(instr)

    def _fresh_temp(self):
        """Allocate and return a fresh temporary"""
        self._count += 1
        return '%' + str(self._count)

    def _fresh_label(self):
        """Allocate and return a fresh label"""
        self._count += 1
        return '.L' + str(self._count)

    def _lookup(self, var):
        """Lookup the temporary mapped to `var', allocating if necessary"""
        if var not in self._varmap:
            self._varmap[var] = self._fresh_temp()
        return self._varmap[var]

    def munch_prog(self, prog):
        self._loop_exits = []
        self.lab_enter = self._fresh_label()
        self.lab_return = self._fresh_label()
        self._emit(Instr(None, 'label', self.lab_enter, None))
        self.munch_block(prog)
        self._emit(Instr(None, 'label', self.lab_return, None))

    def munch_block(self, stmts):
        for stmt in stmts:
            self.munch_stmt(stmt)

    def munch_stmt(self, stmt):
        if isinstance(stmt, ast.Assign):
            t_rhs = self.bmm_int_expr(stmt.value)
            self._emit(Instr(self._lookup(stmt.var.name), 'copy', t_rhs, None))
        elif isinstance(stmt, ast.Print):
            t_arg = self.bmm_int_expr(stmt.arg)
            self._emit(Instr(None, 'print', t_arg, None))
        elif isinstance(stmt, ast.Block):
            self.munch_block(stmt.body)
        elif isinstance(stmt, ast.IfElse):
            lab_true = self._fresh_label()
            lab_false = self._fresh_label()
            lab_end = self._fresh_label()
            self.munch_bool_expr(stmt.cond, lab_true, lab_false)
            self._emit(Instr(None, 'label', lab_false, None))
            self.munch_stmt(stmt.els)
            self._emit(Instr(None, 'jmp', lab_end, None))
            self._emit(Instr(None, 'label', lab_true, None))
            self.munch_stmt(stmt.thn)
            self._emit(Instr(None, 'label', lab_end, None))
        elif isinstance(stmt, ast.Break):
            if len(self._loop_exits) == 0:
                raise RuntimeError(f'Cannot break here; not in a loop')
            self._emit(Instr(None, 'jmp', self._loop_exits[-1][0], None))
        elif isinstance(stmt, ast.Continue):
            if len(self._loop_exits) == 0:
                raise RuntimeError(f'Cannot continue here; not in a loop')
            self._emit(Instr(None, 'jmp', self._loop_exits[-1][1], None))
        elif isinstance(stmt, ast.While):
            lab_header = self._fresh_label()
            lab_body = self._fresh_label()
            lab_end = self._fresh_label()
            self._emit(Instr(None, 'label', lab_header, None))
            self.munch_bool_expr(stmt.cond, lab_body, lab_end)
            self._emit(Instr(None, 'label', lab_body, None))
            self._loop_exits.append((lab_end, lab_header))
            self.munch_stmt(stmt.body)
            self._loop_exits.pop()
            self._emit(Instr(None, 'jmp', lab_header, None))
            self._emit(Instr(None, 'label', lab_end, None))
        else:
            raise RuntimeError(f'munch_stmt() cannot handle: {stmt.__class__}')

    def munch_bool_expr(self, expr, ltrue, lfalse):
        if expr.ty is not ast.BOOL:
            raise RuntimeError(f'munch_bool_expr(): expecting {ast.BOOL}, got {expr.ty}')
        if isinstance(expr, ast.Boolean):
            self._emit(Instr(None, 'jmp', ltrue if expr.value else lfalse, None))
        elif isinstance(expr, ast.Appl):
            if expr.func in relop_code:
                (opcode, left, right) = relop_code[expr.func](expr.args[0], expr.args[1])
                t_left = self.bmm_int_expr(left)
                t_right = self.bmm_int_expr(right)
                t_result = self._fresh_temp()
                self._emit(Instr(t_result, 'sub', t_left, t_right))
                self._emit(Instr(None, opcode, t_result, ltrue))
                self._emit(Instr(None, 'jmp', lfalse, None))
            elif expr.func == '!':
                self.munch_bool_expr(expr.args[0], lfalse, ltrue)
            elif expr.func == '&&':
                li = self._fresh_label()
                self.munch_bool_expr(expr.args[0], li, lfalse)
                self._emit(Instr(None, 'label', li, None))
                self.munch_bool_expr(expr.args[1], ltrue, lfalse)
            elif expr.func == '||':
                li = self._fresh_label()
                self.munch_bool_expr(expr.args[0], ltrue, li)
                self._emit(Instr(None, 'label', li, None))
                self.munch_bool_expr(expr.args[1], ltrue, lfalse)
            else:
                raise RuntimeError(f'munch_bool_expr(): unknown operator {expr.func}')
        else:
            raise RuntimeError(f'munch_bool_expr(): unknown boolean expression {expr.__class__}')

    def bmm_int_expr(self, expr):
        if expr.ty is not ast.INT:
            raise RuntimeError(f'bmm_int_expr(): expecting {ast.INT}, got {expr.ty}')
        if isinstance(expr, ast.Variable):
            return self._lookup(expr.name)
        if isinstance(expr, ast.Number):
            t_result = self._fresh_temp()
            self._emit(Instr(t_result, 'const', expr.value, None))
            return t_result
        if isinstance(expr, ast.Appl):
            if expr.func in binop_code:
                t_left = self.bmm_int_expr(expr.args[0])
                t_right = self.bmm_int_expr(expr.args[1])
                t_result = self._fresh_temp()
                self._emit(Instr(t_result, binop_code[expr.func], t_left, t_right))
                return t_result
            elif expr.func in unop_code:
                t_left = self.bmm_int_expr(expr.args[0])
                t_result = self._fresh_temp()
                self._emit(Instr(t_result, unop_code[expr.func], t_left, None))
                return t_result
            else:
                raise RuntimeError(f'bmm_int_expr(): unknown operator {expr.func}')
        raise RuntimeError(f'Unknown expr kind: {expr.__class__}')

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys, getopt, time, random, bx1
    opts, bx_files = getopt.getopt(sys.argv[1:], 'hvi', [])
    verbosity = 0
    interpret = False
    for opt, val in opts:
        if opt == '-h':
            print(f'''\
USAGE: {sys.argv[0]} OPTIONS file.bx ...

Where OPTIONS is one of

  -v          Increase verbosity (can be used multiple times)
  -i          Run the TAC interpreter instead of writing TAC files
  -h          Print this help message''')
            exit(0)
        elif opt == '-v':
            verbosity += 1
        elif opt == '-i':
            interpret = True
        else:
            print(f'Unknown option {opt}')
            exit(1)
    for bx_file in bx_files:
        if not bx_file.endswith('.bx'):
            print(f'File name {bx_file} does not end in ".bx"')
            exit(1)
        bx1.lexer.load_source(bx_file)
        bx1_prog = ast.Block(*bx1.parser.parse(lexer=bx1.lexer))
        bx1_prog.type_check([])
        mx = Munch([bx1_prog])
        tac_prog = mx.ship()
        if interpret:
            execute(tac_prog, show_instr=(verbosity>0), only_decimal=(verbosity<=1))
        else:
            tac_file = bx_file[:-3] + '.tac'
            with open(tac_file, 'w') as f:
                for instr in tac_prog:
                    print(instr, file=f)
            if verbosity > 0:
                print(f'{bx_file} -> {tac_file} done')
