#!/usr/bin/env python3

import bx1_parser
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
    # 'u-': 'uminus'
}

equality_op_map = {
    '==': ('jz',1),
    '!=': ('jnz',1),
    '<': ('jl',1),
    '<=': ('jle',1),
     '>': ('jl',-1),
     '>=': ('jle',-1)
    }

class Context:
    """Context of the compiler"""

    def __init__(self):
        self.instrs = []
        self._varmap = dict()
        self._last_temp = -1
        self._last_L = -1
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
        # print('inside lookup_temp:', self._varmap)
        if var not in self._varmap:
            self._varmap[var] = self.fresh_temp()
        return self._varmap[var]
    
def build_expr_ast(pt):
    """transform parse tree expression into ast typed expression"""
    #print('expression opcode: ', pt.opcode)
    #print('expression value', pt.value)
    if pt.opcode == 'binop':
        return ast.Appl(pt.value, build_expr_ast(pt.kids[0]), build_expr_ast(pt.kids[1])) #doesnt work for all ops
    elif pt.opcode == 'unop':
        # if pt.value == '-': pt.value = 'u-'
        return ast.Appl(pt.value, build_expr_ast(pt.kids[0]))
    elif pt.opcode == 'num':
        return ast.Number(pt.value)
    elif pt.opcode == 'var':
        return ast.Variable(pt.value)
    elif pt.opcode == 'bool':
        # print('build_expr_ast: booooooooooooooooooooooooooooooooooooooool')
        # print(pt.value)
        return ast.Boolean(pt.value)

def build_stmt_ast(pt_stmt):
    """transform parse tree statement into ast typed statement"""
    # print('cuild stmt ast: ', stmt.opcode )
    if pt_stmt.opcode == 'assign':
        return ast.Assign(build_expr_ast(pt_stmt.kids[0]), build_expr_ast(pt_stmt.kids[1]))
    elif pt_stmt.opcode == 'print':
        return ast.Print(build_expr_ast(pt_stmt.kids[0]))
    elif pt_stmt.opcode == 'block':
        # print(pt_stmt)
        return ast.Block(*[build_stmt_ast(block_stmt) for block_stmt in pt_stmt.kids[0]])
    elif pt_stmt.opcode == 'ifelse':
         if pt_stmt.kids[2]:
             # print('pt_stmt kidsssssssssssssssssssssssssssssssssssssssssssssssss 2', pt_stmt.kids[2])
             return ast.IfElse(build_expr_ast(pt_stmt.kids[0]), 
                           build_stmt_ast(pt_stmt.kids[1]),#block
                           build_stmt_ast(pt_stmt.kids[2]))
         else:
             return ast.IfElse(build_expr_ast(pt_stmt.kids[0]), 
                           build_stmt_ast(pt_stmt.kids[1]))
             
    elif pt_stmt.opcode == 'ifrest':
        # print('PT KIDSSSS',pt_stmt.kids[0])
        return build_stmt_ast(pt_stmt.kids[0])
    
    elif pt_stmt.opcode == 'while':
        # print('KIDDSSSSSSSSSS', pt_stmt.kids[0])
        return ast.While(build_expr_ast(pt_stmt.kids[0]), 
                         build_stmt_ast(pt_stmt.kids[1]))
    elif pt_stmt.opcode == 'break':
        return ast.Break()
    elif pt_stmt.opcode == 'continue':
        return ast.Continue()
    else:
        print('unknown stmt opcode')
        raise RuntimeError
        
        
            
def tmm_int_expr(cx, expr, tdest):
    if isinstance(expr, ast.Number):
        cx.emit(Instr(tdest, 'const', expr.value, None))
    elif isinstance(expr, ast.Variable):
        cx.emit(Instr(tdest, 'copy', cx.lookup_temp(expr.name), None))
    
    #there is stuff to fix here -> 
    elif isinstance(expr, ast.Appl):
        
        if len(expr.args)==2: #binop
            tl = cx.fresh_temp()
            tmm_int_expr(cx, expr.args[0], tl)
            tr = cx.fresh_temp()
            tmm_int_expr(cx, expr.args[1], tr)
            cx.emit(Instr(tdest, binop_code[expr.func], tl, tr)) #need to use some map -> where ??
        elif len(expr.args)==1:#unop
            t = cx.fresh_temp()
            tmm_int_expr(cx, expr.args[0], t)
            # print('EXPRREEE : ',expr.func)
            cx.emit(Instr(tdest, unop_code[expr.func], t, None)) 
    else:
        print(f'Unknown expression: {expr}')
        raise RuntimeError
    
