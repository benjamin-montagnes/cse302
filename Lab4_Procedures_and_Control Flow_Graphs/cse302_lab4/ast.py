#!/usr/bin/env python3

"""
BX1 Abstract Syntax Tree (with optional types)
"""

# ------------------------------------------------------------------------------
# Types of BX1

class Type:
    """Parent class of all types"""
    pass

class _Basic(Type):
    """Basic types"""
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
               and self.name == other.name

INT  = _Basic('int')
BOOL = _Basic('bool')
# VOID = _Basic('void') # not needed yet

class FUNC(Type):
    """Function types"""
    def __init__(self, result, *args):
        self.result = result or VOID
        self.args = args

    def __str__(self):
        if not hasattr(self, '_str'):
            self._str = f'({", ".join(str(ty) for ty in self.args)}) -> {self.result!s}'
        return self._str

    def __hash__(self):
        return hash((self.result, *self.args))

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
               and self.result == other.result \
               and self.args == other.args

# ------------------------------------------------------------------------------
# Expression

class Expr:
    """Parent class of all expressions"""
    __slots__ = ('_ty',)

    @property
    def ty(self):
        """Read the type of the expression"""
        return self._ty

class Number(Expr):
    """64-bit signed integers (2's complement)"""
    def __init__(self, value):
        if not isinstance(value, int):
            raise ValueError(f'Invald Boolean: {val}')
        self.value = value
        self._ty = INT

    def type_check(self, scopes):
        pass

class Boolean(Expr):
    """Booleans"""
    def __init__(self, value):
        if not isinstance(value, bool):
            raise ValueError(f'Invald Boolean: {val}')
        self.value = value
        self._ty = BOOL

    def type_check(self, scopes):
        pass

class Variable(Expr):
    """Variables"""
    def __init__(self, name):
        self.name = name

    def type_check(self, scopes):
        # for scope in reversed(scopes):
        #     if self.name in scope:
        #         self._ty = scope[self.name]
        # raise TypeError(f'Cannot determine type: '
        #                 f'variable {self.name} not in scope')
        self._ty = INT

_arith2_ty = FUNC(INT, INT, INT)
_rel2_ty   = FUNC(BOOL, INT, INT)
_bool2_ty  = FUNC(BOOL, BOOL, BOOL)
_builtins = {
    '+': _arith2_ty, '-': _arith2_ty,
    '*': _arith2_ty, '/': _arith2_ty, '%': _arith2_ty,
    'u-': FUNC(INT, INT),
    '&': _arith2_ty, '|': _arith2_ty, '^': _arith2_ty,
    '>>': _arith2_ty, '<<': _arith2_ty,
    '~': FUNC(INT, INT),
    '==': _rel2_ty, '!=': _rel2_ty,
    '<': _rel2_ty, '<=': _rel2_ty,
    '>': _rel2_ty, '>=': _rel2_ty,
    '&&': _bool2_ty, '||': _bool2_ty,
    '!': FUNC(BOOL, BOOL),
}

class Appl(Expr):
    def __init__(self, func, *args):
        if func not in _builtins:
            raise ValueError(f'Unknown operator {func}')
        if len(_builtins[func].args) != len(args):
            raise ValueError(f'Arity mismatch for {func}: '
                             f'expected {len(__builtins[func].args)}, got {len(args)}')
        self.func = func
        self.args = args

    def type_check(self, scopes):
        func_ty = _builtins[self.func]
        for i, arg_ty in enumerate(func_ty.args):
            self.args[i].type_check(scopes)
            if self.args[i].ty != arg_ty:
                raise TypeError(f'Type mismatch for {self.func}, argument #{i + 1}: '
                                f'expected {arg_ty}, got {self.args[i].ty}')
        self._ty = func_ty.result

# ------------------------------------------------------------------------------
# Statements

class Stmt:
    """Parent class of all statements"""
    pass

class Assign(Stmt):
    """Assignment statements"""
    def __init__(self, var, value):
        if not all([isinstance(var, Variable), isinstance(value, Expr)]):
            raise ValueError(f'Invalid assignment: {var} = {value}')
        self.var = var
        self.value = value

    def type_check(self, scopes):
        self.var.type_check(scopes)
        self.value.type_check(scopes)
        if self.var.ty != self.value.ty:
            raise TypeError(f'Type mismatch in assignment: '
                            f'lhs is {self.var.ty}, rhs is {self.value.ty}')

class Print(Stmt):
    """Print statements"""
    def __init__(self, arg):
        if not isinstance(arg, Expr):
            raise ValueError(f'Invalid print: print({arg})')
        self.arg = arg

    def type_check(self, scopes):
        self.arg.type_check(scopes)
        if self.arg.ty is not INT:
            raise TypeError(f'Type mismatch in print argument: '
                            f'expected {INT}, got {self.arg.ty}')

class Block(Stmt):
    """Block statements"""
    def __init__(self, *stmts):
        for i, stmt in enumerate(stmts):
            if not isinstance(stmt, Stmt):
                raise ValueError(f'Unexpected object (position {i + 1}) in block: '
                                 f'{stmt}')
        self.body = stmts

    def type_check(self, scopes):
        try:
            scopes.append(dict())
            for stmt in self.body:
                stmt.type_check(scopes)
        finally:
            scopes.pop()

class IfElse(Stmt):
    """Conditional statements"""
    def __init__(self, cond, thn, els):
        if not all([isinstance(cond, Expr),
                    isinstance(thn, Block),
                    isinstance(els, Block)]):
            raise ValueError(f'Invalid IfElse: if ({cond}) {thn} else {els}')
        self.cond = cond
        self.thn = thn
        self.els = els

    def type_check(self, scopes):
        self.cond.type_check(scopes)
        if self.cond.ty is not BOOL:
            raise TypeError(f'Type mismatch in IfElse condition: '
                            f'expected {BOOL}, got {self.cond.ty}')
        self.thn.type_check(scopes)
        self.els.type_check(scopes)

class While(Stmt):
    """While loops"""
    def __init__(self, cond, body):
        if not all([isinstance(cond, Expr),
                    isinstance(body, Block)]):
            raise ValueError(f'Invalid While: while ({cond}) {body}')
        self.cond = cond
        self.body = body

    def type_check(self, scopes):
        self.cond.type_check(scopes)
        if self.cond.ty is not BOOL:
            raise TypeError(f'Type mismatch in While condition: '
                            f'expected {BOOL}, got {self.cond.ty}')
        self.body.type_check(scopes)

class Break(Stmt):
    """Structured jump -- break"""
    def type_check(self, scopes):
        pass

class Continue(Stmt):
    """Structured jump -- continue"""
    def type_check(self, scopes):
        pass
