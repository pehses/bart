# Copyright 2016. The Regents of the University of California.
# All rights reserved. Use of this source code is governed by 
# a BSD-style license which can be found in the LICENSE file.
#
# Authors: 
# 2016 Siddharth Iyer <sid8795@gmail.com>
# 2018 Soumick Chatterjee <soumick.chatterjee@ovgu.de> , WSL Support

import subprocess as sp
import tempfile as tmp
import cfl
import os
from wslsupport import PathCorrection

def bart(nargout, cmd, *args):

    if type(nargout) != int or nargout < 0:
        print("Usage: bart(<nargout>, <command>, <arguments...>)")
        return None

    try:
        bart_path = os.environ['TOOLBOX_PATH']
    except:
        bart_path = None
    isWSL = False

    if bart_path is None:
        if os.path.isfile('/usr/local/bin/bart'):
            bart_path = '/usr/local/bin'
        elif os.path.isfile('/usr/bin/bart'):
            bart_path = '/usr/bin'
        else:
            bartstatus = os.system('wsl bart version -V')
            if bartstatus==0:
                bart_path = '/usr/bin'
                isWSL = True
            else:
                raise Exception('Environment variable TOOLBOX_PATH is not set.')

    name = tmp.NamedTemporaryFile().name

    nargin = len(args)
    infiles = [name + 'in' + str(idx) for idx in range(nargin)]

    for idx in range(nargin):
        cfl.writecfl(infiles[idx], args[idx])

    outfiles = [name + 'out' + str(idx) for idx in range(nargout)]

    cmd = cmd.split(" ")

    if os.name =='nt':
        if isWSL:
            #For WSL and modify paths
            infiles = [PathCorrection(item) for item in infiles]
            outfiles = [PathCorrection(item) for item in outfiles]
            cmd = [PathCorrection(item) for item in cmd]
            shell_cmd = ['wsl', 'bart', *cmd, *infiles, *outfiles]
        else:
            #For cygwin use bash and modify paths
            infiles = [item.replace(os.path.sep, '/') for item in infiles]
            outfiles = [item.replace(os.path.sep, '/') for item in outfiles]
            cmd = [item.replace(os.path.sep, '/') for item in cmd]
            shell_cmd = ['bash.exe', '--login',  '-c', os.path.join(bart_path, 'bart'), *cmd, *infiles, *outfiles]
            #TODO: Test with cygwin, this is just translation from matlab code
    else:
        shell_cmd = [os.path.join(bart_path, 'bart'), *cmd, *infiles, *outfiles]

    # run bart command and store errcode and stdout in function attributes
    bart.ERR, bart.stdout, bart.stderr = execute_cmd(shell_cmd)

    for elm in infiles:
        if os.path.isfile(elm + '.cfl'):
            os.remove(elm + '.cfl')
        if os.path.isfile(elm + '.hdr'):
            os.remove(elm + '.hdr')

    output = []
    for idx in range(nargout):
        elm = outfiles[idx]
        if not bart.ERR:
            output.append(cfl.readcfl(elm))
        if os.path.isfile(elm + '.cfl'):
            os.remove(elm + '.cfl')
        if os.path.isfile(elm + '.hdr'):
            os.remove(elm + '.hdr')

    if bart.ERR:
        raise Exception(f"Command exited with error code {bart.ERR}.")

    if nargout == 1:
        output = output[0]

    return output


def execute_cmd(cmd):
    """
    Execute a command in a shell.
    Print and catch the output.
    """
    
    errcode = 0
    stdout = ""
    stderr = ""

    proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)

    for stdout_line in iter(proc.stdout.readline, ""):
        stdout += stdout_line
        print(stdout_line, end="")
    proc.stdout.close()

    errcode = proc.wait()
    if errcode:
        stderr = "".join(proc.stderr.readlines())
        print(stderr)
    proc.stderr.close()

    return errcode, stdout, stderr
