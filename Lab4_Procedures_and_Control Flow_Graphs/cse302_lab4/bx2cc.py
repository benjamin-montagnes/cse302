#!/usr/bin/env python3

import bx1, ast, tac, bx1tac, x64, tacx64
from argparse import ArgumentParser
import tempfile, subprocess

bx1_runtime = r"""
#include <stdio.h>
#include <stdint.h>
void bx_print_int(int64_t arg) { printf("%ld\n", arg); }
"""

def main():
    ap = ArgumentParser(description='BX1 to X64 compiler')
    ap.add_argument('bx1', metavar='FILE', type=str, nargs=1, help='a BX1 source file')
    ap.add_argument('--keep-tac', dest='keep_tac', default=False, action='store_true',
                    help='keep the intermediate TAC file')
    ap.add_argument('-g', dest='debug', default=False, action='store_true',
                    help='store debug symbols (i.e., pass the -g flag to gcc)')
    ap.add_argument('-v', dest='verbosity', default=0, action='count',
                    help='increase verbosity')
    args = ap.parse_args()
    bx1_file = args.bx1[0]
    assert bx1_file.endswith('.bx')
    bx1_base = bx1_file[:-3]
    bx1.lexer.load_source(bx1_file)
    bx1_ast = bx1.parser.parse(lexer=bx1.lexer)
    if args.verbosity > 1: print(f'{bx1_file} parsed')
    scopes = [dict()]
    for stmt in bx1_ast:
        stmt.type_check(scopes)
    if args.verbosity > 1: print(f'{bx1_file} type-checked')
    tac_prog = bx1tac.Munch(bx1_ast).ship()
    if args.verbosity > 0: print(f'TAC produced (from {bx1_file})')
    if args.keep_tac:
        tac_file = bx1_base + '.tac'
        with open(tac_file, 'w') as f:
            for i in tac_prog: print(i, file=f)
        if args.verbosity > 1: print(f'{tac_file} written')
    x64_file = bx1_base + '.s'
    x64_prog = tacx64.Isel(tac_prog).result
    if args.verbosity > 0: print(f'x64 produced (from TAC (from {bx1_file}))')
    with open(x64_file, 'w') as f:
        for i in x64_prog: print(i, file=f)
        if args.verbosity > 1: print(f'{x64_file} written')
    exe_file = bx1_base + '.exe'
    with tempfile.TemporaryDirectory() as tmpdirname:
        bxrt_file = tmpdirname + '/bxrt.c'
        with open(bxrt_file, 'w') as f:
            print(bx1_runtime, file=f)
        cmd = ["gcc"] + (["-g"] if args.debug else []) + \
              ["-o", exe_file, x64_file, bxrt_file]
        if args.verbosity > 2:
            print(f'gcc command: {" ".join(cmd)}')
        result = subprocess.run(cmd)
        if result.returncode == 0 and args.verbosity > 1:
            print(f'{exe_file} written')
        return result.returncode

if __name__ == '__main__':
    exit(main())
