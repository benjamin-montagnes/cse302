#!/usr/bin/env python3

"""
Instruction selection: from TAC to X64
"""

from x64 import *
import tac, subprocess, sys

jcc_map = { 'jz': JZ, 'jnz': JNZ, 'jl': JL, 'jle': JLE }
simple_binop = { 'add': ADD, 'sub': SUB, 'mul': IMUL, 'and': AND, 'or': OR,
                 'xor': XOR }
simple_unop = { 'neg': NEG, 'not': NOT }

# header = ['.globl main','.text','main:','pushq %rbp','movq %rsp, %rbp',]
# footer = ['movq %rbp, %rsp', 'popq %rbp', 'xorq %rax, %rax', 'retq']

class Isel:
    """Instruction selection"""

    def __init__(self):
        """Generate instructions for `prog', a list of tac.Instr instructions"""
        self.stack = dict()
        self.results = []
        self.stnum,self.paramnum = 0,0

    def get(self, temp, proc):
        if temp not in self.stack[proc]:
            self.stack[proc][temp] = -8*(len(self.stack[proc]) + 1)
        return (self.stack[proc][temp],'%rbp')

    def proc(self, prog):
        for decl in prog:
            # print('DECLLLL:',str(decl))
            decl.name = decl.name[1:]
            self.stack[decl.name] = {}
            header=[
                MISC(f'.globl {decl.name}'),
                MISC(".text"),
                LABEL(f'{decl.name}'),
                PUSH("%rbp"),
                MOV("%rsp", "%rbp"),
            ]
            footer = [
                MOV("%rbp", "%rsp"),
                POP("%rbp"),
                XOR("%rax", "%rax"),
                RET
            ]
            reg = ['%rdi','%rsi','%rdx','%rcx','%r8','%r9']
            self.results = header + self.results
            self.stnum = len(self.results) - 1
            for i in range(len(decl.t_args)):
                if i<6: self.results.append(MOV(reg[i], self.get(decl.t_args[i], decl.name)))
                else: self.stack[decl.name][decl.t_args[i]] = str(16 + 8*(i - 6)) + "(%rbp)"
            for expr in decl.body: self.results += self._process(expr, decl.name)
            self.results[self.stnum] = SUB(8*len(self.stack[decl.name]), "%rsp")
            self.results += footer

    def _process(self, tin, proc):
        body = []
        if tin.opcode == 'nop':
            body.append(NOP)

        elif tin.opcode == 'const':
            body.append(MOV(tin.arg1, self.get(tin.dest, proc)))

        elif tin.opcode == 'copy':
            body.append(MOV(self.get(tin.arg1, proc), "%rax"))
            body.append(MOV("%rax", self.get(tin.dest, proc)))

        elif tin.opcode in simple_binop:
            body.append(MOV(self.get(tin.arg1, proc),"%rax" ))
            body.append(simple_binop[tin.opcode](self.get(tin.arg2, proc),"%rax"))
            body.append(MOV("%rax",self.get(tin.dest, proc)))

        elif tin.opcode in simple_unop:
            body.append(MOV(self.get(tin.arg1, proc), "%rax" ))
            body.append(simple_unop[tin.opcode]("%rax"))
            body.append(MOV("%rax", self.get(tin.dest, proc)))

        elif tin.opcode == 'shl' or tin.opcode == 'shr':
            body.append(MOV(self.get(tin.arg2, proc), "%rcx" ))
            body.append(MOV(self.get(tin.arg1, proc), "%rax" ))
            body.append((SAL if tin.opcode == 'shl' else SAR)('%rcl', '%rax'))
            body.append(MOV("%rax",self.get(tin.dest, proc)))
  
        elif tin.opcode == 'div' or tin.opcode == 'mod':
            body.append(MOV(self.get(tin.arg1, proc),'%rax'))
            body.append(IDIV(self.get(tin.arg2, proc)))
            body.append(MOV('%rax' if tin.opcode == 'div' else '%rdx', self.get(tin.dest, proc)))

        elif tin.opcode == 'jmp':
            body.append(JMP(tin.arg1))

        elif tin.opcode in jcc_map:
            body.append(CMP(0, self.get(tin.arg1, proc)))
            body.append(jcc_map[tin.opcode](tin.arg2))

        elif tin.opcode == 'label':
            body.append(LABEL(tin.arg1))

        elif tin.opcode == 'param':
            self.paramnum += 1
            body.append(MOV(self.get(tin.arg2, proc), '%rax'))
            body.append(MOV('%rax', self.get("param" + str(tin.arg1), proc)))

        elif tin.opcode == 'call':
            reg = ['%rdi','%rsi','%rdx','%rcx','%r8','%r9']
            for i in range(self.paramnum):
                if i<6: body.append(MOV(self.get("param"+str(i+1), proc), reg[i]))
                else: body.append(PUSH(self.get("param" + str(i+1), proc), None))               
            self.paramnum = 0
            body.append(CALL(tin.arg1[1:]))

        else:
            raise RuntimeError(f'Isel: cannot handle TAC opcode {tin.opcode}')

        return body

def generate(tac_file, gcc=True):
    tac_prog = tac.load_tac(tac_file)
    x64_prog = Isel()
    # print(tac_prog)
    x64_prog.proc(tac_prog)
    # print(x64_prog.results)
    x64_file = tac_file[:-3] + 's'
    out_files = []
    with open(x64_file, "w") as f:
                for xi in x64_prog.results: print(xi, file=f)
    out_files.append(x64_file)
    if gcc:
        exe_file = tac_file[:-3] + 'exe'
        cmd = ["gcc", "-g", "-o", exe_file, x64_file, "bx_runtime.c"]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise RuntimeError(f'Failed to run: {" ".join(cmd)}')
        out_files.append(exe_file)
    return out_files

if __name__ == "__main__":
    generate(sys.argv[1], gcc=False)
    