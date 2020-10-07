#!/usr/bin/env python3

"""
Three Address Code (TAC) intermediate representation
"""

from ply import lex, yacc
from ply_util import *

# ------------------------------------------------------------------------------

opcode_kinds = {
    'nop': 'NNN',
    'jmp': 'NLN',
    'jz': 'NTL', 'jnz': 'NTL', 'jl': 'NTL', 'jle': 'NTL',
    'add': 'TTT', 'sub': 'TTT', 'mul': 'TTT', 'div': 'TTT',
    'mod': 'TTT', 'neg': 'TTN', 'and': 'TTT', 'or': 'TTT',
    'xor': 'TTT', 'not': 'TTN', 'shl': 'TTT', 'shr': 'TTT',
    'print': 'NTN', 'const': 'TIN', 'copy': 'TTN',
    'label': 'NLN',
}
opcodes = frozenset(opcode_kinds.keys())

class Instr:
    __slots__ = ('dest', 'opcode', 'arg1', 'arg2')
    def __init__(self, dest, opcode, arg1, arg2):
        """Create a new TAC instruction with given `opcode' (must be non-None).
        The other three arguments, `dest', 'arg1', and 'arg2' depend on what
        the opcode is.

        Raises ValueError if attempting to create an invalid Instr."""
        self.dest = dest
        self.opcode = opcode
        self.arg1 = arg1
        self.arg2 = arg2
        self._check()

    @classmethod
    def _istemp(cls, thing):
        return isinstance(thing, str) and \
               len(thing) > 0 and \
               thing[0] == '%'

    @classmethod
    def _isint(cls, thing):
        return isinstance(thing, int)

    @classmethod
    def _islabel(cls, thing):
        return isinstance(thing, str) and \
               len(thing) > 1 and \
               thing[0:2] == '.L'

    @classmethod
    def _isvalid(cls, thing, k):
        if k == 'N': return thing == None
        if k == 'I': return cls._isint(thing)
        if k == 'T': return cls._istemp(thing)
        if k == 'L': return cls._islabel(thing)
        return ValueError(f'Unknown argument kind: {k}')

    def _check(self):
        """Perform a well-formedness check on this instruction"""
        if self.opcode not in opcodes:
            raise ValueError(f'bad tac.Instr opcode: {self.opcode}')
        kind = opcode_kinds[self.opcode]
        if not self._isvalid(self.dest, kind[0]):
            raise ValueError(f'bad tac.Instr/{self.opcode} destination: {self.dest}')
        if not self._isvalid(self.arg1, kind[1]):
            raise ValueError(f'bad tac.Instr/{self.opcode} arg1: {self.arg1}')
        if not self._isvalid(self.arg2, kind[2]):
            raise ValueError(f'bad tac.Instr/{self.opcode} arg2: {self.arg2}')

    def __repr__(self):
        result = ''
        if self.dest != None: result += f'(set {self.dest} '
        result += '(' + self.opcode
        if self.arg1 != None: result += f' {self.arg1}'
        if self.arg2 != None: result += f' {self.arg2}'
        result += ')'
        if self.dest != None: result += ')'
        return result

    def __str__(self):
        result = ''
        if self.opcode == 'label':
            result += f'{self.arg1}:'
        else:
            result += '  '
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
    'LABEL',                    # label
    # 'GLABEL',                   # global label
    'EQ', 'COMMA', 'SEMICOLON', 'COLON',
)

