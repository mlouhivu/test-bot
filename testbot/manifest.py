import os
import re

from testbot.target import Target
from testbot import core

ro_target = re.compile('\[\s*(?P<target>[^]]+)\s*\](?P<definition>[^[]*)')
ro_assign = re.compile('(?P<all>(?P<key>[a-zA-Z0-9_.-]+)='
        + '''(?P<value>["'].*["']|\(.*\)|[a-zA-Z0-9_./-]+))''')
ro_tag = re.compile('(^|\s+)\+(?P<tag>\w+)')
ro_word = re.compile('''["'](.*)["']|(\w+)''')
ro_comment = re.compile('(^|\n)\s*(?P<comment>#[^\n]*\n)')
ro_list = re.compile('\((?P<list>.*)\)')

class Manifest(object):
    def __init__(self, filename):
        self.targets = []
        self.read(filename)

    def __iter__(self):
        return iter(self.targets)

    def __bool__(self, x):
        if x.lower() in ('true', 'yes'):
            return True
        elif x.lower() in ('false', 'no'):
            return False
        return x

    def __read_definition__(self, txt, expand=True):
        args = {}
        # find all tags
        for match in ro_tag.finditer(txt):
            tag = match.group('tag')
            args[tag] = True
            txt = txt.replace(tag, '', 1)
        # find all arguments in long-form ...
        for match in ro_assign.finditer(txt):
            if not expand:
                value = match.group('value')
            elif ro_list.match(match.group('value')):
                value = ro_list.search(match.group('value')).group('list')
                value = tuple([x.strip('\'\" ') for x in value.split(',')])
            else:
                value = self.__bool__(match.group('value').strip('\'\"'))
            args[match.group('key')] = value
            txt = txt.replace(match.group('all'), '', 1)
        # ... and in short-form
        txt.strip()
        if txt:
            words = []
            for word in ro_word.finditer(txt):
                words.append(word.group(0) or word.group(1))
            if len(words) == 2:
                args['type'] = words[0]
                args['reference'] = words[1]
        return args

    def read(self, filename):
        if not os.path.isfile(filename):
            raise ValueError('File does not exist: %s' % str(filename))
        self.__filename__ = filename
        with open(filename) as fp:
            txt = fp.read()
        for match in ro_comment.finditer(txt):
            txt = txt.replace(match.group('comment'), '', 1)
        for match in ro_target.finditer(txt):
            path = match.group('target')
            snippet = match.group('definition')
            self.add_target(path, self.__read_definition__(snippet))

    def add_target(self, path, args={}):
        if path not in self.targets:
            self.targets.append(Target(path, **args))
        else:
            i = self.targets.index(path)
            self.targets[i].define(**args)

    def __repr__(self):
        return "Manifest('{0}')".format(self.__filename__)

    def echo(self):
        for target in self.targets:
            target.echo()
            print('')

    def update(self, source, properties=None):
        new = []
        for root, dirs, files in os.walk(source):
            root = os.path.realpath(root)
            if 'Makefile' in files:
                dirs = []
                if root not in self:
                    new.append(os.path.relpath(root))
                continue
            for name in files:
                if name.endswith(('.md', '.png', '.h', '.dat')):
                    continue
                path = root + '/' + name
                if path not in self:
                    new.append(os.path.relpath(path))
            prune = []
            for name in dirs:
                if name.startswith((core.botdir, '.git')):
                    prune.append(name)
                    continue
                path = os.path.realpath(root + '/' + name)
                makefile = path + '/Makefile'
                if os.path.exists(makefile):
                    if path not in self:
                        new.append(os.path.relpath(path))
                    prune.append(name)
            for x in prune:
                dirs.remove(x)
        if new:
            print('New targets:')
            for target in new:
                print('  ' + target)
        args = self.__read_definition__(properties, expand=False)
        with open(self.__filename__, 'a') as fp:
            for path in new:
                target = Target(path, **args)
                fp.write('\n' + target.format())
