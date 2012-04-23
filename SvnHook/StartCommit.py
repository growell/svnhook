#!/usr/bin/env python

import argparse
from SvnHook import *

class StartCommit(SvnHook):
    """Handles start-commit hook calls."""

    def __init__(self):
        """Process the input arguments."""

        # Define how to process the command line.
        cmdline = argparse.ArgumentParser(
            description='Handle start-commit hook calls.')

        cmdline.add_argument(
            '--cfgfile', required=True,
            help='Path name of the hook configuration file')

        cmdline.add_argument(
            'repospath', help='Path name of the repository root')
        cmdline.add_argument(
            'user', help='Name of the Subversion user')
        cmdline.add_argument(
            'capabilities', help='List of client capabilities')

        args = cmdline.parse_args()
        
        # Perform parent initialization.
        super(StartCommit, self).__init__(args.cfgfile)

    def run(self):
        raise Exception('Found the handler')