def tmm_bool_expr(cx, expr, lab_true, lab_false):
    """Emit code to evaluate 'bexpr', jumping to 'lab_true' if true and jumping
    to 'lab_false' if false""" #see slides for illustrative cases
    
    if isinstance(expr, ast.Boolean):
         if expr.value == 'true': cx.emit(Instr(None, 'jmp', lab_true, None))
         else: cx.emit(Instr(None, 'jmp', lab_false, None))
    
    elif isinstance(expr, ast.Appl):
        if expr.func in equality_op_map:#as seen in the slides
            t1, t2 = cx.fresh_temp(), cx.fresh_temp()
            tmm_int_expr(cx, expr.args[0], t1)
            tmm_int_expr(cx, expr.args[1], t2)
            # print('eq_map',equality_op_map[expr.func])
            cx.emit(Instr(None, equality_op_map[expr.func][0], t1, lab_true))
            if equality_op_map[expr.func][1] == 1 :
                cx.emit(Instr(None, 'jmp', lab_true, None))
            elif equality_op_map[expr.func][1] == -1 :
                cx.emit(Instr(None, 'jmp', lab_false, None))
        
        elif expr.func == '!':
            # for i, arg in enumerate(expr.args):
            tmm_bool_expr(cx, expr.args[0], lab_false, lab_true)
                
        elif expr.func == '&&':
            Li = cx.fresh_L()
            tmm_bool_expr(cx, expr.args[0], Li, lab_false)
            cx.emit(Instr(None, 'label',Li,None))
            tmm_bool_expr(cx, expr.args[1], lab_true, lab_false)
            
        elif expr.func == '||':
            Li = cx.fresh_L()
            tmm_bool_expr(cx, expr.args[0], lab_true, Li)
            cx.emit(Instr(None, 'label',Li,None))
            tmm_bool_expr(cx, expr.args[1], lab_true, lab_false)
                          
        
        else: print('ERROR: type(expr) :', type(expr) )
            
    
def tmm_stmt(cx, stmt): 
    if isinstance(stmt, ast.Assign):
        #not good yet
        # print('Assign:', stmt.rhs, stmt.lhs.name)
        
        tmm_int_expr(cx, stmt.rhs, cx.lookup_temp(stmt.lhs.name)) 
        
    elif isinstance(stmt, ast.Print):
        t = cx.fresh_temp()
        tmm_int_expr(cx, stmt.arg, t)
        cx.emit(Instr(None, 'print', t, None))
        
    elif isinstance(stmt, ast.Block):
        for s in stmt.body:
            # for l in s:
                tmm_stmt(cx,s)
            
    elif isinstance(stmt, ast.IfElse):
        not_none = stmt.else_ is not None
        Lt, Lf = cx.fresh_L(), cx.fresh_L()
        if not_none: Lo = cx.fresh_L()
        tmm_bool_expr(cx, stmt.cond, Lt,Lf)
        cx.emit(Instr(None, 'label', Lt, None))
        tmm_stmt(cx, stmt.then)
        if not_none: 
            cx.emit(Instr(None, 'jmp', Lo, None))
        cx.emit(Instr(None, 'label', Lf, None))
        if not_none: 
            tmm_stmt(cx, stmt.else_) 
            cx.emit(Instr(None, 'label', Lo, None))
        # Lt, Lf, Lo = cx.fresh_L(), cx.fresh_L(), cx.fresh_L()
        # tmm_bool_expr(cx, stmt.cond, Lt, Lf)
        # cx.emit(Instr(None,'label',Lt,None))    
        # tmm_stmt(cx, stmt.then)
        # cx.emit(Instr(None,'jmp',Lo,None))     
        # cx.emit(Instr(None,'label',Lf,None)) 
        # tmm_stmt(cx, stmt.else_)
        # cx.emit(Instr(None,'label',Lo,None))
        

    elif isinstance(stmt, ast.While):
        # Lhead, Lbod, Lend = cx.fresh_L(), cx.fresh_L(), cx.fresh_L()
        # cx.break_stack.append(Lend)
        # cx.continue_stack.append(Lhead)
        # #cx.emit(Instr(None, Lhead+':', None, None))
        # #cx.emit(Instr(None, Lhead, None, None))
        # cx.emit(Instr(None, 'label', Lhead, None))
        # tmm_bool_expr(cx, stmt.cond, Lbod, Lend)
        # #cx.emit(Instr(None, Lbod+':', None, None))#right way to do it ?
        # tmm_stmt(cx, stmt.body)
        # cx.emit(Instr(None, 'jmp', Lhead, None))
        # #cx.emit(Instr(None, Lend+':', None, None))
        # #cx.emit(Instr(None, Lend, None, None))
        # cx.emit(Instr(None, 'label', Lend, None))
        # cx.break_stack.pop()
        # cx.continue_stack.pop()
        
        Lhead, Lbod, Lend = cx.fresh_L(), cx.fresh_L(), cx.fresh_L()
        cx.break_stack.append(Lend)
        cx.continue_stack.append(Lhead)
        cx.emit(Instr(None, 'label', Lhead, None))
        tmm_bool_expr(cx, stmt.cond, Lbod, Lend)
        cx.emit(Instr(None, 'label', Lbod, None))
        tmm_stmt(cx, stmt.body)
        cx.emit(Instr(None, 'jmp', Lhead, None))
        cx.emit(Instr(None, 'label', Lhead, None))
        cx.break_stack.pop()
        cx.continue_stack.pop()
        
    elif isinstance(stmt, ast.Break):
        cx.emit(Instr(None, 'jmp', cx.break_stack[-1], None))
    
    elif isinstance(stmt, ast.Continue):
        cx.emit(Instr(None, 'jmp', cx.continue_stack[-1], None))
    
    else:
        print(f'Unknown statement')
        raise RuntimeError


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
        bx1_parser.lexer.load_source(bx_file)
        bx1_prog = bx1_parser.parser.parse(lexer=bx1_parser.lexer)
        # print('bx1_prog:', type(bx1_prog[0]))
        for stmt in bx1_prog:
            # print('stmt_pt', stmt)
            stmt_ast = build_stmt_ast(stmt)
            # print('stmt_ast', stmt_ast)
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
                
                
                
                
                
            