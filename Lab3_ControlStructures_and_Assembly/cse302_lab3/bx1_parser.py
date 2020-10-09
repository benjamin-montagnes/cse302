#!/usr/bin/env python3

"""
BX0 scanner and parser
"""

from ply import lex, yacc
from ply_util import *

# Reserved keywords
reserved = {
    'print': 'PRINT',
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'break': 'BREAK',
    'continue': 'CONTINUE',
    'true': 'TRUE',
    'false': 'FALSE'
}

# All tokens
tokens = (
    # punctuation
    'LPAREN', 'RPAREN', 'SEMICOLON', 'EQ',
    # arithmetic operators
    'PLUS', 'MINUS', 'STAR', 'SLASH', 'PERCENT',
    'AMP', 'BAR', 'CARET', 'LTLT', 'GTGT',
    'TILDE', 'UMINUS',
    # primitives
    'IDENT', 'NUMBER',
    # new for booleans
    'LBRACKET', 'RBRACKET',
    # new binary ops
    'BOOLOR', 'BOOLAND', 'BDISEQ', 'BEQ', 'BL', 'BLEQ', 'BS', 'BSEQ', 
    #new unary ops
    'NEG'
) + tuple(reserved.values())

def create_lexer():
    t_ignore = ' \t\f\v\r'

    def t_newline_or_comment(t):
        r'\n|//[^\n]*\n?'
        t.lexer.lineno += 1

    # operators and punctuation
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_TILDE = r'~'
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_STAR = r'\*'
    t_SLASH = r'/'
    t_PERCENT = r'%'
    t_AMP = r'&'
    t_BAR = r'\|'
    t_CARET = r'\^'
    t_LTLT = r'<<'
    t_GTGT = r'>>'
    t_EQ = r'='
    t_SEMICOLON = r';'
    t_LBRACKET = r'\{'
    t_RBRACKET = r'\}'
    t_BOOLOR = r'\|\|'
    t_BOOLAND = r'&&'
    t_BDISEQ = r'!='
    t_BEQ = r'=='
    t_BL = r'<'
    t_BLEQ = r'<='
    t_BS = r'>'
    t_BSEQ = r'>='
    t_NEG = r'\!'

    # primitives

    def t_IDENT(t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        t.type = reserved.get(t.value, 'IDENT')
        # t.value == whatever the above regex matches
        return t

    def t_NUMBER(t):
        r'0|[1-9][0-9]*'
        # t.type == 'NUMBER'
        t.value = int(t.value)
        if not (0 <= t.value < (1<<63)):
            print_at(t, f'Error: numerical literal {t.value} not in range(0, 1<<63)')
            raise SyntaxError('bad number')
        return t

    # error messages
    def t_error(t):
        print_at(t, f'Warning: skipping illegal character {t.value[0]}')
        t.lexer.skip(1)

    return extend_lexer(lex.lex())

precedence = (
    ('left', 'BOOLOR'),
    ('left', 'BOOLAND'),
    ('left', 'BAR'),
    ('left', 'CARET'),
    ('left', 'AMP'),
    ('left', 'BDISEQ', 'BEQ'),
    ('left', 'BL', 'BLEQ', 'BS', 'BSEQ'),
    ('left', 'LTLT', 'GTGT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'STAR', 'SLASH'),
    ('left', 'UMINUS'),
    ('left', 'TILDE'),
)

class Node:
    def __init__(self, opcode, value, *kids):
        self.opcode = opcode
        self.value = value
        self.kids = kids

    def __repr__(self):
        return '({} {}{}{})'\
               .format(self.opcode, repr(self.value),
                       '' if len(self.kids) == 0 else ' ',
                       ' '.join(repr(kid) for kid in self.kids))

    def __eq__(self, other):
        return \
            isinstance(other, Node) and \
            self.opcode == other.opcode and \
            self.value == other.value and \
            self.kids == other.kids

def create_parser():
    def p_expr_ident(p):
        '''expr : IDENT'''
        p[0] = Node('var', p[1])

    def p_expr_number(p):
        '''expr : NUMBER'''
        p[0] = Node('num', p[1])

    def p_expr_binop(p):
        '''expr : expr PLUS  expr
                | expr MINUS expr
                | expr STAR  expr
                | expr SLASH expr
                | expr PERCENT expr
                | expr AMP expr
                | expr BAR expr
                | expr CARET expr
                | expr LTLT expr
                | expr GTGT expr
                | expr BOOLOR expr
                | expr BOOLAND expr
                | expr BDISEQ expr
                | expr BEQ expr
                | expr BL expr
                | expr BLEQ expr
                | expr BS expr
                | expr BSEQ expr'''
        p[0] = Node('binop', p[2], p[1], p[3])

    def p_expr_unop(p):
        '''expr : MINUS expr %prec UMINUS
                | UMINUS expr
                | TILDE expr
                | NEG expr'''
        p[0] = Node('unop', p[1], p[2])
    
    def p_expr_true(p):
        '''expr : TRUE'''
        p[0] = Node('bool',p[1])
        
    def p_expr_false(p):
        '''expr : FALSE'''
        p[0] = Node('bool',p[1])

    def p_expr_parens(p):
        '''expr : LPAREN expr RPAREN'''
        p[0] = p[2]
    
    def p_block(p):
        '''block : LBRACKET stmts RBRACKET'''
        # p[0] = p[2]
        p[0] = Node('block', None, p[2])
        
    def p_stmt_assign(p):
        '''stmt : IDENT EQ expr SEMICOLON'''
        p[0] = Node('assign', p[2], Node('var', p[1]), p[3])

    def p_stmt_print(p):
        '''stmt : PRINT LPAREN expr RPAREN SEMICOLON'''
        p[0] = Node('print', None, p[3])

    def p_stmt_ifelse(p):
        '''stmt : IF LPAREN expr RPAREN block ifrest'''
        # print('yahooo')
        p[0] = Node('ifelse', None, p[3], p[5],p[6])
        
    def p_ifrest(p): # problem here as stmt should be ifelse
        '''ifrest : ELSE stmt 
                | ELSE block
                | '''
        # p[0] = p[2] if len(p)>1 else None
        p[0] = Node('ifrest', None, p[2]) if len(p)>1 else None

    def p_stmt_while(p):
        '''stmt : WHILE LPAREN expr RPAREN block'''
        p[0] = Node('while', None, p[3], p[5])

    def p_stmt_jump(p):
        '''stmt : BREAK SEMICOLON
                | CONTINUE SEMICOLON'''
        p[0] = Node(p[1], None)
                
    def p_stmts(p):
        '''stmts : stmt stmts
                |  '''
        p[0]= [p[1]] + p[2] if len(p)>1 else []
        # if len(p)>1:
        #     p[0]=p[1]
        #     p[0].append(p[2])
        # else:
        #     p[0]=[]
        
    def p_program(p):
        '''program : stmts'''
        p[0] = p[1]
        

    def p_error(p):
        # print("typpeee:",p.type)
        if not p: return
        p.lexer.lexpos -= len(p.value)
        print_at(p, f'Error: syntax error while processing {p.type}')
        # Note: SyntaxError is a built in exception in Python
        # raise SyntaxError(p.type)

    return yacc.yacc(start='program')

lexer = create_lexer()
parser = create_parser()
