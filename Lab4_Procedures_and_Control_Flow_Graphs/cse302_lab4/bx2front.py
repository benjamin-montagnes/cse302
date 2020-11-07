#!/usr/bin/env python3

"""
Main binary for BX2
"""

import sys
from bx2_parser import load_source, lexer, parser
#from ast import context

if __name__ == '__main__':
    if len(sys.argv[1:])>1: raise RuntimeError('Only one document')
    assert sys.argv[1:][0].endswith('.bx')
    load_source(sys.argv[1])
    prog = parser.parse(lexer=lexer)
    print(f'Type checking {sys.argv[1]}')
    prog.type_check_global()
    # context._str_(context.first_scope)
    # print(prog)
    prog.type_check()
    print('SUCCESS')
