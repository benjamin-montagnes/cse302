#!/usr/bin/env python3

"""
BX2 Abstract Syntax Tree (with optional types)
"""

# ------------------------------------------------------------------------------
# Types of BX2

class Type:
    """Parent class of all types"""
    pass

class _Basic(Type):
    """Basic types"""
    def __init__(self, _name):
        self.name = _name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()
    
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
               and self.name == other.name

Type.INT   = _Basic('int')
Type.BOOL  = _Basic('bool')
Type.VOID  = _Basic('void')

class FUNC(Type):
    def __init__(self, _result, *_args):
        self.result = _result or Type.VOID
        self.args = _args

    def __str__(self):
        if not hasattr(self, '_str'):
            self._str = f'({", ".join(str(ty) for ty in self.args)}) -> {self.result!s}'
        return self._str

    def __repr__(self):
        return self.__str__()
    
    def __hash__(self):
        return hash((self.result, *self.args))

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
               and self.result == other.result \
               and self.args == other.args

Type.FUNC = FUNC

# ------------------------------------------------------------------------------
# Expression

class Expr:
    """Parent class of all expressions"""
    __slots__= ('_ty',)

    @property
    def ty(self):
        """Read the type of the expression"""
        return self._ty

    def type_check(self):
        # print('16')
        raise RuntimeError("Error with: {}".format(self))

class Number(Expr):
    """64-bit signed integers (2's complement)"""
    def __init__(self, value):
        if not isinstance(value, int): raise ValueError(f'Invalid Number: {value}')
        self.value = value
        self._ty  = Type.INT

    def __str__(self):
        return self.value

    def type_check(self):
        # print('17')
        pass
    
class Boolean(Expr):
    """Booleans"""
    def __init__(self, value):
        if value!='true' and value!='false': raise ValueError(f'Invalid Boolean: {value}')
        self.value = value
        self._ty  = Type.BOOL

    def __str__(self):
        return self.value

    def type_check(self):
        # print('18')
        pass

# ------------------------------------------------------------------------------

class Context:
    """Symbol management"""
    # def _make_builtins():
    #     cx = dict()
    #     ty=FUNC(INT, INT, INT)
    #     for op in ('+', '-', '*', '/', '%', '&', '|', '^', '<<', '>>'):
    #         cx[op] = ty
    #     ty = FUNC(INT, INT)
    #     for op in ('u-', '~'):
    #         cx[op] = ty
    #     ty = FUNC(BOOL, INT, INT)
    #     for op in ('==', "!=", '<', '<=', '>', '>='):
    #         cx[op] = ty
    #     ty = FUNC(BOOL, BOOL, BOOL)
    #     for op in ('&&', '||'):
    #         cx[op] = ty
    #     cx['!'] = FUNC(BOOL, BOOL)
    #     cx['__bx_print_int'] = FUNC(VOID, INT)
    #     cx['__bx_print_bool'] = FUNC(VOID, BOOL)
    #     return cx
    # _builtins = _make_builtins()

    def __init__(self):
        # self.global_defs = self._builtins.copy()
        self.local_defs = [{}]

    @property
    def current(self):
        """Return the current scope"""
        # if len(self.local_defs) == 0:
        #     return self.global_defs
        # else:
        return self.local_defs[-1]
    
    @property
    def first_scope(self):
        return self.local_defs[0]

    def enter(self):
        """enter a new (local) scope"""
        self.local_defs.append({})

    def leave(self):
        """leave a local scope"""
        self.local_defs.pop()

    def _contains_(self):
        return len(self.local_defs) == 1

    def _getitem_(self, name):
        """Lookup the name in the context."""
        for i in range(len(self.local_defs)-1, -1, -1):
            if name in self.local_defs[i]: return self.local_defs[i][name]
        return None
    
    def _str_(self, scope):
        for symbol in scope:
            print("{}\t{}".format(symbol, scope[symbol]))

context = Context()

# ------------------------------------------------------------------------------

class Variable(Expr):
    """Variables"""
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def type_check(self):
        # print('19')
        self._ty = context._getitem_(self.name)
        if self._ty is None:
            raise TypeError(f'Cannot determine type: '
                            f'variable {self.name} not in scope')

