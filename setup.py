#!/usr/bin/env python
######################################################################
# Subversion Hook Framework Setup
######################################################################
from distutils.core import setup, Command

class UnitTest(Command):
    description = 'Discover and/or run unit tests.'
    user_options = [
        ('tests=', 't', 'comma-delimited test sets (default all)')]

    def initialize_options(self):
        self.tests = None

    def finalize_options(self):
        if not self.tests: self.tests = 'discover'

    def run(self):
        import sys, subprocess

        cmd = [sys.executable, '-m', 'unittest']
        for tests in self.tests.split(r','): cmd.append(tests)
        if self.verbose > 1: cmd.append('-v')

        errno = subprocess.call(cmd)
        raise SystemExit(errno)

config = {
    'description': 'Subversion Hook Framework',
    'author': 'Geoff Rowell',
    'url': 'http://sourceforge.net',
    'download_url': 'http://github.com',
    'author_email': 'geoff.rowell@gmail.com',
    'version': '3.00',
    'packages': ['svnhook'],
    'scripts': [],
    'name': 'svnhook',
    'cmdclass': {'test': UnitTest},
}

setup(**config)
########################### end of file ##############################
