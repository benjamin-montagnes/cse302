#!/usr/bin/env python3

"""
Three Address Code (TAC) intermediate representation
"""

from ply import lex, yacc
from ply_util import *

# ------------------------------------------------------------------------------

opcodes = frozenset((
    'nop',
    'print', 'const', 'copy',
    'add', 'sub', 'mul', 'div', 'mod', 'neg',
    'and', 'or', 'xor', 'not', 'shl', 'shr',
))

class Instr:
    __slots__ = ('dest', 'opcode', 'arg1', 'arg2')
    def __init__(self, dest, opcode, arg1, arg2):
        self.dest = dest
        assert opcode in opcodes
        self.opcode = opcode
        self.arg1 = arg1
        self.arg2 = arg2

    def __repr__(self):
        result = '('
        if self.dest != None: result += f'set {self.dest} ('
        result += self.opcode
        if self.arg1 != None: result += f' {self.arg1}'
        if self.arg2 != None: result += f' {self.arg2}'
        result += ')'
        if self.dest != None: result += ')'
        return result

    def __str__(self):
        result = ''
        if self.dest != None: result += f'{self.dest} = '
        result += f'{self.opcode}'
        if self.arg1 != None:
            result += f' {self.arg1}'
            if self.arg2 != None: result += f', {self.arg2}'
        result += ';'
        return result

# ------------------------------------------------------------------------------

tokens = (
    'TEMP',                     # *local* identifier
    'NUM64',                    # immediate integer
    'OPCODE',                   # instruction opcode
    'EQ', 'COMMA', 'SEMICOLON',
)

