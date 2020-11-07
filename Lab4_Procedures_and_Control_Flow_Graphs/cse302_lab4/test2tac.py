#!/usr/bin/env python3

#tac generator from the typed ast
import ast
#import tac
from tac import Instr, execute

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

class Munch: #TO DO -> UPDATE EVERYTHING WITH THE PROC
    def __init__(self, prog):#, prog):
        
        self._varmap = dict() #still useful ???
        self._temp_count = -1
        self._label_count = -1
        self._instrs = [] #TO REMOVE ?
        self._saved_prog = prog
        self._procmap = dict() #key: <proc_name>, value: (keytac.Proc, [list of instrs (body)]), USELESS TO HAVE A MAP IN FACT
        self._globvarmap = dict() #key: "@<varname>", value: "<value>"
        
        self.munch_prog(prog) #how to deal with that ?
        #?
        
        

    def ship(self):
        return self._instrs

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

    def munch_prog(self, prog): #THIS IS PROBABLY USELESS NOW..
        
        for decl in prog.thn: #things
            self.munch_decl(decl)
        #self._loop_exits = []
        #self.lab_enter = self._fresh_label()
        #self.lab_return = self._fresh_label()
        #self._emit(Instr(None, 'label', self.lab_enter, None), proc)
        #self.munch_block(prog)
        #self._emit(Instr(None, 'label', self.lab_return, None), proc)

    def munch_block(self, stmts, proc): #sould be ok ?
        for stmt in stmts.body:
            self.munch_stmt(stmt, proc)

    def munch_stmt(self, stmt, proc): #update: not yet tested #ADD PROC AS ARGUMENT ??
        if isinstance(stmt, ast.Assign):
            t_dest = self._lookup(stmt.var)
            self.munch_expr( stmt.value, t_dest, proc)
            
            # t_rhs = self.bmm_int_expr(stmt.expr)#may be wrong - > not necessarily an int
            # self._emit(Instr(self._lookup(stmt.var.name), 'copy', t_rhs, None), proc)
        elif isinstance(stmt, ast.Block):
            self.munch_block(stmt.body)
        elif isinstance(stmt, ast.IfElse): #?
            lab_true = self._fresh_label()
            lab_false = self._fresh_label()
            lab_end = self._fresh_label()
            c = self._fresh_temp()
            self.munch_bool_expr(stmt.cond, c, lab_true, lab_false, proc)
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
            self._emit(Instr(None, 'label', lab_header, None), proc)
            self.munch_bool_expr(stmt.cond, lab_body, lab_end)
            self._emit(Instr(None, 'label', lab_body, None), proc)
            self._loop_exits.append((lab_end, lab_header))
            self.munch_stmt(stmt.body)
            self._loop_exits.pop()
            self._emit(Instr(None, 'jmp', lab_header, None), proc)
            self._emit(Instr(None, 'label', lab_end, None), proc)
        #BX2
        #VERIFY AND UPDATE
        #verify the old ifs
        #elif isinstance(stmt, ast.LocalVardecl):
        elif isinstance(stmt, ast.VarDecl):
        #for varinit in stmt.varinits: #sould we have several or just one ???
            for varinit in stmt.names:
                self.munch_stmt(ast.Assign(varinit[0], varinit[1]), proc) #name, value
        #    self.munch_stmt(ast.Assign(stmt.init.name, stmt.init.value), proc)
        elif isinstance(stmt, ast.Eval):
            t_dest = "%_"
            self.munch_expr(stmt.arg, t_dest, proc)
        elif isinstance(stmt, ast.Return): #PROBLEM TO FIXXXX
            t_ret = self._fresh_temp() #WTF ?
            self.munch_expr(stmt.value, proc) #how do we deal with that ?
            self._emit(Instr(None, "ret", t_ret, None), proc)
            
        else:
            raise RuntimeError(f'munch_stmt() cannot handle: {stmt.__class__}')
            

    def munch_expr(self, expr, dest, proc): #TO REWRITE... NOT GOOD
        
        if isinstance(expr, ast.Variable):#not sure about this one..
            temp = self._lookup(expr.name)
            self._emit(Instr(dest, 'copy', temp, None), proc)
            
        if isinstance(expr, ast.Call):
            for i in range(len(expr.args)):
                temp = self._fresh_temp()
                self.munch_expr(expr.args[i], temp, proc)
                self._emit(Instr(None, "param", i+1, temp), proc) #UPDATE EMIT
            self._emit(Instr(dest, "call", f'@{expr.name}', len(expr.args)), proc)
            
        #elif expr._ty is ast.Type.INT: self.bmm_int_expr(expr, dest, proc)
        ##########
        elif isinstance(expr, ast.Boolean):#not sure
             #self._emit(Instr(None, 'jmp', ltrue if expr.value else lfalse, None), proc)
             if expr.value : self.emit(proc, Instr(dest, 'const', 1, None))
             else: self.emit(proc, Instr(dest, 'const', 0, None))
        
        elif isinstance(expr, ast.Number):
            #t_result = self._fresh_temp()
            #self._emit(Instr(t_result, 'const', expr.value, None), proc)
            self._emit(Instr(dest, 'const', expr.value, None), proc)
            #return t_result#??
            return dest
        
        elif isinstance(expr, ast.Appl):
            #BOOL---------------------
            ltrue = self._fresh_label()
            lfalse = self._fresh_label()
            if expr.func in relop_code:
                (opcode, left, right) = relop_code[expr.func](expr.args[0], expr.args[1])
                #t_left = self.bmm_int_expr(left, dest, proc)
                #t_right = self.bmm_int_expr(right, dest, proc)
                t_left = self.munch_expr(left, dest, proc)
                t_right = self.munch_expr(right, dest, proc)
                #t_result = self._fresh_temp()
                #self._emit(Instr(t_result, 'sub', t_left, t_right), proc)
                self._emit(Instr(dest, 'sub', t_left, t_right), proc)
                self._emit(Instr(None, opcode, dest, ltrue), proc)
                self._emit(Instr(None, 'jmp', lfalse, None), proc)
            elif expr.func == '!':
                self.munch_bool_expr(expr.args[0], lfalse, ltrue, proc)
            elif expr.func == '&&':
                li = self._fresh_label()
                self.munch_bool_expr(expr.args[0], li, lfalse, proc)
                self._emit(Instr(None, 'label', li, None), proc)
                self.munch_bool_expr(expr.args[1], ltrue, lfalse, proc)
            elif expr.func == '||':
                li = self._fresh_label()
                self.munch_bool_expr(expr.args[0], ltrue, li, proc)
                self._emit(Instr(None, 'label', li, None), proc)
                self.munch_bool_expr(expr.args[1], ltrue, lfalse, proc)
            #NUMBER------------------
            if expr.func in binop_code:
                t_left = self.bmm_int_expr(expr.args[0],dest, proc)
                t_right = self.bmm_int_expr(expr.args[1],dest, proc)
                t_result = self._fresh_temp()
                #self._emit(Instr(t_result, binop_code[expr.func], t_left, t_right), proc)
                if t_left and t_right:
                    self._emit(Instr(t_result, binop_code[expr.func], t_left, t_right), proc)
                # return t_result
                return t_result
            elif expr.func in unop_code:
                t_left = self.bmm_int_expr(expr.args[0], proc)
                t_result = self._fresh_temp()
                #self._emit(Instr(t_result, unop_code[expr.func], t_left, None))
                #return t_result
                self._emit(Instr(t_result, unop_code[expr.func], t_left, None), proc)
                return t_result
        
        # elif expr._ty is ast.Type.BOOL: 
        #     if isinstance(expr, ast.Boolean):#not sure
        #         if expr.value: self.emit(proc, Instr(dest, 'const', 1, None), proc)
        #         else: self.emit(Instr(dest, 'const', 0, None), proc)
        #     else:
        #         ltrue = self._fresh_label()
        #         lfalse = self._fresh_label()
        #         self.munch_bool_expr(expr, dest,ltrue, lfalse, proc)#probably wrong
        

    def munch_bool_expr(self, expr, dest, ltrue, lfalse, proc): #USELESS NOW ?
        # if expr.ty is not ast.Type.BOOL:
        #     raise RuntimeError(f'munch_bool_expr(): expecting {ast.BOOL}, got {expr.ty}')
           
        # if isinstance(expr, ast.Boolean):#not sure
        #     if expr.value: self.emit(proc, Instr(dest, 'const', 1, None), proc)
        #     else: self.emit(Instr(dest, 'const', 0, None), proc)
                
        #BEFORE ??
        if isinstance(expr, ast.Boolean):#not sure
             #self._emit(Instr(None, 'jmp', ltrue if expr.value else lfalse, None), proc)
             if expr.value : self.emit(proc, Instr(dest, 'const', 1, None))
             else: self.emit(proc, Instr(dest, 'const', 0, None))
            
        elif isinstance(expr, ast.Appl):
            if expr.func in relop_code:
                (opcode, left, right) = relop_code[expr.func](expr.args[0], expr.args[1])
                #t_left = self.bmm_int_expr(left, dest, proc)
                #t_right = self.bmm_int_expr(right, dest, proc)
                t_left = self.munch_expr(left, dest, proc)
                t_right = self.munch_expr(right, dest, proc)
                #t_result = self._fresh_temp()
                #self._emit(Instr(t_result, 'sub', t_left, t_right), proc)
                self._emit(Instr(dest, 'sub', t_left, t_right), proc)
                self._emit(Instr(None, opcode, dest, ltrue), proc)
                self._emit(Instr(None, 'jmp', lfalse, None), proc)
            elif expr.func == '!':
                self.munch_bool_expr(expr.args[0], lfalse, ltrue, proc)
            elif expr.func == '&&':
                li = self._fresh_label()
                self.munch_bool_expr(expr.args[0], li, lfalse, proc)
                self._emit(Instr(None, 'label', li, None), proc)
                self.munch_bool_expr(expr.args[1], ltrue, lfalse, proc)
            elif expr.func == '||':
                li = self._fresh_label()
                self.munch_bool_expr(expr.args[0], ltrue, li, proc)
                self._emit(Instr(None, 'label', li, None), proc)
                self.munch_bool_expr(expr.args[1], ltrue, lfalse, proc)
            else:
                raise RuntimeError(f'munch_bool_expr(): unknown operator {expr.func}')
        else:
            raise RuntimeError(f'munch_bool_expr(): unknown boolean expression {expr.__class__}')

    def bmm_int_expr(self, expr, dest, proc): #why returns ??
        
        #useless now
        # if expr.ty is not ast.INT:
        #     raise RuntimeError(f'bmm_int_expr(): expecting {ast.INT}, got {expr.ty}')
        # if isinstance(expr, ast.Variable):
        #     return self._lookup(expr.name)
        if isinstance(expr, ast.Number):
            #t_result = self._fresh_temp()
            #self._emit(Instr(t_result, 'const', expr.value, None), proc)
            self._emit(Instr(dest, 'const', expr.value, None), proc)
            #return t_result#??
            return dest
        elif isinstance(expr, ast.Appl):
            if expr.func in binop_code:
                t_left = self.bmm_int_expr(expr.args[0],dest, proc)
                t_right = self.bmm_int_expr(expr.args[1],dest, proc)
                t_result = self._fresh_temp()
                #self._emit(Instr(t_result, binop_code[expr.func], t_left, t_right), proc)
                self._emit(Instr(t_result, binop_code[expr.func], t_left, t_right), proc)
                # return t_result
                return t_result
            elif expr.func in unop_code:
                t_left = self.bmm_int_expr(expr.args[0],dest, proc)
                t_result = self._fresh_temp()
                #self._emit(Instr(t_result, unop_code[expr.func], t_left, None))
                #return t_result
                self._emit(Instr(t_result, unop_code[expr.func], t_left, None), proc)
                return t_result
            else:
                raise RuntimeError(f'bmm_int_expr(): unknown operator {expr.func}')
        elif isinstance(expr, ast.Variable):
            temp = self._lookup(expr.name)
            self._emit(Instr(dest, 'copy', temp, None), proc)
        else:
            raise RuntimeError(f'Unknown expr kind: {expr.__class__}')

    def munch_decl(self, decl): 
        """globvardecl and procdecl"""
        #if isinstance(decl, ast.GlobalVardecl):
        if isinstance(decl, ast.VarDecl):
            self.add_globvar(decl)#change the name of this
        elif isinstance(decl, ast.Proc):
            self.munch_proc(decl)

    
    def add_globvar(self, decl):#no need to munch ???
        for globvar in decl.init: #there might be a problem here !!!
            if globvar.value == "true":
                self._globvarmap[f'@{globvar.name}'] = 1 #do we add the '@' ? #should 1 be a string ?
            elif globvar.value == "false":
                self._globvarmap[f'@{globvar.name}'] = 0
            else:
                self._globvarmap[f'@{globvar.name}'] = globvar.value
    
    def munch_proc(self, decl):
        params = []
        for param in decl.params:
            params += [f'%{p}' for p in param.paramvars]
        
        #self._procmap[decl.name] =  ast.Proc(f'@{decl.name}', params, [], decl.block)
        self._procmap[decl.name] =  (decl, [])
        
        
        #WTF 
        # for param in params:
        #     self._varmap[param] = ''
        #     #self.temps[-1][var] = f'%{var}' #wtf ?
        self.munch_block(decl.body, decl.name)
        
        #if self._procmap[decl.name].body.stmts == [] or not isinstance(self._procmap[decl.name].body.stmts[-1], ast.Return):
        #if self._procmap[decl.name].block.stmts == [] or not isinstance(self._procmap[decl.name].block.stmts[-1], ast.Return):
        if self._procmap[decl.name][0].body.body == []: #or not isinstance(self._procmap[decl.name][0].body.stmts[-1], ast.Return):
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
        bx2_parser.lexer.load_source(bx_file)
        #prog = ast.Block(*bx2_parser.parser.parse(lexer=bx2_parser.lexer))
        prog = bx2_parser.parser.parse(lexer=bx2_parser.lexer)
        print(prog)
        #prog.type_check() #should it be [{}] ?
        done=False
        munched = Munch(prog)
        
        #while not done :
           # decl = prog.decl
           # munch.munch_decl(decl)
           # if prog.prog == None:
            #    done = True
            #else:
              #  prog = prog.prog
                
        tac_prog = munched.ship()
        if interpret:
            execute(tac_prog, show_instr=(verbosity>0), only_decimal=(verbosity<=1))
        else:
            tac_file = bx_file[:-3] + '.tac'
            with open(tac_file, 'w') as f:
                #write the global variables
                for globvar_name, globvar_value in munched._globvarmap:
                    f.write(f'var {globvar_name} = {globvar_value};\n')
                
                #write the procedures
                for p in munched._procmap.values():
                    proc, proc_instrs = p
                    f.write(f'proc {proc.name}({proc.params}): \n')
                    for instr in proc_instrs:
                        print(instr, file=f)
                    
                    #f.write(str(munched._procmap[proc][0])+'\n')
                    
                #for instr in tac_prog:
                    #print(instr, file=f)
            if verbosity > 0:
                print(f'{bx_file} -> {tac_file} done')
