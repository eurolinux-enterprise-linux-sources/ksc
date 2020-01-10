#!/usr/bin/env python
"""ksc"""
from distutils.core import setup
from distutils.core import Command
from unittest import TextTestRunner, TestLoader
import os


class TestCommand(Command):
    user_options = [ ]

    def initialize_options(self):
        self._dir = os.getcwd()

    def finalize_options(self):
        pass

    def run(self):
        '''
        Finds all the tests modules in tests/, and runs them.
        '''
        testfiles = ['tests']
        #for t in glob(pjoin(self._dir, 'tests', '*.py')):
        #    if not t.endswith('__init__.py'):
        #        testfiles.append('.'.join(
        #            ['tests', splitext(basename(t))[0]])
        #        )

        tests = TestLoader().loadTestsFromNames(testfiles)
        t = TextTestRunner(verbosity = 1)
        t.run(tests)

data = []
for x in os.listdir('data/'):
    if x in ['ksc.conf','test.c']:
        continue
    elif x.startswith('kabi_whitelist_'):
        continue
    else:
        data.append('data/%s' % x)

setup(name='ksc',
      version='0.9.5',
      description="ksc tool",
      long_description = "Kernel Module Source Checker tool",
      cmdclass = { 'test': TestCommand},
      platforms = ["Linux"],
      author="Kushal Das",
      author_email="kdas@redhat.com",
      url="http://redhat.com",
      license = "http://www.gnu.org/copyleft/gpl.html",
      data_files=[("/usr/bin",['ksc']),
          ('/etc', ['data/ksc.conf']),
          ('/usr/share/ksc',['ksc.py','keywords.py','utils.py']),
          ('/usr/share/ksc/data', data),
          ('/usr/share/ksc/bz_xmlrpc', ['bz_xmlrpc/__init__.py','bz_xmlrpc/base.py','bz_xmlrpc/classes.py', 'bz_xmlrpc/settings.py', 'bz_xmlrpc/utils.py'])],

      )
