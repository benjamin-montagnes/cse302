# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
1. Reads in a TAC file, compute its CFG, and then performs liveness analysis
2. Uses the live sets information to do crude SSA generation
3. Performs all the SSA minimization steps until no further minimizations can be done
4. Then linearizes the SSA CFG back to TAC, and then outputs it to a file with the extension.ssa.tac.
   That is, an input fileprog.tacshould be converted toprog.ssa.tac
"""

import tac, sys, copy
import cfg as cfg_


def add_phi_def(cfg):
    """Add φ-function definitions for all temporaries that are live-in at the 
    start of each block. These φ-function definitions must come before any other
    instruction in the block. """ 
    liveinset = []
    liveoutset = []
    cfg_.recompute_liveness(cfg, liveinset, liveoutset)
    for block in cfg._blockmap.values():
        for temp in liveinset[block.first_instr()]:
            if temp != '%_': block.body.insert(0,tac.Instr(temp,'phi', tuple(),None))
            
            
def version_tmp(cfg):
    """Uniquely version every temporary that is defined by any instruction in the
    entire CFG.""" 
    k = 1
    for block in cfg._blockmap.values():
        for instr in block.body:
            if instr.dest and instr.dest != '%_': instr.dest += "."+str(k)
            k+=1
        
def get_root(tmp): tmp.split(sep='.')[0][1:] 

def update_uses(cfg):
    """Update the uses of each temporary within the same block to their most recent versions."""
    for block in cfg._blockmap.values():
        for i in range(len(block.body)):
            instr = block.body[i]
            a1,a2 = instr.arg1, instr.arg2
            t1,t2 = get_root(a1),get_root(a2)
            if a1 != None and type(a1) == str and a1[0] == "%" and a1[0] != '%_':
                for j in range(i, -1, -1):
                    if block.body[j].dest != None and get_root(block.body[j].dest) == t1:
                        instr.arg1 = block.body[j].dest
            if a2 != None and type(a2) == str and a2[0] == "%" and a2[0] != '%_':
                for k in range(i, -1, -1):
                    if block.body[k].dest != None and get_root(block.body[k].dest) == t2:
                        instr.arg2 = block.body[k].dest

def fill_phi_args(cfg): #...
    """For every edge in the CFG (use the.edges()iterator) fill in the arguments 
    of the φ functions.For an edge from block .L1 to .L2, there would be a φ-argument
    (in the.L2block) of the form.L1:%nfor every temporary%nthat comes to.L2 from.L1."""
    _,block = next(iter(cfg._blockmap.items()))
    il= init_livein(cfg)
    for instr in block.body:
        if instr.opcode =="phi" and (get_root(instr.dest) in il):
            instr.arg1 = list(instr.arg1)
            instr.arg1.append((cfg.proc_name,'%'+get_root(instr.dest)))
    for e in cfg.edges():
        for instr in cfg[e[1]].body:
            if instr.opcode == "phi":
                tmp = ""
                for i in range(1, len(cfg[e[0]].body) + 1):
                    tmp = cfg[e[0]].body[-i].dest
                    if tmp == None: continue
                    if get_root(tmp) == get_root(instr.dest): break
                instr.arg1 = list(instr.arg1)
                instr.arg1.append((e[0], tmp))
        

def crude_ssa(cfg):
    """ Perform crude SSA generation Algorithm"""
    add_phi_def(cfg)
    version_tmp(cfg)
    update_uses(cfg)
    fill_phi_args(cfg)
    
def null_choice_elim(ssa):
    """removes redundant φ-function definitions from the SSA."""
    for block in cfg._blockmap.values():
        c_block = block.copy() #should it be copy.copy(block) ?
        for instr in c_block.body:
            if instr.opcode =='phi':
                tf = True 
                for tmp in instr.arg1.values(): 
                    if tmp != instr.dest: tf = False
                if tf: block.body.remove(instr)
                
def rename_elimination(ssa):
    """ perform rename elimination """
    pass
    
                    
def minimization_steps(ssa):
    """perform all the SSA minimization steps"""
    old = cfg
    while True:
        null_choice_elim(cfg)
        rename_elimination(cfg)
        tf = True
        for ins,block in cfg._blockmap.items():
            if block.body == old._blockmap[ins].body: tf = False 
        old = cfg
        if not tf: break
        
def init_livein(cfg):
    args = []
    _,block = next(iter(cfg._blockmap.items()))
    for instr in block.body:
        child = set()
        if type(instr.arg1) == str and instr.arg1[0] == '%': child.add(instr.arg1)
        if type(instr.arg2) == str and instr.arg2[0] == '%': child.add(instr.arg2)
        for i in child:
            if not i in args and not get_root(i).isnumeric(): args.append(get_root(i))
    return args
                

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
    for filename in sys.argv[1:]:
        cfgs = cfg_.main_cfg(filename) #compute cfg from tac
        with open(f'{filename[:-4]}.ssa.tac','w') as f: 
            for cfg in cfgs:
                dproc = tac.Proc(cfg.proc_name, [], [])
                crude_ssa(cfg)
                minimization_steps(cfg)
                cfg_.linearize(dproc, cfg)
                init_args = init_livein(cfg) #find lab_entry 
                f.write('proc '+str(cfg.proc_name) + '(')
                if len(init_args)>0:
                    for arg in init_args[:-1]:
                        f.write('%'+arg+',')
                    f.write('%'+init_args[-1]+'):\n')
                else: f.write('):\n')
                for instr in dproc.body:
                    f.write(str(instr)+'\n')