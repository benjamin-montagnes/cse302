#!/usr/bin/env python3

#tac generator from the typed ast
import ast
#import tac
from tac import Instr, execute
from context import context

#TO DO -> VERBOSITY

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
    'u-': 'neg',
    '~': 'not',
}
relop_code = {
    '==': (lambda l, r: ('jz', l, r)),
    '!=': (lambda l, r: ('jnz', l, r)),
    '<':  (lambda l, r: ('jl', l, r)),
    '<=': (lambda l, r: ('jle', l, r)),
    '>':  (lambda l, r: ('jl', r, l)),
    '>=': (lambda l, r: ('jle', r, l)),
}

class Munch: 
    def __init__(self, prog):
        
        self._varmap = dict() 
        self._temp_count = -1
        self._label_count = -1
        self._saved_prog = prog
        self._procmap = dict() #key: <proc_name>, value: (keytac.Proc, [list of instrs (body)])
        #(actually we could just have a list..)
        self._globvarmap = dict() #key: "@<varname>", value: "<value>"
        
        self.munch_prog(prog) 
        

    def _emit(self, instr, proc):
        #self._instrs.append(instr)
        #._procmap[proc].body.append(instr)
        self._procmap[proc][1].append(instr)
        #self._procmap[proc].block.stmts.append(instr) #NOT GOOD BUT MIGHT WORK

    def _fresh_temp(self):
        """Allocate and return a fresh temporary"""
        self._temp_count += 1
        return '%' + str(self._temp_count)

    def _fresh_label(self):
        """Allocate and return a fresh label"""
        self._label_count += 1
        return '.L' + str(self._label_count)

    def _lookup(self, var):
        """Lookup the temporary mapped to `var', allocating if necessary"""
        if var not in self._varmap:
            self._varmap[var] = self._fresh_temp()
        return self._varmap[var]

    def munch_prog(self, prog): 
        
        self._loop_exits = []
        self.lab_enter = self._fresh_label()
        self.lab_return = self._fresh_label()
        #self._emit(Instr(None, 'label', self.lab_enter, None), proc)
        #self.munch_block(prog)
        for decl in prog.thn: #things
            self.munch_decl(decl)
        #self._emit(Instr(None, 'label', self.lab_return, None), proc)

    def munch_block(self, block, proc): 
        for stmt in block.body:
            self.munch_stmt(stmt, proc)

    def munch_stmt(self, stmt, proc): 
        if isinstance(stmt, ast.Assign):
            t_dest = self._lookup(stmt.var)
            self.munch_expr(stmt.var, t_dest, proc)
            # t_rhs = self.bmm_int_expr(stmt.expr)#may be wrong - > not necessarily an int
            # self._emit(Instr(self._lookup(stmt.var.name), 'copy', t_rhs, None), proc)
        elif isinstance(stmt, ast.Block):
            self.munch_block(stmt, proc)
        elif isinstance(stmt, ast.IfElse):
            lab_true = self._fresh_label()
            lab_false = self._fresh_label()#useless
            lab_end = self._fresh_label()
            c = self._fresh_temp()
            self.munch_expr(stmt.cond, c, proc)
            self._emit(Instr(None, 'label', lab_false, None), proc)
            self.munch_stmt(stmt.els, proc)
            self._emit(Instr(None, 'jmp', lab_end, None), proc)
            self._emit(Instr(None, 'label', lab_true, None), proc)
            self.munch_stmt(stmt.thn, proc)
            self._emit(Instr(None, 'label', lab_end, None), proc)
        elif isinstance(stmt, ast.Break):
            if len(self._loop_exits) == 0:
                raise RuntimeError(f'Cannot break here; not in a loop')
            self._emit(Instr(None, 'jmp', self._loop_exits[-1][0], None), proc)
        elif isinstance(stmt, ast.Continue):
            if len(self._loop_exits) == 0:
                raise RuntimeError(f'Cannot continue here; not in a loop')
            self._emit(Instr(None, 'jmp', self._loop_exits[-1][1], None),  proc)
        elif isinstance(stmt, ast.While):
            lab_header = self._fresh_label()
            lab_body = self._fresh_label()
            lab_end = self._fresh_label()
            t = self._fresh_temp()
            self._emit(Instr(None, 'label', lab_header, None), proc)
            self.munch_expr(stmt.cond, t, proc)
            self._emit(Instr(None, 'label', lab_body, None), proc)
            self._loop_exits.append((lab_end, lab_header))
            self.munch_stmt(stmt.body, proc)
            self._loop_exits.pop()
            self._emit(Instr(None, 'jmp', lab_header, None), proc)
            self._emit(Instr(None, 'label', lab_end, None), proc)
        #BX2
        elif isinstance(stmt, ast.VarDecl):
            for varinit in stmt.names:
                self.munch_stmt(ast.Assign(varinit[0], varinit[1]), proc) #name, value
        elif isinstance(stmt, ast.Eval):
            t_dest = "%_"
            self.munch_expr(stmt.arg, t_dest, proc)
        elif isinstance(stmt, ast.Return): #TO FIX
            t_ret = self._fresh_temp() 
            self.munch_expr(stmt.value, proc) 
            self._emit(Instr(None, "ret", t_ret, None), proc)
            
        else:
            raise RuntimeError(f'munch_stmt() cannot handle: {stmt.__class__}')
            

    def munch_expr(self, expr, dest, proc): #TO REWRITE... NOT GOOD
        
        if isinstance(expr, ast.Variable):#not sure about this one..
            #print('ast.Variable---------')
            temp = self._lookup(expr.name)
            self._emit(Instr(dest, 'copy', temp, None), proc)
            
        if isinstance(expr, ast.Call):
            #print('ast.call---------')
            for i in range(len(expr.args)):
                temp = self._fresh_temp()
                self.munch_expr(expr.args[i], temp, proc)
                self._emit(Instr(None, "param", i+1, temp), proc) #UPDATE EMIT
            self._emit(Instr(dest, "call", f'@{expr.name}', len(expr.args)), proc)
        elif isinstance(expr, ast.Boolean):
             #print('ast.boolean---------')
             if expr.value : self._emit(Instr(dest, 'const', 1, None),proc)
             else: self._emit(Instr(dest, 'const', 0, None),proc)
        
        elif isinstance(expr, ast.Number):
            #print('ast.number---------')
            self._emit(Instr(dest, 'const', expr.value, None), proc)
            return dest
        
        elif isinstance(expr, ast.Appl):
            #print("ast.APPL -------------")
            #BOOL---------------------
            ltrue = self._fresh_label()
            lfalse = self._fresh_label()
            if expr.func in relop_code:
               # print("relop")
                t1 = self._fresh_temp()
                self.munch_expr(expr.args[0],t1, proc)
                t2 = self._fresh_temp()
                #print('exprargs1', type(expr.args[1]))
                self.munch_expr(expr.args[1], t2, proc)
                Lt = self._fresh_label()
                Lp = self._fresh_label()
                self._emit(Instr( t1, 'sub', t1, t2), proc)
                (opcode, left, right) = relop_code[expr.func](expr.args[0], expr.args[1])
                self._emit(Instr(None, opcode, t1, Lt), proc)
                self._emit(Instr(dest, 'const', 0, None), proc) #FIX THE PROBLEM HERE !!!
                self._emit(Instr(None, 'jmp', Lp, None), proc)
                self._emit(Instr(None, 'label', Lt, None), proc)
                self._emit(Instr(dest, 'const', 1, None), proc)
                self._emit(Instr(None, 'label', Lp, None), proc)
                
            elif expr.func == '!':
                #print("! operator")
                t_1 = self.new_temp()
                t_2 = self._fresh_temp()
                self.munch_expr(expr.args[0], t_1, proc)
                self.emit(proc, Instr(t_1, "const", 1, None))
                self.emit(proc, Instr(dest, "xor", t_2, t_1))
            elif expr.func == '&&':
                #print("&&")
                li = self._fresh_label()
                self.munch_expr(expr.args[0], li, lfalse, proc)
                self._emit(Instr(None, 'label', li, None), proc)
                self.munch_expr(expr.args[1], ltrue, lfalse, proc)
            elif expr.func == '||':
                #print("||")
                li = self._fresh_label()
                self.munch_expr(expr.args[0], ltrue, li, proc)
                self._emit(Instr(None, 'label', li, None), proc)
                self.munch_expr(expr.args[1], ltrue, lfalse, proc)
            #NUMBER------------------
            if expr.func in binop_code:
                #print("binop")
                tl = self._fresh_temp()
                tr = self._fresh_temp()
                self.munch_expr(expr.args[0],tl, proc)
                self.munch_expr(expr.args[1],tr, proc)
                self._emit(Instr(dest, binop_code[expr.func],tl,tr), proc)
            elif expr.func in unop_code:
                #print("unnop")
                t_left = self.munch_expr(expr.args[0], proc)
                t_result = self._fresh_temp()
                self._emit(Instr(t_result, unop_code[expr.func], t_left, None), proc)
        


    def munch_decl(self, decl): 
        """globvardecl and procdecl"""
        #if isinstance(decl, ast.GlobalVardecl):
        if isinstance(decl, ast.VarDecl):
            self.add_globvar(decl)#change the name of this
        elif isinstance(decl, ast.Proc):
            self.munch_proc(decl)

    
    def add_globvar(self, decl):
        for globvar in decl.init: 
            if globvar.value == "true":
                self._globvarmap[f'@{globvar.name}'] = 1 
            elif globvar.value == "false":
                self._globvarmap[f'@{globvar.name}'] = 0
            else:
                self._globvarmap[f'@{globvar.name}'] = globvar.value
    
    def munch_proc(self, decl): #vey messy . does not work as it should
        self._procmap[decl.name] =  (decl, [])
        self.munch_block(decl.body, decl.name)
        if self._procmap[decl.name][0].body.body == [] or isinstance(self._procmap[decl.name][0].body.body[-1], ast.Return):
            self._emit(Instr(None, "ret", "%_", None), decl.name)
        
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys, getopt, time, random, bx2_parser
    opts, bx_files = getopt.getopt(sys.argv[1:], 'hvi', [])
    verbosity = 0
    interpret = False
    for opt, val in opts:
        if opt == '-h':
            print(f'''\
USAGE: {sys.argv[0]} OPTIONS file.bx ...

Where OPTIONS is one of

  -v          Increase verbosity (can be used multiple times)
  -i          Run the TAC interpreter instead of writing TAC files
  -h          Print this help message''')
            exit(0)
        elif opt == '-v':
            verbosity += 1
        elif opt == '-i':
            interpret = True
        else:
            print(f'Unknown option {opt}')
            exit(1)
    for bx_file in bx_files:
        if not bx_file.endswith('.bx'):
            print(f'File name {bx_file} does not end in ".bx"')
            exit(1)
        bx2_parser.load_source(bx_file)
        prog = bx2_parser.parser.parse(lexer=bx2_parser.lexer)
        print(prog)
        #type check
        prog.type_check_global()
        #context._str_(context.first_scope)
        prog.type_check()
        if verbosity > 0: print('type check OK \n')
        
        munched = Munch(prog)
        #if interpret:
        #    execute(...)
        
        tac_file = bx_file[:-3] + '.tac'
        with open(tac_file, 'w') as f:
            #write the global variables
            for globvar_name, globvar_value in munched._globvarmap:
                f.write(f'var {globvar_name} = {globvar_value};\n')
            
            #write the procedures
            for p in munched._procmap.values():
                proc, proc_instrs = p
                #not really how params should be read..
                params = ''
                for i in range(len(proc.params)):
                    params += str(proc.params[i])
                    if i!=(len(proc.params)-1): params += ', '
                    
                f.write(f'proc @{proc.name}({proc.params}): \n')
                for instr in proc_instrs:
                    print(instr, file=f)
                
                #f.write(str(munched._procmap[proc][0])+'\n')
                
        if verbosity > 0:
            print(f'{bx_file} -> {tac_file} done')
