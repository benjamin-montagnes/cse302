"""Benjamin Montagnes, Antonin Wattel"""
#classes for AST structure with support for type information

class Type:
    pass

class __Basic(Type):
    def __init__(self, name):
        self.name = name
    
class __Func(Type):
    def __init__(self, result, *args):
        self.result = result
        self.args = args

Type.BOOL = __Basic('bool')
Type.INT  = __Basic('int')
Type.FUNC = __Func


class Expr:
    @property
    def ty(self):
        return self._ty #maybe it should be self.ty
    
    def builtin_ops(self):
        __builtin_ops ={
        '+' : Type.FUNC(Type.INT, Type.INT, Type.INT),
        '-' : Type.FUNC(Type.INT, Type.INT, Type.INT), # HOW DO WE DEAL WITH TWO '-' ???
        '||' : Type.FUNC(Type.BOOL, Type.BOOL, Type.BOOL),
        '|' : Type.FUNC(Type.INT, Type.INT, Type.INT)   ,
        '^' : Type.FUNC(Type.INT, Type.INT, Type.INT),
        '&&' : Type.FUNC(Type.BOOL, Type.BOOL, Type.BOOL),
        '&' : Type.FUNC(Type.INT, Type.INT, Type.INT) ,
        '==' : Type.FUNC(Type.BOOL, Type.INT, Type.INT),
        '!=' : Type.FUNC(Type.BOOL, Type.INT, Type.INT),
        '>' : Type.FUNC(Type.BOOL, Type.INT, Type.INT),
        '<=' : Type.FUNC(Type.BOOL, Type.INT, Type.INT),
        '<' : Type.FUNC(Type.BOOL, Type.INT, Type.INT),
        '>=' : Type.FUNC(Type.BOOL, Type.INT, Type.INT),
        '>>' : Type.FUNC(Type.INT, Type.INT, Type.INT),
        '<<' : Type.FUNC(Type.INT, Type.INT, Type.INT) ,
        '*' : Type.FUNC(Type.INT, Type.INT, Type.INT),
        '/' : Type.FUNC(Type.INT, Type.INT, Type.INT) ,
        '%' : Type.FUNC(Type.INT, Type.INT, Type.INT) ,
        'u-' : Type.FUNC(Type.INT, Type.INT),
        '!' : Type.FUNC(Type.BOOL, Type.BOOL),
        '~' : Type.FUNC(Type.INT, Type.INT),
        }
        return __builtin_ops

class Number(Expr):
    def __init__(self, value):
        self.value = value
        self._ty = Type.INT

class Boolean(Expr): #I'm not sure we should do this...
    def __init__(self, value):
        self.value = value
        self._ty = Type.BOOL
        
class Variable(Expr):
    def __init__(self, name):
        self.name = name
        self._ty = Type.INT



class Appl(Expr):
    def __init__(self, func, *args):
        self.func = func
        self.args = args
        #if func not in __builtin_ops:
        if func not in self.builtin_ops():
            raise ValueError(f'Unknown operator: {func}')
        #func_ty = __builtin_ops[func]
        func_ty = self.builtin_ops()[func]
        for i, arg in enumerate(args):
            print('i :',i)
            print('Arg.ty : ', 'int' if arg.ty == Type.INT else 'not an int')
            print('func_ty.ty: ', 'int' if func_ty.args[i]== Type.INT else 'not an int')
            print('Processing : ', func)
            if arg.ty != func_ty.args[i]:
                raise ValueError(f'Bad type for {func} argument #{i+1};', f'Expected {func_ty.args[i]}, got {arg.ty}')
        self._ty = func_ty.result
    
    
class Stmt:
    pass 

class Assign(Stmt):
    def __init__(self, lhs, rhs):
        assert (isinstance(lhs, Variable) and isinstance(rhs, Expr) and rhs.ty is Type.INT)
        self.lhs, self.rhs = lhs, rhs

class Print(Stmt):
    def __init__(self, arg):
        assert isinstance(arg, Expr) and arg.ty is Type.INT 
        self.arg = arg
        
class Block(Stmt):
    """Represents {s1 s2 ...sn }"""
    def __init__(self, *stmts):
        self.body = stmts

class IfElse(Stmt):
    def __init__(self, cond, then, else_=None):
        assert isinstance(cond, Expr) and cond.ty is Type.BOOL
        # print('coucou else', (isinstance(else_, Block)))
        # print('coucou else rien', else_)
        # print('coucou then', then)
        if isinstance(else_, IfElse): 
            print('ERROR : _else is not of type Block - Skipping this IF:', else_)
            else_ = None
        assert isinstance(then, Block) and (isinstance(else_, Block) or else_ is None) #else_ could be None in Fact
        self.cond, self.then, self.else_ = cond, then, else_
        
class While(Stmt):
    def __init__(self, cond, body):
        assert isinstance(cond, Expr) and cond.ty is Type.BOOL
        self.cond,self.body = cond, body
        
class Break(Stmt): pass #??
class Continue(Stmt):pass #??

#implement the break stack and continue stack ????? see slides
        
    
    
        
    