def __create_lexer():
    """Create and return a lexer for a TAC"""

    t_ignore = ' \t\f\v\r'

    t_TEMP = r'%(0|[1-9][0-9]*|[A-Za-z][A-Za-z0-9_]*)'
    t_EQ = r'='
    t_COMMA = r','
    t_SEMICOLON = r';'
    t_COLON = r':'

    def t_newline(t):
        r'\n|//[^\n]*\n?'
        t.lexer.lineno += 1

    t_LABEL = r'\.L(?:0|[1-9][0-9]*|[A-Za-z0-9_]+)'

    def t_OPCODE(t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        if t.value not in opcodes:
            t.type = 'GLABEL'
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
        '''program : instrs'''
        p[0] = p[1]

    def p_instrs(p):
        '''instrs : instrs instr
                  | '''
        if len(p) == 1:
            p[0] = []
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_instr(p):
        '''instr : lhs OPCODE args SEMICOLON'''
        lhs = p[1]
        opcode = p[2]
        arg1, arg2 = p[3]
        try:
            p[0] = Instr(lhs, opcode, arg1, arg2)
        except ValueError as exn:
            raise SyntaxError(exn.args[0])

    def p_label(p):
        '''instr : LABEL COLON'''
        p[0] = Instr(None, 'label', p[1], None)

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
               | NUM64
               | LABEL'''
        p[0] = p[1]

    def p_error(p):
        if p:
            p.lexer.lexpos -= len(str(p.value))
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
    'div' : (lambda u, v: twoc(int(untwoc(u) / untwoc(v)))),
    'mod' : (lambda u, v: twoc(untwoc(u) - untwoc(v) * int(untwoc(u) / untwoc(v)))),
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
jumps = {
    'jz':  (lambda k: k == 0),
    'jnz': (lambda k: k != 0),
    'jl':  (lambda k: untwoc(k) < 0),
    'jle': (lambda k: untwoc(k) <= 0),
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

    labels = dict()
    for i, instr in enumerate(prog):
        if instr.opcode != 'label': continue
        if instr.arg1 in labels:
            raise RuntimeError(f'Reused label {instr.arg1}')
        labels[instr.arg1] = i + 1 # spot right after the label

    pc = 0
    while pc in range(len(prog)):
        instr = prog[pc]

        if show_instr: print(f'// [{pc: 4d}] {instr}')
        if instr.opcode == 'nop' or instr.opcode == 'label':
            pc += 1
        elif instr.opcode == 'jmp':
            if instr.arg1 not in labels:
                raise RuntimeError(f'Unknown jump destination {instr.arg1}')
            pc = labels[instr.arg1]
        elif instr.opcode in jumps:
            k = read_temp(instr.arg1, 'cond')
            if instr.arg2 not in labels:
                raise RuntimeError(f'Unknown jump destination {instr.arg2}')
            pc = labels[instr.arg2] if jumps[instr.opcode](k) else pc + 1
        elif instr.opcode == 'const':
            if not isinstance(instr.arg1, int):
                print(f'Missing or bad argument: {instr.arg1}')
                raise RuntimeError
            write_temp(instr.dest, twoc(instr.arg1), 'lhs')
            pc += 1
        elif instr.opcode == 'copy':
            write_temp(instr.dest, read_temp(instr.arg1, 'source'), 'dest')
            pc += 1
        elif instr.opcode == 'print':
            u = read_temp(instr.arg1, 'arg')
            if only_decimal:
                print(str(untwoc(u)))
            else:
                print(f'{untwoc(u): 20d}  0x{u:016x}  0b{u:064b}')
            pc += 1
        elif instr.opcode in binops:
            u = read_temp(instr.arg1, '1st operand')
            v = read_temp(instr.arg2, '2nd operand')
            write_temp(instr.dest, binops[instr.opcode](u, v), 'dest')
            pc += 1
        elif instr.opcode in unops:
            u = read_temp(instr.arg1, 'arg')
            if instr.arg2 != None:
                print(f'Unary operator {self.opcode} has two arguments!')
                raise RuntimeError
            write_temp(instr.dest, unops[instr.opcode](u), 'dest')
            pc += 1
        else:
            print(f'Unknown opcode {instr.opcode}')
            raise RuntimeError

# --------------------------------------------------------------------------------

lexer = None
parser = None

if '__file__' in globals():
    lexer  = __create_lexer()
    parser = __create_parser()

def load_tac(tac_file):
    """Load the TAC instructions from the given `tac_file'"""
    lexer.load_source(tac_file)
    return parser.parse(lexer=lexer)

if __name__ == '__main__':
    from argparse import ArgumentParser
    ap = ArgumentParser(description='TAC library, parser, and interpreter')
    ap.add_argument('files', metavar='FILE', type=str, nargs='*', help='A TAC file')
    ap.add_argument('-v', dest='verbosity', default=0, action='count',
                    help='increase verbosity')
    ap.add_argument('--no-exec', dest='onlyparse', action='store_true',
                    default=False, help='do not run the interpreter')
    args = ap.parse_args()
    for srcfile in args.files:
        prog = load_tac(srcfile)
        if args.onlyparse:
            if args.verbosity > 0:
                for instr in prog: print(instr)
        else:
            execute(prog, show_instr=(args.verbosity>0), only_decimal=(args.verbosity<=1))
