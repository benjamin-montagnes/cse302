#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

@author: benjaminmontagnes and antoninwattel

"""

import subprocess,os

def assemble_and_link(asm_file, runtime_file, debug=False):
    """Run gcc on `asm_file' and `runtime_file' to create a suitable 
    executable file. If `debug' is True, then also send the `­g' option
    to gcc that will store debugging information useful for gdb.""" 
    cmd = ["gcc"]
    if debug: cmd.append("­g")
    assert asm_file.endswith('.s')
    exe_file = asm_file[:-1] + 'exe'
    cmd.extend(["­o", exe_file, asm_file, runtime_file])
    result = subprocess.run(cmd)
    return result.returncode # 0 on success, non­zero on failure

if __name__ == '__main__':
    import sys, getopt
    opts, bx_files = getopt.getopt(sys.argv[1:],
                                   'h:',
                                   ['keep-tac', 'stop-tac', 'test-bx1'])
    if len(bx_files) > 1:
        print(f'Only one file at a time')
        exit(1)
    bx_file = bx_files[0]
    tac_file = bx_file[:-3] + '.tac'
    exe_file = bx_file[:-3] + '.exe'
    s_file = bx_file[:-3] + '.s'
    expected_file = bx_file[:-3] + '.expected'
    remove_tac = True
    continue_wrapper = True
    test_bx1 = False
    is_tac = False
    print('OPTS:',opts)
    print('bx_file:', bx_file)
    for opt, val in opts:
        if opt == '-h':
            print(f'''\
USAGE: {sys.argv[0]} OPTIONS file.bx ...

Where OPTIONS is one of

  --keep-tac         Produces the intermediate .tac file
  --stop-tac          Makes the wrapper stop after creating the .tac file
  --test-bx1            Only tests the bx1tac file and outputs results 
  ''')
            exit(0)
        elif opt == '--­­keep­-tac':
            print('Keeping tac...')
            remove_tac = False
        elif opt == '--stop-tac':
            print('Stopping after creating tac')
            continue_wrapper = False
            remove_tac = False
        elif opt == '--test-bx1':
            print('\nPrinting results only for bx1 to tac !\n')
            test_bx1 = True
        else:
            print(f'Unknown option {opt}')
            exit(1)
            
    if bx_file.endswith('.tac'): 
        is_tac = True
        tac_file = bx_file
        expected_file = bx_file[:-4] + '.expected'
        
            
    if ( not bx_file.endswith('.bx')) and (not bx_file.endswith('.tac') ):
        print(f'File name does not end in ".bx" or in ".tac"')
        exit(1)
        
    if not is_tac : os.system("python3 bx1tac.py "+bx_file)
    
    if test_bx1 : 
        print('\n\n Our results: \n')
        if os.path.exists(tac_file) : os.system('./tac.py '+tac_file)
        else : 
            print('ERROR: could not create tac file',tac_file)
            exit(1)
        continue_wrapper = False
        
    if continue_wrapper :
        if os.path.exists(tac_file) : os.system("python3 tacx64.py "+tac_file)
        else : 
            print('ERROR: could not create tac file')
            exit(1)
        if os.path.exists(s_file) : os.system("gcc -o "+exe_file+s_file+"bx_runtime.c")
        else:
            print('ERROR: could not create assembly file')
            exit(1)
        print('\n\n Our results: \n')
        os.system('./'+exe_file)
        os.system('rm '+s_file)
        os.system('rm '+exe_file)
        
    if remove_tac: os.system('rm '+tac_file)
    
    print('\n\n Expected results: \n')
    if os.path.exists(expected_file): os.system('cat '+expected_file)
    else :
        print('ERROR: no .expected file to display result')
        exit(1)
    print('')
    






































