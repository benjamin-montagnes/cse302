#!/usr/bin/env python3

"""
BX1 scanner and parser
"""

from ply import lex, yacc
from ply_util import *

# Reserved keywords
reserved = {
    'print': 'PRINT',
    'while': 'WHILE',
    'true': 'TRUE',
    'false': 'FALSE',
    'if': 'IF',
    'else': 'ELSE',
    'break': 'BREAK',
    'continue': 'CONTINUE',
}

# All tokens
tokens = (
    # punctuation
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'SEMICOLON', 'EQ',
    # arithmetic operators
    'PLUS', 'MINUS', 'STAR', 'SLASH', 'PERCENT',
    'AMP', 'BAR', 'CARET', 'LTLT', 'GTGT',
    'TILDE', 'UMINUS',
    # comparison operators
    'EQEQ', 'BANGEQ', 'LT', 'LTEQ', 'GT', 'GTEQ',
    # boolean operators
    'AMPAMP', 'BARBAR', 'BANG',
    # primitives
    'IDENT', 'NUMBER',
) + tuple(reserved.values())

def create_lexer():
    t_ignore = ' \t\f\v\r'

    def t_newline_or_comment(t):
        r'\n|//[^\n]*\n?'
        t.lexer.lineno += 1

    # operators and punctuation
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_TILDE = r'~'
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_STAR = r'\*'
    t_SLASH = r'/'
    t_PERCENT = r'%'
    t_AMPAMP = r'&&'
    t_BARBAR = r'\|\|'
    t_AMP = r'&'
    t_BAR = r'\|'
    t_CARET = r'\^'
    t_EQEQ = r'=='
    t_BANGEQ = r'!='
    t_LT = r'<'
    t_LTEQ = r'<='
    t_GT = r'>'
    t_GTEQ = r'>='
    t_BANG = r'!'
    t_LTLT = r'<<'
    t_GTGT = r'>>'
    t_EQ = r'='
    t_SEMICOLON = r';'

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
    ('left', 'BARBAR'),
    ('left', 'AMPAMP'),
    ('left', 'BAR'),
    ('left', 'CARET'),
    ('left', 'AMP'),
    ('nonassoc', 'EQEQ', 'BANGEQ'),
    ('nonassoc', 'LT', 'LTEQ', 'GT', 'GTEQ'),
    ('left', 'LTLT', 'GTGT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'STAR', 'SLASH', 'PERCENT'),
    ('left', 'UMINUS', 'BANG'),
    ('left', 'TILDE'),
)

import ast

def create_parser():
    def p_expr_ident(p):
        '''expr : IDENT'''
        p[0] = ast.Variable(p[1])

    def p_expr_number(p):
        '''expr : NUMBER'''
        p[0] = ast.Number(p[1])

    def p_expr_boolean(p):
        '''expr : TRUE
                | FALSE'''
        p[0] = ast.Boolean(p[1] == 'true')

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
                | expr AMPAMP expr
                | expr BARBAR expr
                | expr EQEQ expr
                | expr BANGEQ expr
                | expr LT expr
                | expr LTEQ expr
                | expr GT expr
                | expr GTEQ expr'''
        p[0] = ast.Appl(p[2], p[1], p[3])

    def p_expr_unop(p):
        '''expr : MINUS expr %prec UMINUS
                | UMINUS expr
                | BANG expr
                | TILDE expr'''
        op = 'u-' if p[1] == '-' else p[1]
        p[0] = ast.Appl(op, p[2])

    def p_expr_parens(p):
        '''expr : LPAREN expr RPAREN'''
        p[0] = p[2]

    def p_stmt_assign(p):
        '''stmt : IDENT EQ expr SEMICOLON'''
        p[0] = ast.Assign(ast.Variable(p[1]), p[3])

    def p_stmt_print(p):
        '''stmt : PRINT LPAREN expr RPAREN SEMICOLON'''
        p[0] = ast.Print(p[3])

    def p_stmt_while(p):
        '''stmt : WHILE LPAREN expr RPAREN block'''
        p[0] = ast.While(p[3], p[5])

    def p_stmt_escape(p):
        '''stmt : BREAK SEMICOLON
                | CONTINUE SEMICOLON'''
        if p[1] == 'break':
            p[0] = ast.Break()
        else:
            p[0] = ast.Continue()

    def p_ifelse(p):
        '''ifelse : IF LPAREN expr RPAREN block ifcont'''
        p[0] = ast.IfElse(p[3], p[5], p[6])

    def p_ifcont(p):
        '''ifcont : ELSE ifelse
                  | ELSE block
                  | '''
        if len(p) == 1:
            p[0] = ast.Block()
        elif isinstance(p[2], ast.Block):
            p[0] = p[2]
        else:
            p[0] = ast.Block(p[2])

    def p_block(p):
        '''block : LBRACE stmts RBRACE'''
        p[0] = ast.Block(*(p[2]))

    def p_stmt_trivs(p):
        '''stmt : ifelse
                | block'''
        p[0] = p[1]

    def p_stmts(p):
        '''stmts : stmts stmt
                 | '''
        if len(p) == 1:
            p[0] = []
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_program(p):
        '''program : stmts'''
        p[0] = p[1]

    def p_error(p):
        if not p: return
        p.lexer.lexpos -= len(p.value)
        print_at(p, f'Error: syntax error while processing {p.type}')
        # Note: SyntaxError is a built in exception in Python
        raise SyntaxError(p.type)

    return yacc.yacc(start='program')

lexer = None
parser = None

if '__file__' in globals():
    lexer = create_lexer()
    parser = create_parser()
