#!/usr/bin/env python3

"""
BX0 Interpreter

Usage: ./bx0_interpreter.py file1.bx file2.bx ...
"""

from scanner import load_source, lexer
from parser1 import parser

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
        var = {}
        while e.kids:
            if e.kids[0].opcode == 'assign': var[e.kids[0].kids[0]] = evaluate_expression(var, e.kids[0].kids[1])
            else: print(evaluate_expression(var, e.kids[0].value))
            e = e.kids[1]
            
def evaluate_expression(var, e):
    if e.opcode == 'var':
        if e.value not in var.keys(): sys.exit('ERROR: {} NOT DEFINED'.format(e.value))
        return var[e.value]
    if e.opcode == 'num': return e.value
    if e.opcode == 'binop':
        x,y = evaluate_expression(var, e.kids[0]), evaluate_expression(var, e.kids[1])
        symbol = e.value
        if symbol == '+': final = x + y
        elif symbol == '-': final = x - y
        elif symbol == '*': final = x * y
        elif symbol == '/': final = x // y
        elif symbol == '%': final = x % y
        elif symbol == '|': final = x | y
        elif symbol == '^': final = x ^ y
        elif symbol == '<<': final = x << y
        elif symbol == '>>': final = x >> y
        final &= 0xffffffffffffffff
        if (final & (1<<63)) != 0 : final -= (1<<64)
        return final
    if e.opcode == 'unop':
        x = evaluate_expression(var, e.kids[0])
        symbol = e.value
        if symbol == '-': final = -x
        elif symbol == '~': final = ~x
        final &= 0xffffffffffffffff
        if (final & (1<<63)) != 0 : final -= (1<<64)
        return final

if __name__ == '__main__':
    main()