#!/usr/bin/env python
"""Pre-commit Hook Handler Class

Defines the hook-specific logic needed to handle pre-commit hook
requests.
"""
__version__ = '3.00'
__all__     = ['PreCommit']

import argparse
import re
import sys

from svnhook import SvnHook

class PreCommit(SvnHook):
    """Handle pre-commit hook calls."""

    def __init__(self):

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

        # Parse the command line.
        args = cmdline.parse_args()

        # Parse the STDIN lock tokens.
        locktokens = []
        intotokens = False
        for inline in sys.stdin.read():
            if intotokens and re.search(r'\S', inline):
                [path, name] = inline.split('|', 1)
                locktokens[path] = name
            elif re.match(r'LOCK-TOKENS:$', inline):
                intotoken = True

        ### MHL: What to do with lock tokens?

        # Construct the hook context.
        tokens = dict(os.environ)
        tokens['ReposPath']   = args.repospath
        tokens['Transaction'] = args.txnname
        context = CtxTransaction(tokens)

        # Perform parent initialization.
        super(PreCommit, self).__init__(context, args.cfgfile)

########################### end of file ##############################
