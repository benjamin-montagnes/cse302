#!/usr/bin/env python3

"""
BX2 scanner and parser
"""

from ply import lex, yacc
from ply_util import *
import ast

# Reserved keywords
reserved = {
    'var'     : 'VAR',
    'int'     : 'INT',
    'bool'    : 'BOOL',
    'void'    : 'VOID',
    'true'    : 'TRUE',
    'false'   : 'FALSE',
    'proc'    : 'PROC',
    'if'      : 'IF',
    'else'    : 'ELSE',
    'while'   : 'WHILE',
    'break'   : 'BREAK',
    'continue': 'CONTINUE',
    'return'  : 'RETURN',
    'print'   : 'PRINT',
}

# All tokens
tokens = (
    # Punctuation
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
    'COMMA', 'COLON', 'SEMICOLON', 'EQ',
    # Arithmetic Operators
    'PLUS', 'MINUS', 'STAR', 'SLASH', 'PERCENT',
    'AMP', 'BAR', 'CARET', 'TILDE',
    'LTLT', 'GTGT',
    'EQEQ', 'NEQ', 'LT', 'LTEQ', 'GT', 'GTEQ',
    'AMPAMP', 'BARBAR', 'NOT', 'UMINUS',
    # Primitives
    'IDENT', 'NUMBER',
) + tuple(reserved.values())

# ------------------------------------------------------------------------------

def print_error_message(tok, msg):
    """Print an error message `msg' at the location of `tok'"""
    lineno = tok.lexer.lineno
    if hasattr(tok.lexer, 'lexmatch'):
        tokstr = tok.lexer.lexmatch.group(0)
        curpos = tok.lexer.lexpos - len(tokstr)
    else:
        tokstr = tok.value[0]
        curpos = tok.lexer.lexpos
    # scan backwards from curpos for the position of the beginning of line (bol)
    bolpos = tok.lexer.lexdata.rfind('\n', 0, curpos) + 1
    # scan forwards from curpos for the position of the end of the line (eol)
    eolpos = tok.lexer.lexdata.find('\n', curpos)
    if eolpos == -1: eolpos = tok.lexer.lexlen
    # offset of the given token
    charpos = max(curpos - bolpos, 0) + 1
    errfile = getattr(tok.lexer, 'errfile', None)
    provenance = getattr(tok.lexer, 'provenance', None)
    if provenance:
        print(f'At {provenance}, line {lineno}, character {charpos}:', file=errfile)
    else:
        print(f'At line {lineno}, character {charpos}:', file=errfile)
    print(msg, file=errfile)
    print('>', tok.lexer.lexdata[bolpos:eolpos], file=errfile)
    print(' '*(charpos+1), '^'*len(tokstr), sep='', file=errfile)

# ------------------------------------------------------------------------------

# LEXER:

