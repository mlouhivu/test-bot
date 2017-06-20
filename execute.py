import subprocess
import config

def serial(command, out=None, err=subprocess.STDOUT):
    print('Execute: ' + command)
    try:
        subprocess.check_call(command, stdout=out, stderr=err, shell=True)
        print('  OK')
    except subprocess.CalledProcessError:
        print('  FAIL')

def parallel(command, tasks=4, threads=None, out=None, err=subprocess.STDOUT):
    if config.mpi_runner == 'aprun':
        cmd = aprun(command, tasks, threads)
    elif config.mpi_runner == 'mpirun':
        cmd = mpirun(command, tasks, threads)
    else:
        raise ValueError, 'Unknown MPI runner: %s' % mpirun
    try:
        subprocess.check_call(cmd, stdout=out, stderr=err, shell=True)
        print('  OK')
    except subprocess.CalledProcessError:
        print('  FAIL')

def aprun(command, tasks=4, threads=None):
    runner = 'aprun -n %d ' % tasks
    if threads:
        runner += '-d %d -e OMP_NUM_THREADS=%d ' % (threads, threads)
    return runner + command

def mpirun(command, tasks=4, threads=None):
    runner = 'mpirun -np %d ' % tasks
    if threads:
        runner = 'OMP_NUM_THREADS=%d ' % threads + runner
    return runner + command