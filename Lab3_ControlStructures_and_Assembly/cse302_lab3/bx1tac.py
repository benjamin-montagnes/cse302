"""Benjamin Montagnes, Antonin Wattel"""


#import bx1_parser
import bx0
from tac import Instr, execute
import ast

binop_code = {
    '+': 'add',
    '-': 'sub',
    '*': 'mul',
    '/': 'div',
    '%': 'mod',
    '&': 'and',
    '|': 'or',
    '^': 'xor',
    '<<': 'shl',
    '>>': 'shr',
}

unop_code = {
    '-': 'neg',
    '~': 'not',
}

class Context:
    """Context of the compiler"""

    def __init__(self):
        self.instrs = []
        self._varmap = dict()
        self._last_temp = -1
        self._last_L = -1
        self.equality_op_map = {'==':'je',
                           '!=':'jnz',
                           '<':'jl',
                           '<=':'jle'}
        self.break_stack = [] #is it ok to put that here ??
        self.continue_stack = []

    def emit(self, *new_instrs):
        """Extend the instructions with `new_instrs'"""
        self.instrs.extend(new_instrs)

    def fresh_temp(self):
        """Allocate and return a fresh temporary"""
        self._last_temp += 1
        return '%' + str(self._last_temp)
    
    def fresh_L(self):
        """Allocate and return a fresh temporary"""
        self._last_L += 1
        return '.L' + str(self._last_L)

    def lookup_temp(self, var):
        """Lookup the temporary mapped to `var', allocating if necessary"""
        if var not in self._varmap:
            self._varmap[var] = self.fresh_temp()
        return self._varmap[var]
    
def build_expr_ast(pt): 
    """transform parse tree expression into ast typed expression"""
    print('expression opcode: ', pt.opcode)
    print('expression value', pt.value)
    if pt.opcode == 'binop':
        return ast.Appl(pt.value, build_expr_ast(pt.kids[0]), build_expr_ast(pt.kids[1]))
    elif pt.opcode == 'unop':
        return ast.Appl(pt.value, build_expr_ast(pt.kids[0]))
    elif pt.opcode == 'num':
        return ast.Number(pt.value)
    elif pt.opcode == 'var':
        return ast.Variable(pt.value)
    #is that all ???

def build_stmt_ast(pt_stmt):
    """transform parse tree statement into ast typed statement"""
    if stmt.opcode == 'assign':
        print('assign')
        print('kid 1 ', build_expr_ast(stmt.kids[1]))
        return ast.Assign(build_expr_ast(stmt.kids[0]), build_expr_ast(stmt.kids[1]))
    elif stmt.opcode == 'print':
        return ast.Print(build_expr_ast(stmt.kids[0]))
    elif stmt.opcode == 'block':
        return ast.Print(build_expr_ast(stmt.kids[0]))
    elif stmt.opcode == 'ifelse':
        return ast.IfElse(build_expr_ast(stmt.kids[0]), 
                          ast.Block(*[build_stmt_ast(block_stmt) for block_stmt in stmt.kids[1]]),
                          ast.Block(*[build_stmt_ast(block_stmt) for block_stmt in stmt.kids[1]]) if stmt.kids[2] else None )
    elif stmt.opcode == 'while':
        return ast.While(build_expr_ast(stmt.kids[0]), 
                         ast.Block(*[build_stmt_ast(block_stmt) for block_stmt in stmt.kids[1]]))
    elif stmt.opcode == 'break':
        return ast.Break()
    elif stmt.opcode == 'continue':
        return ast.Continue()
        

# #we shouldn't need that shit
# def tmm_expr(cx, expr, tdest):
#     """Typed Top-down maximal munch of the expression 'expr' with the result in 'tdest'"""
#     if expr.ty() == ast.Type.BOOL: #not sure this is the right syntax
#         tmm_bool_expr(cx, expr, t_dest)
#     else : ##==INT
#         tmm_int_expr(expr, lab_true, lab_false)
#     #will this when expr is an application ?
        
            
def tmm_int_expr(cx, expr, tdest):
    if isinstance(expr, ast.Number):
        cx.emit(Instr(tdest, 'const', expr.value, None))
    elif isinstance(expr, ast.Variable):
        cx.emit(Instr(tdest, 'copy', cx.lookup_temp(expr.name), None))
    
    #there is stuff to fix here...
    elif isinstance(expr, ast.Appl):
        if expr.args[0] and expr.args[1]: #binop
            tl = cx.fresh_temp()
            tmm_expr(cx, expr.args[0], tl)
            tr = cx.fresh_temp()
            tmm_expr(cx, expr.args[1], tr)
            cx.emit(Instr(tdest, expr.func, tl, tr))
        elif expr.args[0]:#unop
            t = cx.fresh_temp()
            tmm_expr(cx, expr.args[0], t)
            cx.emit(Instr(tdest, expr.func, t, None)) 
    else:
        print(f'Unknown expression: {expr}')
        raise RuntimeError
            
        
    
