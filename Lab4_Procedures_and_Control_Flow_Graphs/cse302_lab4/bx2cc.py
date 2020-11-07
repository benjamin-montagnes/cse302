#!/usr/bin/env python3

import subprocess,os,sys, getopt

if __name__ == '__main__':
    bx_file = sys.argv[1]
    tac_file = bx_file[:-3] + '.tac'
    s_file = bx_file[:-3] + '.s'
    os.system("python3 bx2tac.py "+bx_file)
    print('\n\n Tac file produced: \n')
    os.system("cat "+tac_file)
    print('\n')
    os.system("python3 tacx64.py "+tac_file)
    print('\n\n Assembly file produced: \n')
    os.system("cat "+s_file)

