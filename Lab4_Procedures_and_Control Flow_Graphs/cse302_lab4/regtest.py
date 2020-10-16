#!/usr/bin/env python3

import sys, subprocess, difflib, os, time
from pathlib import Path
from multiprocessing import Pool

def log(msg):
    print(f'[{time.strftime(time.strftime("%Y-%m-%dT%H:%M:%S%z"))}] {msg}')

def do_regression_check(bxfile):
    bxfile = Path(bxfile)
    try:
        assert bxfile.suffix == '.bx'
        asmfile = bxfile.with_suffix('.s')
        expfile = bxfile.with_suffix('.expected')
        tacfile = bxfile.with_suffix('.tac')
        assert subprocess.run(["python3", "bx1cc.py",
                               "--keep-tac", bxfile]).returncode == 0
        exefile = bxfile.with_suffix('.exe')
        if not exefile.is_file():
            rtfile = bxfile.parent.joinpath('bx_runtime.c')
            assert subprocess.run(['gcc', '-o', exefile,
                                   asmfile, rtfile]).returncode == 0
        log(f'GEN {tacfile} {asmfile} {exefile}')
        tacresult = subprocess.run(["python3", "tac.py", tacfile], capture_output=True)
        assert tacresult.returncode == 0
        tacoutput = tacresult.stdout.decode().split('\n')
        exeresult = subprocess.run([exefile], capture_output=True)
        assert exeresult.returncode == 0
        exeoutput = exeresult.stdout.decode().split('\n')
        if expfile.is_file():
            with open(expfile, 'r') as f:
                expected = f.read().split('\n')
                if tacoutput != expected:
                    print(*difflib.unified_diff(tacoutput, expected, lineterm='',
                                                fromfile=tacfile.with_suffix('.tac.output').name,
                                                tofile=expfile.name),
                          sep='\n')
                    raise RuntimeError(f'{tacfile}: output does not match {expfile}')
                log(f'MATCH {tacfile} {expfile}')
                if exeoutput != expected:
                    print(*difflib.unified_diff(exeoutput, tacoutput, lineterm='',
                                                fromfile=exefile.with_suffix('.exe.output').name,
                                                tofile=expfile.name),
                          sep='\n')
                    raise RuntimeError(f'{exefile}: output does not match {expfile}')
                log(f'MATCH {exefile} {expfile}')
        else:
            expfile = expfile.with_suffix('.tac-expected')
            with open(expfile, 'w') as f:
                print(*tacoutput, sep='\n', end='', file=f)
                # print(file=f)
            log(f'GEN {expfile}')
            if exeoutput != tacoutput:
                print(*difflib.unified_diff(exeoutput, tacoutput, lineterm='',
                                            fromfile=exefile.with_suffix('.exe.output').name,
                                            tofile=tacfile.with_suffix('.tac.output').name),
                      sep='\n')
                raise RuntimeError(f'{exefile}: output does not match {expfile}')
            log(f'MATCH {exefile} {tacfile}')
        os.remove(tacfile)
        os.remove(exefile)
        os.remove(asmfile)
        log(f'DELETE {tacfile} {asmfile} {exefile}')
        log(f'SUCCESS {bxfile}')
    except Exception as exn:
        log(f'FAIL {bxfile}')
        log(f'EXN [{exn.__class__.__name__}] {exn!s}')
        raise

if __name__ == '__main__':
    fileset = frozenset(sys.argv[1:])
    with Pool() as p:
        p.map(do_regression_check, fileset)
