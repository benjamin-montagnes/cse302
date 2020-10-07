#!/usr/bin/env python3

import bx1_parser
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
    '-': 'neg',
    '~': 'not',
}

class Context:
    """Context of the compiler"""

    def __init__(self):
        self.instrs = []
        self._varmap = dict()
        self._last_temp = -1

    def emit(self, *new_instrs):
        """Extend the instructions with `new_instrs'"""
        self.instrs.extend(new_instrs)

    def fresh_temp(self):
        """Allocate and return a fresh temporary"""
        self._last_temp += 1
        return '%' + str(self._last_temp)

    def lookup_temp(self, var):
        """Lookup the temporary mapped to `var', allocating if necessary"""
        if var not in self._varmap:
            self._varmap[var] = self.fresh_temp()
        return self._varmap[var]

def tmm_expr(cx, e, tdest):
    """Top-down maximal munch of the expression `e' with the result in `tdest'"""
    if e.opcode == 'num':
        cx.emit(Instr(tdest, 'const', e.value, None))
    elif e.opcode == 'var':
        cx.emit(Instr(tdest, 'copy', cx.lookup_temp(e.value), None))
    elif e.opcode == 'binop':
        tl = cx.fresh_temp()
        tmm_expr(cx, e.kids[0], tl)
        tr = cx.fresh_temp()
        tmm_expr(cx, e.kids[1], tr)
        cx.emit(Instr(tdest, binop_code[e.value], tl, tr))
    elif e.opcode == 'unop':
        t = cx.fresh_temp()
        tmm_expr(cx, e.kids[0], t)
        cx.emit(Instr(tdest, unop_code[e.value], t, None))
    else:
        print(f'Unknown expression opcode: {e.opcode}')
        raise RuntimeError

def tmm_stmt(cx, s):
    """Top-down maximal munch of the statement s"""
    if s.opcode == 'print':
        t = cx.fresh_temp()
        tmm_expr(cx, s.kids[0], t)
        cx.emit(Instr(None, 'print', t, None))
    elif s.opcode == 'assign':
        tmm_expr(cx, s.kids[1], cx.lookup_temp(s.kids[0].value))
    else:
        print(f'Unknown stmt opcode: {s.opcode}')
        raise RuntimeError

def bmm_expr(cx, e):
    """Bottom-up maximal munch of the expression `e'; returns the temporary where
    the result would end up."""
    if e.opcode == 'num':
        t = cx.fresh_temp()
        cx.emit(Instr(t, 'const', e.value, None))
        return t
    if e.opcode == 'var':
        return cx.lookup_temp(e.value)
    if e.opcode == 'binop':
        tl = bmm_expr(cx, e.kids[0])
        tr = bmm_expr(cx, e.kids[1])
        t = cx.fresh_temp()
        cx.emit(Instr(t, binop_code[e.value], tl, tr))
        return t
    if e.opcode == 'unop':
        ta = bmm_expr(cx, e.kids[0])
        t = cx.fresh_temp()
        cx.emit(Instr(t, unop_code[e.value], ta, None))
        return t
    print(f'Unknown expression opcode: {e.opcode}')
    raise RuntimeError

def bmm_stmt(cx, s):
    """Bottom-up maximal munch of the statement s"""
    if s.opcode == 'print':
        t = bmm_expr(cx, s.kids[0])
        cx.emit(Instr(None, 'print', t, None))
    elif s.opcode == 'assign':
        t = bmm_expr(cx, s.kids[1])
        cx.emit(Instr(cx.lookup_temp(s.kids[0].value), 'copy', t, None))
    else:
        print(f'Unknown stmt opcode: {s.opcode}')
        raise RuntimeError

import functools

def copy_propagate(cx):
    for i, copy_instr in enumerate(cx.instrs):
        if copy_instr.opcode != 'copy': continue
        t_new = copy_instr.dest
        t_old = copy_instr.arg1
        # in following instructions, replace t_new with t_old
        #   keep doing this while neither has been reset
        for j in range(i + 1, len(cx.instrs)):
            instr = cx.instrs[j]
            if instr.arg1 == t_new: instr.arg1 = t_old
            if instr.arg2 == t_new: instr.arg2 = t_old
            if instr.dest == t_old or instr.dest == t_new: break

def eliminate_dead_copies(cx):
    nop = Instr(None, 'nop', None, None)
    for i, copy_instr in enumerate(cx.instrs):
        if copy_instr.opcode != 'copy': continue
        t_new = copy_instr.dest
        dead = True             # start by assuming it's dead
        # The loop below will determine if it's actually live
        for j in range(i + 1, len(cx.instrs)):
            instr = cx.instrs[j]
            if instr.arg1 == t_new or instr.arg2 == t_new:
                dead = False
                # it's actually live so no need to check further
                break
            if instr.dest == t_new:
                # it got reset, so we can stop looking for reads
                break
        if dead: cx.instrs[i] = nop
    cx.instrs = list(filter(lambda i: i is not nop, cx.instrs))

if __name__ == '__main__':
    import sys, getopt, time
    opts, bx_files = getopt.getopt(sys.argv[1:],
                                   'hvim:',
                                   ['no-prop', 'no-dce'])
    verbosity = 0
    interpret = False
    mm = bmm_stmt
    do_propagate = True
    do_dce = True
    for opt, val in opts:
        if opt == '-h':
            print(f'''\
USAGE: {sys.argv[0]} OPTIONS file.bx ...

Where OPTIONS is one of

  -v          Increase verbosity (can be used multiple times)
  -i          Run the TAC interpreter instead of writing TAC files
  -m <alg>    Use <alg> as the munch algorithm (default: bmm)
  --no-prop   Do not propagate copies
  --no-dce    Do not eliminate dead copies
  -h          Print this help message''')
            exit(0)
        elif opt == '-v':
            verbosity += 1
        elif opt == '-i':
            interpret = True
        elif opt == '-m':
            if val == 'tmm':
                mm = tmm_stmt
            elif val == 'bmm':
                mm = bmm_stmt
            else:
                print(f'Unknown algorithm {val}')
                exit(1)
        elif opt.startswith('--no-prop'):
            do_propagate = False
        elif opt == '--no-dce':
            do_dce = False
        else:
            print(f'Unknown option {opt}')
            exit(1)
    for bx_file in bx_files:
        if not bx_file.endswith('.bx'):
            print(f'File name does not end in ".bx"')
            exit(1)
        cx = Context()
        bx1_parser.lexer.load_source(bx_file)
        bx0_prog = bx1_parser.parser.parse(lexer=bx1_parser.lexer)
        print(bx0_prog)
        for stmt in bx0_prog:
            mm(cx, stmt)
        if do_propagate:
            copy_propagate(cx)
        if do_dce:
            eliminate_dead_copies(cx)
        if interpret:
            execute(cx.instrs, show_instr=(verbosity>0), only_decimal=(verbosity<=1))
        else:
            tac_file = bx_file[:-3] + '.tac'
            with open(tac_file, 'w') as f:
                print(f'// {bx_file}, compiled at {time.strftime("%Y-%m-%d %H:%M:%S")}', file=f)
                for instr in cx.instrs:
                    print(instr, file=f)
            if verbosity > 0:
                print(f'{bx_file} -> {tac_file} done')






