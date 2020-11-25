# -*- coding: utf-8 -*-

"""perform register allocation ona a (non-SSA) TAC input file. The output 
should also be a TAC file with an allocation record as a comment before every procedure. """

"""You should usessagen.pythat you wrote in checkpoint 1 to create theCFGinSSA, 
and then performthe algorithms outlined in this section to allocate the (versioned) 
temporaries to registers. Once done,convert theSSA CFGback toTAC
(leaving theφ-functions in place), and print the allocation record in acomment
 before each procedure.For an input fileprog.tac, produce the outputprog.alloc.tac.
 If you wish, you may also outputtheSSAform before register allocation,
 prog.ssa.tac, like you did in checkpoint 1"""


from ssagen import * #CHANGE ???
import cfg as cfg_
import tac
from copy import copy

#from a CFG, the first step is to compute the interference graph
class Interference_Graph:
    def __init__(self):
        self.nodes = {}#he nodes consist of TAC temporaries
        self.edges = {}#edge between two nodes:the nodes cannotbe allocated to the same machine register
        self.color_map= ('%rax','%rcx','%rdx','%rsi','%rdi','%r8','%r9','%r10','%rbx','%r12','%r13','%r14','%r15','%r11','%rbp','%rsp')
        self.reg_map = {reg : self.color_map.index(reg)+1 for reg in self.color_map}
        self.stack_map = {}
    
    def cfg_to_ig(self, cfg):
        """Compute interference graph from cfg"""
        edges, nodes = set(), set()
        #you first need to compute liveness information for every instruction ??
        livein = []
        liveout = []
        cfg_.recompute_liveness(cfg, livein, liveout)
        for instr in cfg.instrs():
            tmps = set()
            if type(instr.arg1) == str and instr.arg1[0] == '%': tmps.add(instr.arg1)
            if type(instr.arg2) == str and instr.arg2[0] == '%': tmps.add(instr.arg2)
            if type(instr.dest) == str and instr.dest[0] == '%':  defs = {instr.dest}
            else: defs = {}
            if instr.opcode == 'copy': 
                #If I is acopyinstruction, every temporary x∈liveout(I) interferes
                #with every temporary y∈use(I)∪def(I)
                for x in liveout[instr]:
                    for y in tmps.union(defs): self.add_edge(x,y,nodes,edges)
            else:
                #If I is any other instruction, then every temporary x∈liveout(I)
                #interferes with every temporary in y∈def(I).
                if instr.arg1 != '%_':
                    for x in liveout[instr]:
                        for y in defs: self.add_edge(x,y,nodes,edges)                 
        self.nodes, self.edges = nodes, edges

    def add_edge(self, x, y, nodes, edges):
        if x != '%_' and y != '%_' and x != y:
            nodes.add(x)
            nodes.add(y)
            edges.add(frozenset([x,y]))

    def max_cardinality_search(self):
        """input: interference graph with |V|=n, output: simplical elimination ordering"""
        weights,seo, vertices = {}, [], copy(self.nodes)
        for i in self.nodes: weights[i] = 0
        for _ in range(len(self.nodes)):
            v, res = max(weights, key=weights.get) , set()
            for a,b in self.edges:
                if v == a: res.add(b)
                elif v == b: res.add(a)
            for vi in vertices.intersection(res): weights[vi] += 1
            if v in vertices:
                vertices.remove(vi)
                seo.append(vi)
        return seo
    
    def greedy_coloring(self, elim_ordering, col):
        """Greedy coloring algorithm"""
        graph_dict, card = self.nodes, self.max_cardinality_search()
        for u in graph_dict:
            if not u in col.keys(): col[u]=0
        n = len(elim_ordering)
        for v in card:
            if col[v]!=0: continue
            c, neighbor_color = 1, {col[w] for w in graph_dict}
            while True:
                if c not in neighbor_color: break
                c+=1
            col[v] = c
        return col
    
    def tmp_spill(self, color_map): #to change
        """ 1.pick a temporary and assign it ato a stack slot 
            2.Remove that temporary form the interference graph
            3.Recompute the SEO with max cardinality search and retry coloring
            repeat until coloring with <= 13 colors"""
        pass

    def allocation_record(self):
        """Compute allocation record for the cfg
        the allocation record contains the following
        -How much stack space to allocate for spilled temporaries
        -Which registers are mapped to which temporaries"""
        pass

if __name__ == '__main__':
    import logging
    import os
    from argparse import ArgumentParser
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
    ap = ArgumentParser(description='TAC library, parser, and interpreter')
    ap.add_argument('file', metavar='FILE', type=str, nargs=1, help='A TAC file')
    ap.add_argument('-v', dest='verbosity', default=0, action='count',
                    help='increase verbosity')
    args = ap.parse_args()
    gvars, procs = dict(), dict()
    for cfg in cfg_.main_cfg(args.file[0]):
        logging.info(f'Processing cfg')
        # Uncomment these two lines to have it generate a PDF of the CFG
        #   (Requires the graphviz toolkit: http://graphviz.org)
        # cfg.write_dot(args.file[0])
        # os.system(f'dot -Tpdf -O {args.file[0]}.{tlv.name[1:]}.dot')
        crude_ssa(cfg)
        intg = Interference_Graph()
        intg.cfg_to_ig(cfg)
        logging.info(f'Finished processing')
        # with open(f'{filename[:-4]}.alloc.tac','w') as tac_file:
        #     for decl in gvars+procs:
        #         print(decl, sep='\n',file=tac_file)
        print(intg.max_cardinality_search())