def create_lexer():
    t_ignore = ' \t\f\v\r'

    def t_newline_or_comment(t):
        r'\n|//[^\n]*\n?'
        t.lexer.lineno += 1

    # Operators and Punctuation
    t_LPAREN    = r'\('
    t_RPAREN    = r'\)'
    t_LBRACE    = r'\{'
    t_RBRACE    = r'\}'
    t_COMMA     = r'\,'
    t_COLON     = r'\:'
    t_SEMICOLON = r'\;'
    t_EQ        = r'\='
    t_PLUS      = r'\+'
    t_MINUS     = r'\-'
    t_STAR      = r'\*'
    t_SLASH     = r'\/'
    t_PERCENT   = r'\%'
    t_AMP       = r'\&'
    t_BAR       = r'\|'
    t_CARET     = r'\^'
    t_TILDE     = r'\~'
    t_LTLT      = r'\<\<'
    t_GTGT      = r'\>\>'
    t_EQEQ      = r'\=\='
    t_NEQ       = r'\!\='
    t_LT        = r'\<'
    t_LTEQ      = r'\<\='
    t_GT        = r'\>'
    t_GTEQ      = r'\>\='
    t_AMPAMP    = r'\&\&'
    t_BARBAR    = r'\|\|'
    t_NOT       = r'\!'

    # Primitives
    def t_IDENT(t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        t.type = reserved.get(t.value, 'IDENT')
        # t.value == whatever the above regex matches
        return t

    def t_NUMBER(t):
        r'0|-?[1-9][0-9]*'
        # t.type == 'NUMBER'
        t.value = int(t.value)
        if not (t.value >= -(1<<63) and t.value < (1<<63)):
            print_error_message(t, f'Error: numerical literal {t.value} not in range(0, 1<<63)')
            raise SyntaxError('Bad number')
        return t

    # error messages
    def t_error(t):
        print_error_message(t, f'Warning: skipping illegal character {t.value[0]}')
        t.lexer.skip(1)
    
    return extend_lexer(lex.lex())

# ------------------------------------------------------------------------------

precedence = (
    ('left', 'BARBAR'),
    ('left', 'AMPAMP'),
    ('left', 'BAR'),
    ('left', 'CARET'),
    ('left', 'AMP'),
    ('nonassoc', 'EQEQ', 'NEQ'),
    ('nonassoc', 'LT', 'LTEQ', 'GT', 'GTEQ'),
    ('left', 'LTLT', 'GTGT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'STAR', 'SLASH', 'PERCENT'),
    ('right', 'UMINUS', 'NOT'),
    ('right', 'TILDE'),
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
        p[0] = ast.Variable(p[1])

    def p_expr_number(p):
        '''expr : NUMBER'''
        p[0] = ast.Number(p[1])

    def p_expr_boolean(p):
        '''expr : TRUE
                | FALSE'''
        p[0] = ast.Boolean(p[1])

    def p_expr_call(p):
        '''expr : call'''
        p[0] = p[1]
        
    def p_call(p):
        '''call : PRINT LPAREN args RPAREN
                | IDENT LPAREN args RPAREN'''
        #p[0] = ast.Appl(p[1], *p[3])
        p[0] = ast.Call(p[1], *p[3])

    def p_args(p):
        '''args : e
                | args1'''
        if p[1] is None: p[0] = []
        else: p[0] = p[1]

    def p_args1(p):
        '''args1 : expr
                | expr COMMA args1'''
        if len(p) == 2: p[0] = [p[1]]
        else:
            p[0] = [p[1]]
            p[0].extend(p[3])

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
                | expr EQEQ expr
                | expr NEQ expr
                | expr LT expr
                | expr LTEQ expr
                | expr GT expr
                | expr GTEQ expr
                | expr AMPAMP expr
                | expr BARBAR expr'''
        p[0] = ast.Appl(p[2], p[1], p[3])

    def p_expr_unop(p):
        '''expr : MINUS expr %prec UMINUS
                | UMINUS expr
                | TILDE expr
                | NOT expr'''
        # if p[1] == '-': op = 'u-'
        # else: op = p[1]
        op = p[1]
        p[0] = ast.Appl(op, p[2])

    def p_expr_parens(p):
        '''expr : LPAREN expr RPAREN'''
        p[0] = p[2]

    def p_vardecl(p):
        '''vardecl : VAR varinits COLON ty SEMICOLON'''
        p[0] = ast.VarDecl(p[2], p[4])

    def p_varinits(p):
        '''varinits : varinit
                    | varinit COMMA varinits'''
        if len(p) == 2: p[0] = [p[1]]
        else: 
            p[0] = [p[1]]
            p[0].extend(p[3])

    def p_varinit(p):
        '''varinit : IDENT EQ expr'''
        p[0] = (p[1], p[3])

    def p_stmt(p):
        '''stmt : vardecl
                | assign
                | eval
                | block
                | ifelse
                | while
                | break
                | continue
                | return'''
        p[0] = p[1]

    def p_assign(p):
        '''assign : IDENT EQ expr SEMICOLON'''
        p[0] = ast.Assign(p[1], p[3])

    def p_eval(p):
        '''eval : expr SEMICOLON'''
        p[0] = ast.Eval(p[1])

    def p_while(p):
        '''while : WHILE LPAREN expr RPAREN block'''
        p[0] = ast.While(p[3], p[5])

    def p_return(p):
        '''return : RETURN SEMICOLON
                | RETURN expr SEMICOLON'''
        if len(p) == 3: p[0] = ast.Return(None)
        else: p[0] = ast.Return(p[2])

    def p_break(p):
        '''break : BREAK SEMICOLON'''
        p[0] = ast.Break()

    def p_continue(p):
        '''continue : CONTINUE SEMICOLON'''
        p[0] = ast.Continue()

    def p_ifelse(p):
        '''ifelse : IF LPAREN expr RPAREN block ifcont'''
        p[0] = ast.IfElse(p[3], p[5], p[6])

    def p_ifcont(p):
        '''ifcont : e
                | ELSE ifelse
                | ELSE block'''
        if len(p) == 2: p[0] = None
        else: p[0] = p[2]

    def p_block(p):
        '''block : LBRACE stmts RBRACE'''
        p[0] = ast.Block(p[2])

    def p_stmts(p):
        '''stmts : e
                | stmt stmts'''
        if len(p) == 2: p[0] = []
        else:
            p[0] = [p[1]]
            p[0].extend(p[2])

    def p_decl(p):
        '''decl : vardecl
                | proc'''
        p[0] = p[1]

    def p_e(p):
        '''e : '''
        pass

    def p_S(p):
        '''S : program'''
        p[0] = ast.Program(p[1])

    def p_program(p):
        '''program : e
                | decl program'''
        if len(p) == 2: p[0] = []
        else: 
            p[0] = [p[1]]
            p[0].extend(p[2])

    def p_ty(p):
        '''ty : INT
            | BOOL
            | VOID'''
        if p[1] == 'int': p[0] = ast.Type.INT
        elif p[1] == 'bool': p[0] = ast.Type.BOOL
        else: raise ValueError("'void' is not a valid token")

    def p_proc(p):
        '''proc : PROC IDENT LPAREN params RPAREN retty block'''
        p[0] = ast.Proc(p[2], p[4], p[6], p[7])

    def p_params(p):
        '''params : e
                | paramgroups'''
        if not p[1]: p[0] = []
        else: p[0] = p[1]

    def p_paramgroups(p):
        '''paramgroups : paramgroup
                    | paramgroup COMMA paramgroups'''
        if len(p) == 2: p[0] = [p[1]]
        else: 
            p[0] = [p[1]]
            p[0].extend(p[3])

    def p_paramgroup(p):
        '''paramgroup : paramvars COLON ty'''
        p[0] = (p[1], p[3])

    def p_paramvars(p):
        '''paramvars : IDENT
                        | IDENT COMMA paramvars'''
        if len(p) == 2: p[0] = [p[1]]
        else: 
            p[0] = [p[1]]
            p[0].extend(p[3])

    def p_retty(p):
        '''retty : e
                | COLON ty'''
        if len(p) == 2: p[0] = ast.Type.VOID
        else: p[0] = p[2]

    def p_error(p):
        if not p: return
        p.lexer.lexpos -= len(p.value)
        print_at(p, f'Error: syntax error while processing {p.type}')
        # Note: SyntaxError is a built in exception in Python
        raise SyntaxError(p.type)

    return yacc.yacc(start='S')

# ------------------------------------------------------------------------------


# Create the lexer and the parser
parser = create_parser()
lexer = create_lexer()

def set_source(text):
    """Load some source code directly into the lexer"""
    lexer.input(text)
    lexer.lineno = 1
    lexer.provenance = None

def load_source(filename):
    """Load a file into the lexer"""
    with open(filename, 'r') as f:
        lexer.input(f.read())
        lexer.lineno = 1
        lexer.provenance = f'file "{filename}"'

# --------------------------------------------------------------------------------

if __name__ == '__main__':
    pass