def __create_lexer():
    """Create and return a lexer for a TAC"""

    t_ignore = ' \t\f\v\r'

    t_TEMP = r'%(0|[1-9][0-9]*|[A-Za-z][A-Za-z0-9_]*)'
    t_EQ = r'='
    t_COMMA = r','
    t_SEMICOLON = r';'

    def t_newline(t):
        r'\n'
        t.lexer.lineno += 1

    def t_comment(t):
        r'//[^\n]*\n?'
        t.lexer.lineno += 1

    def t_OPCODE(t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        if t.value not in opcodes:
            print_at(t, f'Unknown op: {t.value}')
            raise SyntaxError('opcodes')
        return t

    def t_NUM64(t):
        r'0|-?[1-9][0-9]*'
        t.value = int(t.value)
        if t.value & 0xffffffffffffffff != t.value:
            print_at(t, f'Error: numerical literal {t.value} not in [{-1<<63}, {1<<63})')
            raise SyntaxError('immint')
        return t

    from sys import stderr
    def t_error(t):
        print_at(t, f'Warning: skipping illegal character: {t.value[0]}')
        t.lexer.skip(1)

    return extend_lexer(lex.lex())

# ------------------------------------------------------------------------------

def __create_parser():
    def p_program(p):
        '''program : instr program
                   | '''
        prog = [] if len(p) == 1 else p[2]
        if len(p) != 1: prog.insert(0, p[1])
        p[0] = prog

    def p_instr(p):
        '''instr : lhs OPCODE args SEMICOLON'''
        p[0] = Instr(p[1], p[2], p[3][0], p[3][1])

    def p_lhs(p):
        '''lhs : TEMP EQ
               | '''
        p[0] = None if len(p) == 1 else p[1]

    def p_args(p):
        '''args : arg COMMA arg
                | arg
                | '''
        arg1 = None if len(p) < 2 else p[1]
        arg2 = None if len(p) != 4 else p[3]
        p[0] = (arg1, arg2)

    def p_arg(p):
        '''arg : TEMP
               | NUM64'''
        p[0] = p[1]

    def p_error(p):
        if p:
            p.lexer.lexpos -= len(p.value)
            print_at(p, f'Error: syntax error at token {p.type}')
        raise RuntimeError('parsing')

    return yacc.yacc(start='program')

# ------------------------------------------------------------------------------

word_bytes = 8
word_bits = 8 * word_bytes
sign_mask = 1 << (word_bits - 1)
full_mask = (1 << word_bits) - 1
def untwoc(x):
    """Convert a 64-bit word in two's complement representation
    to a Python int"""
    return x - full_mask - 1 if x & sign_mask else x
def twoc(x):
    """Convert a Python int in range to a 64-bit word in two's
    complement representation"""
    return x & full_mask

binops = {
    'add' : (lambda u, v: twoc(untwoc(u) + untwoc(v))),
    'sub' : (lambda u, v: twoc(untwoc(u) - untwoc(v))),
    'mul' : (lambda u, v: twoc(untwoc(u) * untwoc(v))),
    'div' : (lambda u, v: twoc(untwoc(u) // untwoc(v))),
    'mod' : (lambda u, v: twoc(untwoc(u) % untwoc(v))),
    'and' : (lambda u, v: twoc(untwoc(u) & untwoc(v))),
    'or'  : (lambda u, v: twoc(untwoc(u) | untwoc(v))),
    'xor' : (lambda u, v: twoc(untwoc(u) ^ untwoc(v))),
    'shl' : (lambda u, v: twoc(untwoc(u) << untwoc(v))),
    'shr' : (lambda u, v: twoc(untwoc(u) >> untwoc(v))),
}
unops = {
    'neg' : (lambda u: twoc(-untwoc(u))),
    'not' : (lambda u: twoc(~untwoc(u))),
}

def execute(prog, *, show_instr=False, only_decimal=True):
    values = dict()

    def ensure_valid_temp(x, descr):
        if x == None:
            print(f'Missing {descr}')
            raise RuntimeError
        if isinstance(x, int):
            print(f'Found immediate {x} when expecting temp')
            raise RuntimeError

    def read_temp(x, descr):
        ensure_valid_temp(x, descr)
        if x not in values:
            print(f'Read from uninitialized temp: {x}')
            raise RuntimeError
        return values[x]

    def write_temp(x, v, descr):
        ensure_valid_temp(x, descr)
        values[x] = v

    for instr in prog:
        if show_instr: print(f'// {instr}')
        if instr.opcode == 'nop':
            pass                # nothing to do
        elif instr.opcode == 'const':
            if not isinstance(instr.arg1, int):
                print(f'Missing or bad argument: {instr.arg1}')
                raise RuntimeError
            write_temp(instr.dest, twoc(instr.arg1), 'lhs')
        elif instr.opcode == 'copy':
            write_temp(instr.dest, read_temp(instr.arg1, 'source'), 'dest')
        elif instr.opcode == 'print':
            u = read_temp(instr.arg1, 'arg')
            if only_decimal:
                print(str(untwoc(u)))
            else:
                print(f'{untwoc(u): 20d}  0x{u:016x}  0b{u:064b}')
        elif instr.opcode in binops:
            u = read_temp(instr.arg1, '1st operand')
            v = read_temp(instr.arg2, '2nd operand')
            write_temp(instr.dest, binops[instr.opcode](u, v), 'dest')
        elif instr.opcode in unops:
            u = read_temp(instr.arg1, 'arg')
            if instr.arg2 != None:
                print(f'Unary operator {self.opcode} has two arguments!')
                raise RuntimeError
            write_temp(instr.dest, unops[instr.opcode](u), 'dest')
        else:
            print(f'Unknown opcode {instr.opcode}')
            raise RuntimeError

# --------------------------------------------------------------------------------

lexer  = __create_lexer()
parser = __create_parser()

def load_tac(tac_file):
    """Load the TAC instructions from the given `tac_file'"""
    lexer.load_source(tac_file)
    return parser.parse(lexer=lexer)

if __name__ == '__main__':
    import sys, getopt
    opts, srcfiles = getopt.getopt(sys.argv[1:], 'vh')
    verbosity = 0
    for opt, _ in opts:
        if opt == '-h':
            print(f'''\
{sys.argv[0]} [-v] [-h] file1.tac ...

  -v      Increase verbosity (can be used multiple times)
  -h      Print this help message.''')
            exit(0)
        elif opt == '-v':
            verbosity += 1
        else:
            print(f'Unknown option {opt}', file=sys.stderr)
            exit(1)
    for srcfile in srcfiles:
        prog = load_tac(srcfile)
        execute(prog, show_instr=(verbosity>0), only_decimal=(verbosity<=1))

