#!/usr/bin/env python
######################################################################
# Subversion Hook Framework Setup
######################################################################
import sys
from distutils.core import setup, Command

<<<<<<< HEAD
# Require Python 2.6+.
if sys.version_info < (2, 6):
    raise RuntimeError('Python 2.6+ required.')
=======
# Require Python 2.7+.
if sys.version_info < (2,7):
    raise RuntimeError('Python 2.7+ required.')
>>>>>>> origin/master

# "Run Unit Tests" Command
class UnitTest(Command):
    description = 'Discover and/or run unit tests.'
    user_options = [
        ('tests=', 't', 'comma-delimited test sets (default all)')]

    def initialize_options(self):
        self.tests = None
<<<<<<< HEAD
        if sys.version_info >= (2, 7):
            self.cmd = [sys.executable, '-m', 'unittest']
        else:
            self.cmd = ['unit2']

    def finalize_options(self):
        if not self.tests:
            self.cmd.append('discover')
            if sys.version_info < (2, 7):
                self.cmd += ['-s', 'test']
=======

    def finalize_options(self):
        if not self.tests: self.tests = 'discover'
>>>>>>> origin/master

    def run(self):
        import sys, subprocess

<<<<<<< HEAD
        if self.tests:
            for tests in self.tests.split(r','):
                self.cmd.append(tests)
        if self.verbose > 1: self.cmd.append('-v')

        errno = subprocess.call(self.cmd)
=======
        cmd = [sys.executable, '-m', 'unittest']
        for tests in self.tests.split(r','): cmd.append(tests)
        if self.verbose > 1: cmd.append('-v')

        errno = subprocess.call(cmd)
>>>>>>> origin/master
        raise SystemExit(errno)

# Subversion Hook Names
hooknames = [
    'post-commit',
    'post-lock',
    'post-revprop-change',
    'post-unlock',
    'pre-commit',
    'pre-lock',
    'pre-revprop-change',
    'pre-unlock',
    'start-commit',
]

# Package Parameters
setup(
    name='svnhook',
    version='3.00',
    author='Geoff Rowell',
    author_email='geoff.rowell@gmail.com',
    description='Subversion Hook Framework',
    url='https://github.com/growell/svnhook',
    download_url='git://github.com/growell/svnhook.git',
<<<<<<< HEAD
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Topic :: Software Development :: Version Control',
        ],
    packages=['svnhook'],
    scripts=['bin/svnhook-{0}'.format(h) for h in hooknames],
    data_files=[
        ('schema', ['schema/{0}.xsd'.format(h) for h in hooknames]),
        ],
    cmdclass={'test': UnitTest},
    requires=['argparse', 'yaml']
=======
    packages=['svnhook'],
    scripts=['bin/svnhook-{}'.format(h) for h in hooknames],
    data_files=[
        ('schema', ['schema/{}.xsd'.format(h) for h in hooknames]),
    ],
    cmdclass={'test': UnitTest},
>>>>>>> origin/master
)

########################### end of file ##############################
