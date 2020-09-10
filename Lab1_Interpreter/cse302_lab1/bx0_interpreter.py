#!/usr/bin/env python3

"""
BX0 Interpreter

Usage: ./bx0_interpreter.py file1.bx file2.bx ...
"""

from scanner import load_source, lexer
from parser import parser

import sys

def main():
    """
    The main loop of the interpreter
    """
    for filename in sys.argv[1:]:
        print(f'[[ processing {filename} ]]')
        load_source(filename)
        # Currently this reads an <expr> and then prints it out
        # TODO: Change this to instead read <stmt>s in a loop
        #       executing them one by one
        e = parser.parse(lexer=lexer)
        print(f'>>> {e!r}')

if __name__ == '__main__':
    main()