def tmm_bool_expr(cx, expr, lab_true, lab_false):
    """Emit code to evaluate 'bexpr', jumping to 'lab_true' if true and jumping
    to 'lab_false' if false""" #see slides for illustrative cases
    #how do we deal with true and false ??
    #how the fuck do we evaluate expr ??
    
    if type(expr) == 'bool': #is that possible ??
        if expr.value: cx.emit(Instr(None, 'jmp', lab_true, None))#right arguments for instruction ?
        else: cx.emit(Instr(None, 'jmp', None, lab_false))
    
    elif isinstance(expr, ast.Appl):#we can delete this line
        if expr.func in cx.equality_op_map:#as seen in the slides
            t1 = cx.fresh_temp()
            t2 =cx.frash_temp()
            tmm_int_expr(cx, expr.args[0], t1)
            tmm_int_expr(cx, expr.args[1], t2)
            cx.emit(Instr(None, cx.equality_op_map[expr.func], t1, lab_true))
            cx.emit(Instr(None, 'jmp', lab_false, None))
        
        elif expr.func == '!':
            tmm_bool_expr(cx, expr, lab_true, lab_false)
            
        elif expr.func in ('&&','||'):
            pass #implement short-circuiting
            
            
# def tmm_expr(cx, e, tdest):
#     """Top-down maximal munch of the expression `e' with the result in `tdest'"""
#     if e.opcode == 'num':
#         cx.emit(Instr(tdest, 'const', e.value, None))
#     elif e.opcode == 'var':
#         cx.emit(Instr(tdest, 'copy', cx.lookup_temp(e.value), None))
#     elif e.opcode == 'binop':
#         tl = cx.fresh_temp()
#         tmm_expr(cx, e.kids[0], tl)
#         tr = cx.fresh_temp()
#         tmm_expr(cx, e.kids[1], tr)
#         cx.emit(Instr(tdest, binop_code[e.value], tl, tr))
#     elif e.opcode == 'unop':
#         t = cx.fresh_temp()
#         tmm_expr(cx, e.kids[0], t)
#         cx.emit(Instr(tdest, unop_code[e.value], t, None))
#     else:
#         print(f'Unknown expression opcode: {e.opcode}')
#         raise RuntimeError
    
def tmm_stmt(cx, stmt): 
    print('stmt:', stmt)
    if isinstance(stmt, ast.Assign):
        #not good yet
        tmm_int_expr(cx, stmt.lhs, cx.lookup_temp(stmt.args[0].value)) 
        
    elif isinstance(stmt, ast.Print):
        if stmt.opcode == 'print':
            t = cx.fresh_temp()
            tmm_expr(cx, stmt.args[0], t_dest = t)
            cx.emit(Instr(None, 'print', t, None))
        
    elif isinstance(stmt, ast.Block):
        for s in stmt.body:
            tmm_stmt(cx,s)
            
    elif isinstance(stmt, ast.IfElse):
        not_none = stmt.else_ is not None
        Lt, Lf = cx.fresh_L(), cx.fresh_L()
        if not_none: Lo = cx.fresh_L()
        cx.emit(Instr(None, Lt+':', None, None))
        tmm_stmt(cx, stmt.then)
        if not_none: 
            cx.emit(Instr(None, 'jmp', Lo, None))
        cx.emit(Instr(None, Lf+':', None, None))
        if not_none: 
            tmm_stmt(cx, stmt.else_) 
            cx.emit(Instr(None, Lo+':', None, None))
        

    elif isinstance(stmt, ast.While):
        Lhead, Lbod, Lend = cx.fresh_L(), cx.fresh_L(), cx.fresh_L()
        cx.break_stack.push(Lend)
        cx.continue_stack.push(Lhead)
        cx.emit(Instr(None, Lhead+':', None, None))
        tmm_bool_expr(cx, stmt.cond, Lbod, Lend)
        cx.emit(Instr(None, Lbod+':', None, None))#right way to do it ?
        tmm_stmt(cx, stmt.body)
        cx.emit(Instr(None, 'jmp', Lhead, None))
        cx.emit(Instr(None, Lend+':', None, None))
        cx.break_stack.pop()
        cx.continue_stack.pop()
        
    elif isinstance(stmt, ast.Break):
        cx.emit(Instr(None, 'jmp', cx.break_stack[-1], None))
    
    elif isinstance(stmt, ast.Continue):
        cx.emit(Instr(None, 'jmp', cx.continue_stack[-1], None))
    
    else:
        print(f'Unknown statement')
        raise RuntimeError
        