Type._arith2_ty = Type.FUNC(Type.INT, Type.INT, Type.INT)
Type._rel2_ty = Type.FUNC(Type.BOOL, Type.INT, Type.INT)
Type._bool2_ty = Type.FUNC(Type.BOOL, Type.BOOL, Type.BOOL)

_builtins = {
    '+' : Type._arith2_ty, '-' : Type._arith2_ty,
    '*' : Type._arith2_ty, '/' : Type._arith2_ty,
    '%' : Type._arith2_ty, '&' : Type._arith2_ty,
    '|' : Type._arith2_ty, '^' : Type._arith2_ty,
    '<<': Type._arith2_ty, '>>': Type._arith2_ty,
    '==': Type._rel2_ty, '!=': Type._rel2_ty,
    '<' : Type._rel2_ty, '<=': Type._rel2_ty,
    '>' : Type._rel2_ty, '>=': Type._rel2_ty,
    '&&': Type._bool2_ty, '||': Type._bool2_ty,
}

Type._unarith2_ty  = Type.FUNC(Type.INT, Type.INT)
Type._unbool2_ty  = Type.FUNC(Type.BOOL, Type.BOOL)

_builtins_unops = {
        '-' : Type._unarith2_ty,
        '~' : Type._unarith2_ty,
        '!' : Type._unbool2_ty,
}

class Appl(Expr):
    def __init__(self, func, *args):
        self.func = func
        self.args = args

    def type_check(self):
        # print('20')
        if self.func == 'print':
            if len(self.args) != 1:
                raise RuntimeError(f"Wrong number of arguments for 'print', expecting 1, got {len(self.args)}")
            self.args[0].type_check()
            if self.args[0].ty == Type.INT: self._ty = Type.VOID
            elif self.args[0].ty == Type.BOOL: self._ty = Type.VOID
            else: raise RuntimeError(f"'print' expecting either int or bool, got {self.args[0].ty}")
            return
        if len(self.args) == 2 and self.func in _builtins: func_ty = _builtins[self.func]
        elif len(self.args) == 1 and self.func in _builtins_unops: func_ty = _builtins_unops[self.func]
        else:
            if (not self.func in context.first_scope) or (not isinstance(context.first_scope[self.func], Type.FUNC)):
                raise RuntimeError(f"Proc '{self.func}' not found in global scope.")
            func_ty = context.first_scope[self.func]
        for arg in self.args: arg.type_check()
        if len(func_ty.args) != len(self.args):
            raise RuntimeError(f"Wrong number of arguments for '{self.func}', expecting {len(func_ty.args)}, got {len(self.args)}")
        for i in range(len(func_ty.args)):
            if func_ty.args[i] != self.args[i].ty:
                raise RuntimeError(f"Wrong types for argument #{i+1} of '{self.func}', expecting {func_ty.args[i]}, got {self.args[i].ty}")
        self._ty = func_ty.result
    
    
class Call(Expr): #pretty similar as Appl
    def __init__(self, name, *args): 
        self.name= name
        self.args = args

    def _str_ (self):
        return f'{self.name}({str(self.args)})'
    
    def type_check(self):
        #to do
        # check that name is not referenced before assignment
        # check types for function arguments
        pass

# ------------------------------------------------------------------------------
# Statements

class Stmt:
    """Parent class of all statements"""
    pass
    def type_check(self):
        # print('1')
        raise RuntimeError(f"Error with: {self}")

class Assign(Stmt):
    """Assignment statements"""
    def __init__(self, var, value):
        self.var = var
        self.value = value

    def type_check(self):
        # print('2')
        self.value.type_check()
        # self.var.type_check()
        ty = context._getitem_(self.var)
        if ty is None:
            raise RuntimeError(f"Variable '{self.var}' must be declared first")
        if ty != self.value.ty:
            raise RuntimeError(f"Wrong type for '{self.var}', expecting {ty}, got {self.value.ty}")

class Block(Stmt):
    """Block statements"""
    def __init__(self, stmts):
        self.body = stmts

    def type_check(self):
        # print('3')
        context.enter()
        for stmt in self.body: stmt.type_check()
        context.leave()

