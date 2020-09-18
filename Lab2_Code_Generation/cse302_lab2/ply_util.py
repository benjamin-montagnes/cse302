#!/usr/bin/env python3

"""
Some utilities for using PLY
"""

from ply import lex, yacc

def print_at(tok, msg):
    """Print an error message `msg' at the location of `tok'"""
    lineno = tok.lexer.lineno
    if hasattr(tok.lexer, 'lexmatch'):
        tokstr = tok.lexer.lexmatch.group(0)
        curpos = tok.lexer.lexpos - len(tokstr)
    else:
        tokstr = str(tok.value)[0]
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

def extend_lexer(lexer):
    import types
    def set_source(self, text):
        """Load some source code directly into the lexer"""
        self.input(text)
        self.lineno = 1
        self.provenance = None
    lexer.set_source = types.MethodType(set_source, lexer)
    def load_source(self, filename):
        """Load a file into the lexer"""
        with open(filename, 'r') as f:
            self.input(f.read())
            self.lineno = 1
            self.provenance = f'file "{filename}"'
    lexer.load_source = types.MethodType(load_source, lexer)
    def __iter__(self):
        while True:
            tok = self.token()
            if not tok: break
            yield tok
    lexer.__iter__ = types.MethodType(__iter__, lexer)
    return lexer
