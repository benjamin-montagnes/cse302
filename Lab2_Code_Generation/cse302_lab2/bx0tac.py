#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: benjaminmontagnes and antoninwattel

"""

from scanner import load_source, lexer
from bx0_parser import parser
# from bx0_parser import Node

import sys, tac


def main():
    for filename in sys.argv[1:]:
        print(f'[[ processing {filename} ]]')
        load_source(filename)
        
        statements = parser.parse(lexer=lexer)
        # print(statements, sep='\n')
        
        tmm = TMM()
        # tmm.tmm_expr(Node('binop', '+', Node('var', 'x'), Node('num', 42)), '%2')
        # tmm.tmm_stmt(Node('assign', 'y', Node('binop', '*', Node('num', 2), Node('var', 'x'))))
        
        fname = filename.split('.')[0] + '.tac'
        f = open(fname,"w+")
        
        for stat in statements: tmm.tmm_stmt(stat)
        tmm.copy_prop()
        tmm.dead_copy()
        
        for item in tmm.instrs: f.write("%s\n" % item)
        f.close()
        
        # print(*tmm.instrs, sep= '\n')
    
class TMM:
    def __init__(self):
        self.instrs = [] # the TAC instructions
        self.temp_map = dict()
        self.last_temp = -1
        self.binop_map = {'+': 'add', 
                          '-': 'sub', 
                          '*': 'mul', 
                          '/': 'div', 
                          '%': 'mod', 
                          '&': 'and', 
                          '|': 'or', 
                          '^': 'xor', 
                          '<<': 'shl', 
                          '>>': 'shr'
                          }
        self.unop_map = {'-': 'neg', 
                         '~': 'not'
                         }
    
    def emit(self, instr):
        """Add ‘instr’ to the end of the sequence of instructions produced by
        the code generator."""
        self.instrs.append(instr)
    
    def tmm_expr(self, expr, t_dest):
        """Process the given ‘expr’ so that in the generated instruction(s) 
        the result of the computation is placed in the TAC temporary ‘t_dest’.
        """
        if expr.opcode == 'num':
            self.emit(tac.Instr(t_dest, 'const', expr.value, None))
        elif expr.opcode == 'var':
            # get TAC temporary corresponding to the variable
            # t_source = self.temp_map[expr.value]
            t_source = self.get_temp_for(expr.value)
            self.emit(tac.Instr(t_dest, 'copy', t_source, None))
        elif expr.opcode == 'binop': 
            t_arg1 = self.fresh_temp() 
            self.tmm_expr(expr.kids[0], t_arg1)
            t_arg2 = self.fresh_temp() 
            self.tmm_expr(expr.kids[1], t_arg2)
            self.emit(tac.Instr(t_dest,self.binop_map[expr.value],t_arg1,t_arg2))
        elif expr.opcode == 'unop': 
            t_arg = self.fresh_temp() 
            self.tmm_expr(expr.kids[0], t_arg)
            self.emit(tac.Instr(t_dest,self.unop_map[expr.value],t_arg, None))
        else:
            print(f'Unknown BXO <expr> opcode: {expr.opcode}') 
            raise RuntimeError
    
    def fresh_temp(self):
        self.last_temp += 1
        return '%' + str(self.last_temp)
    
    def get_temp_for(self, var):
        # print("var:",var)
        if var not in self.temp_map:
            self.temp_map[var] = self.fresh_temp() 
        return self.temp_map[var]
    
    def tmm_stmt(self, stmt):
        if stmt.opcode == 'print':
            t_dest = self.fresh_temp() 
            self.tmm_expr(stmt.kids[0], t_dest) 
            self.emit(tac.Instr(None, 'print', t_dest, None))
        elif stmt.opcode == 'assign':
            t_dest = self.get_temp_for(stmt.value) 
            # print("value:",stmt.value)
            self.tmm_expr(stmt.kids[0], t_dest)
        else:
            print(f'Unknown BXO <stmt> opcode: {stmt.opcode}') 
            raise RuntimeError
            
    def copy_prop(self):
        for i in range(len(self.instrs)):
            if self.instrs[i].opcode!= 'copy': continue
            t_old = self.instrs[i].arg1
            t_new = self.instrs[i].dest
            for j in range(i+1, len(self.instrs)):
                if self.instrs[j].arg1 == t_new:
                    self.instrs[j].arg1 = t_old
                if self.instrs[j].arg2 == t_new:
                    self.instrs[j].arg2 = t_old
                if self.instrs[j].dest in (t_old, t_new):
                    break
                
    def dead_copy(self):
        for i in range(len(self.instrs)):
            if self.instrs[i].opcode == 'copy':
                num,found=self.instrs[i].dest,False
                for j in range(i+1, len(self.instrs)):
                    if self.instrs[j].arg1==num or self.instrs[j].arg2==num:
                        found = True
                        break
                if not found : self.instrs[i] = 'nop'
        self.instrs=filter(lambda x : x != 'nop', self.instrs)
                    


if __name__ == '__main__':
    main()
    