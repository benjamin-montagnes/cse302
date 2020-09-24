#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: benjaminmontagnes and antoninwattel

"""

from bx0tac import TMM

import sys, tac

def main():
    for filename in sys.argv[1:]:
        print(f'[[ processing {filename} ]]')
        # load_source(filename)
        
        tmm = TMM()
        tmm.instrs = tac.load_tac(filename)
        tmm.copy_prop()
        tmm.dead_copy()
        # print(*tmm.instrs, sep ='\n')
        
        fname = filename.split('.')[0] + '_optimized.tac'
        f = open(fname,"w+")
        for item in tmm.instrs: f.write("%s\n" % item)
        f.close()
    
if __name__ == '__main__':
    main()