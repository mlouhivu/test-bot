#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
#---------------------------------------------------------------------------#
# Function: Test bot.                                                       #
# Usage: bot.py [options] [command] {[options]}                             #
# Help: run bot.py --help                                                   #
#---------------------------------------------------------------------------#
from argparse import ArgumentParser
import logging
import sys
import os

from testbot import core

class MyParser(ArgumentParser):
    def error(self, message):
        self.print_help()
        sys.exit(1)

def run():
    prog = 'bot'
    usage = '%(prog)s {options} [command] {<path> ...}'
    desc = 'Test bot.'

    parser = MyParser(usage=usage, description=desc)
    parser.add_argument('command',
            help='add / init / manifest / run')
    parser.add_argument('paths', nargs='*',
            help='(optional) files or directories to process')
    parser.add_argument('--compiler', action='store', default='cray',
            help='compile environment in use (default: %(default)s)')
    parser.add_argument('--properties', action='store', default='type=pass',
            help='(only add) define properties for new tests')
    parser.add_argument('--verbose', action='store_true', default=False,
            help='display additional information while running')
    parser.add_argument('--debug', action='store_true', default=False,
            help='run in debug mode, i.e. maximum information')

    args = parser.parse_args()

    # set logger format etc.
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s ' + \
            '%(message)s @ %(asctime)s %(module)s line %(lineno)s',
            datefmt='%H:%M:%S')
    # set logging thresholds
    if args.debug:
        logging.getLogger('').setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger('').setLevel(logging.WARNING)
    else:
        logging.getLogger('').setLevel(logging.CRITICAL)
    logging.debug('args: %s' % repr(args))

    # execute given command
    if args.command == 'manifest':
        core.manifest.echo()
    elif args.command == 'add':
        for path in args.paths:
            core.manifest.update(path, args.properties)
    elif args.command == 'init':
        if not os.path.exists(core.botdir):
            os.mkdir(core.botdir)
            with open(core.botdir + '/config', 'w') as fp:
                fp.write('# Configuration for\n')
                fp.write('#   github.com/mlouhivu/test-bot.git\n')
            with open(core.botdir + '/manifest', 'w') as fp:
                fp.write('# Manifest of test targets for\n')
                fp.write('#   github.com/mlouhivu/test-bot.git\n')
    elif args.command == 'run':
        core.init_log()
        failed = []
        pwd = os.path.realpath('.')
        result = {True: '[ OK ]', False: '[FAIL]', 'skip': '[SKIP]'}
        print('BUILD   RUN    Target')
        for target in core.manifest:
            os.chdir(target.workdir())
            if target.language() == 'make':
                build = core.make(target)
            elif hasattr(target, 'do_not_link') and target.do_not_link:
                build = core.build(target, args.compiler, link=False)
            else:
                build = core.build(target, args.compiler)
            if not build:
                failed.append(target)
                run = 'skip'
            elif (hasattr(target, 'do_not_link') and target.do_not_link) or \
                    (hasattr(target, 'skip_run') and target.skip_run):
                run = 'skip'
            else:
                run = core.run(target)
            if not run:
                failed.append(target)
            print('{0}  {1}'.format(
                ' '.join([result[x] for x in (build, run)]), str(target)))
            os.chdir(pwd)
        print('')
        if failed:
            print('Oops. {0} targets failed:'.format(len(failed)))
            for target in failed:
                print('  ' + str(target))
        else:
            print('Yippee. All is good.')
    else:
        print('Unknown command: ' + args.command)
        return 1

    # the end.
    return 0

if __name__ == '__main__':
    run()
