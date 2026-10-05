import subprocess

from testbot import config
from testbot import core

def serial(command, out=None, err=subprocess.STDOUT, export=None,
        user_input=None, build=False):
    if not build and config.compute_node:
        if config.runner == 'aprun':
            command = aprun(command, tasks=1, env=export)
        elif config.runner == 'mpirun':
            command = mpirun(command, tasks=1, env=export)
        elif config.runner == 'srun':
            command = srun(command, tasks=1, env=export)
        else:
            raise ValueError('Unknown runner: %s' % config.runner)
    if user_input:
        command = "echo '{0}' | ".format(user_input) + command
    core.log_line(command)
    try:
        subprocess.check_call(command, stdout=out, stderr=err, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def parallel(command, tasks=4, threads=None, out=None, err=subprocess.STDOUT,
        export=None, user_input=None):
    if config.runner == 'aprun':
        command = aprun(command, tasks, threads, export)
    elif config.runner == 'mpirun':
        command = mpirun(command, tasks, threads, export)
    elif config.runner == 'srun':
        command = srun(command, tasks, threads, export)
    else:
        raise ValueError('Unknown runner: %s' % config.runner)
    if user_input:
        command = "echo '{0}' | ".format(user_input) + command
    core.log_line(command)
    try:
        subprocess.check_call(command, stdout=out, stderr=err, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def aprun(command, tasks=4, threads=None, env=None):
    runner = 'aprun -n %d ' % tasks
    if threads:
        runner += '-d %d -e OMP_NUM_THREADS=%d ' % (threads, threads)
    if env:
        if type(env) is str:
            runner += '-e ' + env + ' '
        else:
            runner += '-e ' + ' -e '.join(env) + ' '
    return runner + command

def mpirun(command, tasks=4, threads=None, env=None):
    runner = ''
    if tasks and tasks > 1:
        runner = 'mpirun -np %d ' % tasks
    if threads:
        runner = 'OMP_NUM_THREADS=%d ' % threads + runner
    if env:
        if type(env) is str:
            runner += env + ' '
        else:
            runner += ' '.join(env) + ' '
    return runner + command

def srun(command, tasks=4, threads=None, env=None):
    runner = 'srun -n {} '.format(tasks)
    if threads:
        runner = 'OMP_NUM_THREADS={} {}'.format(threads, runner)
    if env:
        if type(env) is str:
            runner += env + ' '
        else:
            runner += ' '.join(env) + ' '
    return runner + command
