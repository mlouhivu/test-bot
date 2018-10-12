import subprocess
import commands
import os
import time
import itertools
from manifest import Manifest
from config import Config
import execute

botdir = '.test'
if os.path.exists(botdir):
    manifest = Manifest(botdir + '/manifest')
    config = Config(botdir + '/config')
    log = open(botdir + '/log', 'a')
basedir = os.path.realpath('.')

def guess_binary(pre, post):
    files = list(post.difference(pre))
    prune = []
    for name in files:
        if name.endswith(('.o', '.mod', '.MOD')):
            prune.append(name)
    files = [x for x in files if x not in prune]
    if not len(files):
        return None
    return files[0]

def make(target):
    pre_log(target, 'make')
    if hasattr(target, 'makefile') and target.makefile:
        cmd = 'make -f ' + target.filename()
    else:
        cmd = 'make'
    subprocess.call('make clean', stdout=log, stderr=subprocess.STDOUT,
                    shell=True)
    pre = set([x for x in os.listdir('.') if os.path.isfile(x)])
    try:
        subprocess.check_call(cmd, stdout=log, stderr=subprocess.STDOUT,
                shell=True)
        post = set([x for x in os.listdir('.') if os.path.isfile(x)])
        binary = guess_binary(pre, post)
        if binary and not hasattr(target, 'binary'):
            target.binary = str(binary)
        return True
    except subprocess.CalledProcessError:
        return False
    finally:
        post_log(target)

def build(target, family, output=None, link=True):
    pre_log(target, 'build')
    flavours = []
    if target.mpi:
        flavours.append('mpi')
    if target.omp:
        flavours.append('omp')
    cc = config.compiler(family, target.language(), flavours, link=link)
    link = config.linker(family, target.language(), flavours)
    if output:
        cc.output = output
    elif hasattr(target, 'binary'):
        cc.output = target.binary
    if not link:
        cc.output = None
    cc.stdout = log
    cc.stderr = log
    try:
        return cc.compile(target.filename())
    finally:
        post_log(target)

def run_multiple(target):
    pre_log(target, 'run multiple')
    args = {'out': log}
    args['export'] = target.as_tuple('export')
    if target.mpi and target.omp:
        args['tasks'] = config.mpi_tasks or 4
        args['threads'] = config.omp_threads or 4
    elif target.mpi:
        args['tasks'] = config.mpi_tasks or 4
    elif target.omp:
        args['tasks'] = 1
        args['threads'] = config.omp_threads or 4
    if hasattr(target, 'user_input') and type(target.user_input) is tuple \
            and (len(target.user_input) == len(target.binary)):
        user_inputs = target.as_tuple('user_input')
        log_line('Unique user input for each binary.')
    else:
        user_inputs = itertools.repeat(target.as_str('user_input'))
        log_line('Single user input for all binaries.')
    status = True
    try:
        for binary, user_input in zip(target.binary, user_inputs):
            log_line('')
            args['user_input'] = user_input
            command = './' + binary
            if hasattr(target, 'arguments'):
                command += ' ' + target.arguments
            if target.mpi and target.omp:
                status = status and execute.parallel(command, **args)
            elif target.mpi:
                status = status and execute.parallel(command, **args)
            elif target.omp:
                status = status and execute.parallel(command, **args)
            else:
                status = status and execute.serial(command, **args)
        return status
    finally:
        post_log(target)

def run(target):
    if hasattr(target, 'binary') and type(target.binary) is tuple:
        return run_multiple(target)
    pre_log(target, 'run')
    command = './a.out'
    try:
        if hasattr(target, 'binary'):
            command = './' + target.binary
        if hasattr(target, 'arguments'):
            command += ' ' + target.arguments
        args = {'out': log}
        args['user_input'] = target.as_str('user_input')
        args['export'] = target.as_tuple('export')
        if target.mpi and target.omp:
            args['tasks'] = config.mpi_tasks or 4
            args['threads'] = config.omp_threads or 4
            return execute.parallel(command, **args)
        elif target.mpi:
            args['tasks'] = config.mpi_tasks or 4
            return execute.parallel(command, **args)
        elif target.omp:
            args['tasks'] = 1
            args['threads'] = config.omp_threads or 4
            return execute.parallel(command, **args)
        else:
            return execute.serial(command, **args)
    finally:
        post_log(target)

def init_log():
    log.write('\n' + '#'*80 + '\n')
    log.write('Run started at {0}\n'.format(time.asctime()))
    log_modules()
    log.flush()

def pre_log(target, mode):
    line = '[-- Start of ' + str(mode).upper() + ' ' + str(target) + ' '
    while len(line) < 78:
        line += '-'
    line += ']'
    log.write('\n' + line + '\n')
    log.flush()

def post_log(target):
    line = '[-- End of ' + str(target) + ' '
    while len(line) < 78:
        line += '-'
    line += ']'
    log.write('\n' + line + '\n')
    log.flush()

def log_line(txt):
    log.write(txt + '\n')
    log.flush()

def log_modules():
    status, out = commands.getstatusoutput('module list')
    log_line('')
    log.write(out.rstrip('\n') + '\n')