class IfElse(Stmt):
    """Conditional statements"""
    def __init__(self, cond, thn, els):
        self.cond   = cond
        self.thn  = thn
        self.els = els

    def type_check(self):
        # print('4')
        self.cond.type_check()
        if self.cond.ty != Type.BOOL:
            raise TypeError(f'Type mismatch in IfElse condition: '
                            f'expected {Type.BOOL}, got {self.cond.ty}')
        self.thn.type_check()
        if self.els is not None: self.els.type_check()

class While(Stmt):
    """While loops"""
    def __init__(self, cond, body):
        self.cond  = cond
        self.body = body

    def type_check(self):
        # print('5')
        self.cond.type_check()
        if self.cond.ty != Type.BOOL:
            raise TypeError(f'Type mismatch in While condition: '
                            f'expected {Type.BOOL}, got {self.cond.ty}')
        self.body.type_check()

class Break(Stmt):
    """Structured jump -- break"""
    def __init__(self):
        pass
    
    def type_check(self):
        # print('6')
        pass

class Continue(Stmt):
    """Structured jump -- continue"""
    def __init__(self):
        pass

    def type_check(self):
        # print('7')
        pass

class VarDecl(Stmt):
    """Declaration of variable"""
    def __init__(self, names, ty):
        self.names = names
        self.ty = ty

    def type_check_global(self):
        # print('8')
        for name in self.names:
            if not (isinstance(name[1], Number) or isinstance(name[1], Boolean)):
                raise RuntimeError(f"Global declaration for '{name[0]}' must be literal value.")
            if name[1].ty != self.ty:
                raise RuntimeError(f"Wrong type for '{name[0]}', expecting {self.ty}, got {name[1].ty}")
            context.first_scope[name[0]] = name[1].ty 
    
    def type_check(self):
        # print('9')
        if context._contains_(): return
        for name in self.names:
            if name[0] in context.current:
                raise RuntimeError(f"Re-declaration of symbol '{name[0]}'")
            name[1].type_check()
            if name[1].ty != self.ty:
                raise RuntimeError(f"Wrong type for '{name[0]}', expecting {self.ty}, got {name[1].ty}")
            context.current[name[0]] = name[1].ty 

class Eval(Stmt):
    def __init__(self, arg):
        self.arg = arg

    def type_check(self):
        # print('10')
        if not isinstance(self.arg, Expr):
            raise TypeError(f'Expected an Expr got {type(self.arg)}')
        self.arg.type_check()

    def __str__(self):
        return 'evaluate ' + str(self.arg)

class Return(Stmt):
    """return statements"""
    def __init__(self, expr=None):
        self.expr = expr
    
    def type_check(self):
        # print('11')
        raise RuntimeError(f'Missing some return or wrong return type: {type(self.expr)}')
        # if not isinstance(self.expr, Expr):
        #     raise TypeError(f'Expected an Expr got {type(self.expr)}')
        # self.expr.type_check()

# ------------------------------------------------------------------------------
#top-level declariations and programs


class Program:
    def __init__(self, thn):
        self.thn = thn

    def type_check_global(self):
        # print('12')
        for thn in self.thn: thn.type_check_global()

    def type_check(self):
        # print('13')
        for thn in self.thn: thn.type_check()

class Proc:
    def __init__(self, name, params, retty, body):
        self.name = name
        self.params = params
        self.retty = retty
        self.body = body
        self.type = Type.FUNC(self.retty, *(arg[1] for arg in params))

    def type_check_global(self):
        # print('14')
        if self.name in context.first_scope:
            raise ValueError(f'Proc name "{self.name}" is already used')
        args = []
        for param in self.params: args += [param[1]] * len(param[0])
        # self.body.type_check()
        context.first_scope[self.name] = Type.FUNC(self.retty, *args)

    def type_check(self):
        # print('15')
        for param in self.params:
            for var in param[0]: context.current[var] = param[1]
        self.body.type_check()
         
    def __str__(self):
        if self.type == None: return f'proc {self.name}({self.params}) {self.body}' 
        return f'proc {self.name} ({self.params}) {self.type} {self.body}'

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    pass