# def tmm_stmt(cx, s):
#     """Top-down maximal munch of the statement s"""s
#     if s.opcode == 'print':
#         t = cx.fresh_temp()
#         tmm_expr(cx, s.kids[0], t)
#         cx.emit(Instr(None, 'print', t, None))
#     elif s.opcode == 'assign':
#         tmm_expr(cx, s.kids[1], cx.lookup_temp(s.kids[0].value))
#     else:
#         print(f'Unknown stmt opcode: {s.opcode}')
#         raise RuntimeError


import functools

def copy_propagate(cx):
    for i, copy_instr in enumerate(cx.instrs):
        if copy_instr.opcode != 'copy': continue
        t_new = copy_instr.dest
        t_old = copy_instr.arg1
        # in following instructions, replace t_new with t_old
        #   keep doing this while neither has been reset
        for j in range(i + 1, len(cx.instrs)):
            instr = cx.instrs[j]
            if instr.arg1 == t_new: instr.arg1 = t_old
            if instr.arg2 == t_new: instr.arg2 = t_old
            if instr.dest == t_old or instr.dest == t_new: break

def eliminate_dead_copies(cx):
    nop = Instr(None, 'nop', None, None)
    for i, copy_instr in enumerate(cx.instrs):
        if copy_instr.opcode != 'copy': continue
        t_new = copy_instr.dest
        dead = True             # start by assuming it's dead
        # The loop below will determine if it's actually live
        for j in range(i + 1, len(cx.instrs)):
            instr = cx.instrs[j]
            if instr.arg1 == t_new or instr.arg2 == t_new:
                dead = False
                # it's actually live so no need to check further
                break
            if instr.dest == t_new:
                # it got reset, so we can stop looking for reads
                break
        if dead: cx.instrs[i] = nop
    cx.instrs = list(filter(lambda i: i is not nop, cx.instrs))

if __name__ == '__main__':
    import sys, getopt, time
    opts, bx_files = getopt.getopt(sys.argv[1:],
                                   'hvim:',
                                   ['no-prop', 'no-dce'])
    verbosity = 0
    interpret = False
    #mm = bmm_stmt
    mm = tmm_stmt
    do_propagate = True
    do_dce = True
    for opt, val in opts:
        if opt == '-h':
            print(f'''\
USAGE: {sys.argv[0]} OPTIONS file.bx ...

Where OPTIONS is one of

  -v          Increase verbosity (can be used multiple times)
  -i          Run the TAC interpreter instead of writing TAC files
  -m <alg>    Use <alg> as the munch algorithm (default: bmm)
  --no-prop   Do not propagate copies
  --no-dce    Do not eliminate dead copies
  -h          Print this help message''')
            exit(0)
        elif opt == '-v':
            verbosity += 1
        elif opt == '-i':
            interpret = True
        elif opt == '-m':
            if val == 'tmm':
                mm = tmm_stmt
            #elif val == 'bmm':
                #mm = bmm_stmt
            else:
                print(f'Unknown algorithm {val}')
                exit(1)
        elif opt.startswith('--no-prop'):
            do_propagate = False
        elif opt == '--no-dce':
            do_dce = False
        else:
            print(f'Unknown option {opt}')
            exit(1)
    for bx_file in bx_files:
        if not bx_file.endswith('.bx'):
            print(f'File name does not end in ".bx"')
            exit(1)
        cx = Context()
        bx0.lexer.load_source(bx_file)
        bx0_prog = bx0.parser.parse(lexer=bx0.lexer)
        print('bx0_prog:', type(bx0_prog[0]))
        for stmt in bx0_prog:
            stmt_ast = build_stmt_ast(stmt)
            mm(cx, stmt_ast)
        if do_propagate:
            copy_propagate(cx)
        if do_dce:
            eliminate_dead_copies(cx)
        if interpret:
            execute(cx.instrs, show_instr=(verbosity>0), only_decimal=(verbosity<=1))
        else:
            tac_file = bx_file[:-3] + '.tac'
            with open(tac_file, 'w') as f:
                print(f'// {bx_file}, compiled at {time.strftime("%Y-%m-%d %H:%M:%S")}', file=f)
                for instr in cx.instrs:
                    print(instr, file=f)
            if verbosity > 0:
                print(f'{bx_file} -> {tac_file} done')