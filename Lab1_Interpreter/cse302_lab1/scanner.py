#!/usr/bin/env python3

"""
Lexical Scanner (lexer) defined in terms of the PLY/Lex library
"""

import ply.lex as lex

# Reserved keywords
reserved = {
    'print': 'PRINT',
}
### TODO: add other keywords

# All tokens
tokens = (
    # punctuation
    'LPAREN', 'RPAREN', 'SEMICOLON', 'EQ',
    # arithmetic operators
    'PLUS', 'MINUS', 'STAR', 'SLASH', 'PERCENT',
    # primitives
    'IDENT', 'NUMBER',
    # bitwise operator
    'GTGT', 'LTLT', 'TILDE', 'CARET', 'BAR', 'AMP',
) + tuple(reserved.values())
### TODO: add other tokens

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
    print(' ' * (charpos + 1), '^' * len(tokstr), sep='', file=errfile)

# ------------------------------------------------------------------------------

# whitespace, newlines, and comments

t_ignore = ' \t\f\v\r'  # all characters that are simply ignored

def t_newline(t):
    r'\n'
    t.lexer.lineno += 1
    # no token returned

def t_comment(t):
    r'//.*\n?'
    t.lexer.lineno += 1
    # no token returned
    
# operators and punctuation
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_PLUS = r'\+'
t_MINUS = r'-'
t_STAR = r'\*'
t_SLASH = r'/'
t_SEMICOLON = r';'
# TODO: add any other operator/punctuation
t_GTGT = r'\>>'
t_LTLT = r'\<<'
t_TILDE = r'\~'
t_CARET = r'\^'
t_BAR = r'\|'
t_AMP = r'\&'
t_PERCENT = r'\%'
t_EQ = r'\='

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
    if not (0 <= t.value < (1 << 63)):
        print_error_message(t, f'Error: numerical literal {t.value} not in range(0, 1<<63)')
        raise SyntaxError('bad number')
    return t

# TODO: add any other lexer function
    
# error messages
def t_error(t):
    print_error_message(t, f'Warning: skipping illegal character {t.value[0]}')
    t.lexer.skip(1)

# ------------------------------------------------------------------------------
#          You shouldn't need to modify this section

# Create the lexer

lexer = lex.lex()

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
    from os import devnull
    def all_tokens(source):
        """Return all the tokens in `source' as a list"""
        set_source(source)
        with open(devnull, 'w') as lexer.errfile:
            toks = []
            while True:
                tok = lexer.token()
                if not tok: break
                toks.append((tok.type, tok.value, tok.lineno, tok.lexpos))
            return toks
    import unittest
    class _TestLexer(unittest.TestCase):
        def test_punct(self):
            for (punct, tok) in (('(', 'LPAREN'),
                                 (')', 'RPAREN'),
                                 ('+', 'PLUS'),
                                 ('-', 'MINUS'),
                                 ('*', 'STAR'),
                                 ('/', 'SLASH'),
                                 (';', 'SEMICOLON')):
                self.assertEqual(all_tokens(punct), [(tok, punct, 1, 0)])
        def test_reserved(self):
            for kwd, tok in reserved.items():
                self.assertEqual(all_tokens(kwd), [(tok, kwd, 1, 0)])
        def test_nonreserved(self):
            self.assertEqual(all_tokens('mary had a little lambda'),
                             [('IDENT', 'mary', 1, 0),
                              ('IDENT', 'had', 1, 5),
                              ('IDENT', 'a', 1, 9),
                              ('IDENT', 'little', 1, 11),
                              ('IDENT', 'lambda', 1, 18)])
        def test_number(self):
            self.assertEqual(all_tokens('0 1 42 100'),
                             [('NUMBER', 0, 1, 0),
                              ('NUMBER', 1, 1, 2),
                              ('NUMBER', 42, 1, 4),
                              ('NUMBER', 100, 1, 7)])
        def test_bad_number(self):
            self.assertRaisesRegex(SyntaxError, 'bad number',
                                   all_tokens, f' {1<<20}      {1<<63} abc\n{1<<20}')
        def test_bad_input(self):
            self.assertEqual(all_tokens('  `  ? !'), [])
        # TODO: add any other unit tests
    unittest.main()
    