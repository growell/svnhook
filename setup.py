#!/usr/bin/env python
######################################################################
# Subversion Hook Framework Setup
######################################################################
from distutils.core import setup, Command

class UnitTest(Command):
    description = 'Discover and run unit tests.'
    user_options = [(
            'verbose', 'v', 'display verbose test output')]
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import sys, subprocess
        cmd = [sys.executable, '-m', 'unittest', 'discover']
        if self.verbose: cmd.append('-v')
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
