#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: benjaminmontagnes and antoninwattel

"""

import sys, tac


def main():
    for filename in sys.argv[1:]:
        print(f'[[ processing {filename} ]]')
        prgrm = tac.load_tac(filename)
            
        tac_to_ass = TTA()
        tac_to_ass.tac_prgm_to_x64(prgrm)
        

        fname = filename.split('.')[0] + '.s'
        f = open(fname,"w+")
        f.write("\t.globl main\n\t.text\nmain:\n\tpushq %rbp\n\tsubq $56, %rsp\n")
        for instr in tac_to_ass.instrs: 
            print(instr)
            if instr.arg2 and instr.arg1: f.write("\t{} {}, {}\n".format(instr.opcode,instr.arg1, instr.arg2))
            elif instr.arg1 : f.write("\t{} {}\n".format(instr.opcode,instr.arg1))
            else: f.write("{}:\n".format(instr.opcode))
        
        #Instructions to restore RSP,RBP and set return code to 0 and exit: 
        f.write("\tmovq %rbp, %rsp\n\tpopq %rbp\n\tmovq $0, %rax\n\tretq")
        f.close()

class Instr_x64:
    __slots__ = ('opcode', 'arg1', 'arg2')
    def __init__(self, opcode, arg1, arg2):
        """Create a new TAC instruction with given `opcode' (must be non-None).
        The other three arguments, `dest', 'arg1', and 'arg2' depend on what
        the opcode is."""
        self.opcode = opcode
        self.arg1 = arg1
        self.arg2 = arg2

    def __repr__(self):
        result = ''
        #if self.dest != None: result += f'(set {self.dest} '
        result += '(' + self.opcode
        if self.arg1 != None: result += f' {self.arg1}'
        if self.arg2 != None: result += f' {self.arg2}'
        result += ')'       
        return result
                    
class TTA:
    def __init__(self):
        self.instrs = [] # the assembly instructions
        self.stack_slot_map = []
        self.last_temp = -1
        self.binop_map = {'add': 'addq', 
                          'sub': 'subq', 
                          'mul': 'imulq',
                          'and': 'andq', 
                          'or': 'orq', 
                          'xor': 'xorq', 
                          }
        self.unop_map = {'neg': 'negq', 
                         'not': 'notq'
                         }
        self.jcc = ['jz','jnz','jl','jle']
        
    def emit(self, instr):
        """Add ‘instr’ to the end of the sequence of instructions produced by
        the code generator."""
        self.instrs.append(instr)
    
    def get_stack_slot(self, temp):
        if temp not in self.stack_slot_map: self.stack_slot_map.append(temp)
        return "-{}(%rbp)".format(str((self.stack_slot_map.index(temp) + 1) * 8)) # nth temporary will be located at RBP - 8n
    
    def tac_expr_to_x64(self, instr):
        if instr.opcode == 'const':
            register = self.get_stack_slot(instr.dest)
            self.emit(Instr_x64("movq","${}".format(str(instr.arg1)), register))
        elif instr.opcode == 'copy':
            register = self.get_stack_slot(instr.dest)
            register_1 = self.get_stack_slot(instr.arg1)
            self.emit(Instr_x64("movq", register_1, "%rax"))
            self.emit(Instr_x64("movq", "%rax", "%rcx"))
            self.emit(Instr_x64("movq", "%rcx", register))
        
        elif instr.opcode in self.binop_map:
            register = self.get_stack_slot(instr.dest)
            register_2 = self.get_stack_slot(instr.arg2)
            self.emit(Instr_x64("movq", register_2, "%rcx"))
            register_1 = self.get_stack_slot(instr.arg1)
            self.emit(Instr_x64("movq", register_1, "%rax"))
            self.emit(Instr_x64(self.binop_map[instr.opcode], "%rax", "%rcx"))
            self.emit(Instr_x64("movq", "%rcx", register))

        elif instr.opcode in self.unop_map:
            register = self.get_stack_slot(instr.dest)
            register_1 = self.get_stack_slot(instr.arg2)
            self.emit(Instr_x64("movq", register_1, "%rax"))
            self.emit(Instr_x64(self.unop_map[instr.opcode ],"%rax", None))
            self.emit(Instr_x64("movq", "%rcx", register))
            
        elif instr.opcode == 'jmp':
            self.emit(Instr_x64('jmp', instr.arg1, None))
            
        elif instr.opcode == 'label':
            self.emit(Instr_x64(instr.arg1, None, None))
            
        elif instr.opcode in self.jcc:
            self.emit(Instr_x64('cmpq', '$0', instr.arg1))
            self.emit(Instr_x64(instr.opcode, instr.arg2, None))
            
        # elif instr.opcode == 'shr' || instr.opcode == 'shl':
        # elif instr.opcode == 'nop':
            
        elif instr.opcode == 'div' or instr.opcode == 'mod':
            register = self.get_stack_slot(instr.dest)
            register_2 = self.get_stack_slot(instr.arg2)
            self.emit(Instr_x64("movq", register_2, "%rcx"))
            register_1 = self.get_stack_slot(instr.arg1)
            self.emit(Instr_x64("movq", register_1, "%rax"))
            self.emit(Instr_x64('idivq', ))
            if instr.opcode == 'div': self.emit(Instr_x64("movq", "%rax", register))
            else: self.emit(Instr_x64("movq", "%rdx", register))
                
            
        elif instr.opcode == 'print':
            self.emit(Instr_x64('pushq', '%rdi', None))
            self.emit(Instr_x64('movq', self.get_stack_slot(instr.arg1) , '%rdi' ))
            self.emit(Instr_x64('callq', 'bx_print_int', None))
            self.emit(Instr_x64('popq', '%rdi', None))
            
            
        
    def tac_prgm_to_x64(self, prgm):
        # self.emit(Instr_x64('subq',"${}".format(len(self.stack_slot_map)*8), "$rsp"))
        for instr in prgm: self.tac_expr_to_x64(instr)
        


if __name__ == '__main__':
    main()






































