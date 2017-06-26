import subprocess
from manifest import Manifest
from config import Config
import execute

botdir = '.bot'
manifest = Manifest(botdir + '/manifest')
config = Config(botdir + '/config')
log = open(botdir + '/loki', 'a')
log.write('#'*80 + '\n')

def make(target):
    try:
        subprocess.check_call('make', stdout=log, stderr=subprocess.STDOUT,
                shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def build(target, family):
    flavours = []
    if target.mpi:
        flavours.append('mpi')
    if target.omp:
        flavours.append('omp')
    cc = config.compiler(family, target.language(), flavours)
    link = config.linker(family, target.language(), flavours)
    if hasattr(target, 'output'):
        cc.output = target.output
    cc.stdout = log
    cc.compile(target)
    return True

def run(target):
    binary = './a.out'
    if hasattr(target, 'binary'):
        binary = './' + target.binary
    if target.mpi and target.omp:
        tasks = config.mpi_tasks or 4
        threads = config.omp_threads or 4
        return execute.parallel(binary, tasks, threads, out=log)
    elif target.mpi:
        tasks = config.mpi_tasks or 4
        return execute.parallel(binary, tasks, out=log)
    elif target.omp:
        threads = config.omp_threads or 4
        return execute.serial(binary, threads, out=log)
    else:
        return execute.serial(binary, out=log)

