#!/usr/bin/env python
"""Defines handler class for pre-commit hook."""

import argparse
import re
import shlex, subprocess
import sys

from SvnHook import *

class PreCommit(SvnHook):
    """Handles pre-commit hook calls."""

    def __init__(self):
        """Process the input arguments."""

        # Define how to process the command line.
        cmdline = argparse.ArgumentParser(
            description='Handle pre-commit hook calls.')

        cmdline.add_argument(
            '--cfgfile', required=True,
            help='Path name of the hook configuration file')

        cmdline.add_argument(
            'repospath', help='Path name of the repository root')
        cmdline.add_argument(
            'txnname', help='Name of the pending transaction')

        # Parse the command line. Save the arguments as attibutes.
        args = cmdline.parse_args()
        self.repospath    = args.repospath
        self.txnname      = args.txnname

        # Parse the STDIN lock tokens.
        self.locktokens = []
        intotokens = False
        for inline in sys.stdin.read():
            if intotokens and re.search(r'\S', inline):
                [path, name] = inline.split('|', 1)
                self.locktokens[path] = name
            elif re.match(r'LOCK-TOKENS:$', inline):
                intotoken = True

        # Perform parent initialization.
        super(PreCommit, self).__init__(args.cfgfile)

        # Enable hook-specific actions.
        self.actions['FilterAuthor'] = self.filter_authors
        self.actions['FilterLogMsg'] = self.filter_log_messages

    def get_author(self):
        """Get the transaction author."""

        # Look up the log message associated with the transaction.
        cmdline = 'svnlook author -t "{}" "{}"'.format(
            self.txnname, self.repospath)
        p = subprocess.Popen(shlex.split(cmdline),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=False)

        # The process started, wait for it to finish.
        p.wait()

        # Handle errors returned by the command.
        if p.returncode != 0:
            errstr = p.stderr.read()
            raise RuntimeError(
                'Command failed: {}: {}'.format(cmdline, errstr))

        # Get the regular output. Remove whitespace.
        return p.stdout.read().strip()

    def get_log_message(self):
        """Get the transaction log message."""

        # Look up the log message associated with the transaction.
        cmdline = 'svnlook log -t "{}" "{}"'.format(
            self.txnname, self.repospath)
        p = subprocess.Popen(shlex.split(cmdline),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=False)

        # The process started, wait for it to finish.
        p.wait()

        # Handle errors returned by the command.
        if p.returncode != 0:
            errstr = p.stderr.read()
            raise RuntimeError(
                'Command failed: {}: {}'.format(cmdline, errstr))

        # Get the regular output. Remove extra whitespace.
        return p.stdout.read().strip()

    #-----------------------------------------------------------------
    # Action Methods
    #-----------------------------------------------------------------

########################### end of file ##############################
