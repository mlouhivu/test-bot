import re
import os
from copy import deepcopy

from testbot.build import Compiler
from testbot.build import Linker

runner = 'srun'
compute_node = True

ro_block = re.compile('\[\s*(?P<name>[^]]+)\s*\](?P<definition>[^[]*)')
ro_lang = re.compile('(?P<all>\(\s*(?P<language>[^)+\s]*)\s*'
        + '(?P<tags>[^)]*)\s*\)(?P<definition>[^[(]*))')
ro_assign = re.compile('(?P<all>(?P<key>[a-zA-Z0-9_.-]+)(?P<plus>\+?)='
        + '''(?P<value>["'].*["']|[a-zA-Z0-9_./-]+))''')
ro_tag = re.compile('\s*\+(?P<tag>\w+)')
ro_comment = re.compile('(^|\n)\s*(?P<comment>#[^\n]*\n)')

class Config(object):
    def __init__(self, filename):
        self.targets = []
        self.__builder__ = {}
        self.mpi_tasks = None
        self.omp_threads = None
        self.read(filename)
        self.check()

    def __find_args__(self, txt):
        args = {}
        for m in ro_assign.finditer(txt):
            args[m.group('key')] = m.group('value')
        return args

    def read(self, filename):
        if not os.path.isfile(filename):
            raise ValueError('File does not exist: %s' % str(filename))
        self.__filename__ = filename
        with open(filename) as fp:
            txt = fp.read()
        for match in ro_comment.finditer(txt):
            txt = txt.replace(match.group('comment'), '', 1)
        for match in ro_block.finditer(txt):
            family = match.group('name')
            section = match.group('definition')
            # find language / flavour specific arguments first ..
            languages = {}
            for m in ro_lang.finditer(section):
                lang = m.group('language') or ''
                tags = tuple(sorted(ro_tag.findall(m.group('tags')))) or ()
                snippet = m.group('definition')
                languages.setdefault(lang, {})
                languages[lang][tags] = self.__find_args__(snippet)
                section = section.replace(m.group('all'), '', 1)
            # .. and then default arguments
            default = self.__find_args__(section)
            self.__lang__ = (languages)
            self.__default__ = deepcopy(default)
            self.__section__ = deepcopy(section)
            # sort out arguments for different languages and flavours
            self.__builder__[family] = {(None,): default}
            for lang in sorted(languages.keys()):
                for tags in sorted(languages[lang].keys()):
                    key = (lang,)
                    if tags:
                        key += tags
                    if (lang,) in self.__builder__[family]:
                        args = deepcopy(self.__builder__[family][(lang,)])
                    else:
                        args = deepcopy(default)
                    args.update(languages[lang][tags])
                    self.__builder__[family][key] = args

    def check(self):
        for family in self.__builder__:
            for key in self.__builder__[family]:
                for opt in ['compiler']:
                    if opt not in self.__builder__[family][key]:
                        raise KeyError('Missing build option in ' \
                                + '{0} {1}: {2}'.format(family, key, opt))

    def __build_args__(self, family='gnu', language='c', flavours=None):
        key = (language,)
        if flavours:
            key += tuple(flavours)
        try:
            if key in self.__builder__[family]:
                return self.__builder__[family][key]
            else:
                return self.__builder__[family][(language,)]
        except KeyError:
            try:
                return self.__build_args__(family, None, flavours)
            except ValueError:
                raise ValueError('Unknown compiler: {0} {1} {2}'.format(
                        family, language, flavours))

    def compiler(self, family='gnu', language='c', flavours=None, link=True):
        args = self.__build_args__(family, language, flavours)
        opts = {'link': link}
        if 'compile-options' in args:
            opts['options'] = args['compile-options']
        for key in ['output']:
            if key in args:
                opts[key] = args[key]
        return Compiler(args['compiler'], **opts)

    def linker(self, family='gnu', language='c', flavours=None):
        args = self.__build_args__(family, language, flavours)
        opts = {}
        if 'link-options' in args:
            opts['options'] = args['link-options']
        for key in ['output', 'libraries']:
            if key in args:
                opts[key] = args[key]
        return Linker(args['compiler'], **opts)
