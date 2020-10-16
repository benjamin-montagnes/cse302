#!/usr/bin/env python3

"""
Instruction selection: from TAC to X64
"""

import tac
from x64 import *
import subprocess

jcc_map = { 'jz': JZ, 'jnz': JNZ, 'jl': JL, 'jle': JLE }
simple_binop = { 'add': ADD, 'sub': SUB, 'mul': IMUL, 'and': AND, 'or': OR,
                 'xor': XOR }
simple_unop = { 'neg': NEG, 'not': NOT }

class Isel:
    """Instruction selection"""

    def __init__(self, tac_prog):
        """Generate instructions for `prog', a list of tac.Instr instructions"""
        self._tac_prog = tac_prog
        self._process()

    def _process(self):
        valid_labels = frozenset(i.arg1 for i in filter(lambda i: i.opcode == 'label', self._tac_prog))

        stack = dict()
        def get(temp):
            if temp not in stack:
                stack[temp] = -8 * (len(stack) + 1)
            return (stack[temp], '%rbp')

        header = [
            MISC('.globl main'),
            MISC('.text'),
            LABEL('main'),
            PUSH('%rbp'),
            MOV('%rsp', '%rbp'),
        ]

        body = []
        for lno, tin in enumerate(self._tac_prog):
            if tin.opcode == 'nop':
                body.append(NOP)
            elif tin.opcode == 'const':
                body.append(MOV(tin.arg1, get(tin.dest)))
            elif tin.opcode == 'copy':
                body.append(MOV(get(tin.arg1), '%r11'))
                body.append(MOV('%r11', get(tin.dest)))
            elif tin.opcode in simple_binop:
                body.append(MOV(get(tin.arg1), '%r11'))
                body.append(simple_binop[tin.opcode](get(tin.arg2), '%r11'))
                body.append(MOV('%r11', get(tin.dest)))
            elif tin.opcode == 'div' or tin.opcode == 'mod':
                body.append(MOV(get(tin.arg1), '%rax'))
                body.append(IDIV(get(tin.arg2)))
                body.append(MOV('%rax' if tin.opcode == 'div' else '%rdx', get(tin.dest)))
            elif tin.opcode == 'shl' or tin.opcode == 'shr':
                body.append(MOV(get(tin.arg2), '%rcx'))
                body.append(MOV(get(tin.arg1), '%r11'))
                body.append((SAL if tin.opcode == 'shl' else SAR)('%rcx', '%r11'))
                body.append(MOV('%r11', get(tin.dest)))
            elif tin.opcode in simple_unop:
                body.append(MOV(get(tin.arg1), '%r11'))
                body.append(simple_unop[tin.opcode]('%r11'))
                body.append(MOV('%r11', get(tin.dest)))
            elif tin.opcode == 'label':
                # if len(body) > 0 and body[-1].opcode == 'JMP' and body[-1].args[0] == tin.arg1:
                #     # previous jump was unnecessary
                #     print(f'killed: {body.pop()}')
                body.append(LABEL(tin.arg1))
            elif tin.opcode == 'jmp':
                body.append(JMP(tin.arg1))
            elif tin.opcode in jcc_map:
                body.append(CMP(0, get(tin.arg1)))
                body.append(jcc_map[tin.opcode](tin.arg2))
            elif tin.opcode == 'print':
                body.append(MOV(get(tin.arg1), '%rdi'))
                body.append(CALL('bx_print_int'))
            else:
                raise RuntimeError(f'Isel: cannot handle TAC opcode {tin.opcode}')

        stack = [
            SUB(8 * (len(stack) + 1), '%rsp')
        ]

        footer = [
            MOV('%rbp', '%rsp'),
            POP('%rbp'),
            XOR('%rax', '%rax'),
            RET
        ]

        self._x64_prog = header + stack + body + footer

    @property
    def result(self):
        return self._x64_prog

# ------------------------------------------------------------------------------

def generate(tac_file, gcc=True):
    assert tac_file.endswith('.tac')
    tac_prog = tac.load_tac(tac_file)
    x64_prog = Isel(tac_prog).result
    x64_file = tac_file[:-3] + 's'
    out_files = []
    with open(x64_file, 'w') as f:
        for xi in x64_prog: print(xi, file=f)
    out_files.append(x64_file)
    if gcc:
        exe_file = tac_file[:-3] + 'exe'
        cmd = ["gcc", "-g", "-o", exe_file, x64_file, "bx_runtime.c"]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise RuntimeError(f'Failed to run: {" ".join(cmd)}')
        out_files.append(exe_file)
    return out_files

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    from argparse import ArgumentParser
    ap = ArgumentParser(description='Compiler from TAC to x64')
    ap.add_argument('files', metavar='FILE', type=str, nargs='*', help='A TAC file')
    ap.add_argument('-v', dest='verbosity', default=0, action='count',
                    help='increase verbosity')
    ap.add_argument('--no-exec', dest='noexec', action='store_true',
                    default=False, help='do not build the executable')
    args = ap.parse_args()
    for tac_file in args.files:
        out_files = generate(tac_file, gcc=(not args.noexec))
        if args.verbosity > 0:
            print(f'{tac_file} -> {", ".join(out_files)} done')
