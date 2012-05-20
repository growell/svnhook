#!/usr/bin/env python
"""Hook Handler Classes"""
__author__    = 'Geoff Rowell'
__copyright__ = 'Copyright 2012, Geoff Rowell'
__license__   = 'Apache'
__version__   = '3.00'
__status__    = 'Development'
__all__       = ['PostCommit', 'PreCommit', 'StartCommit']

from filters import Filter
from contexts import *

import argparse
import logging
import logging.config
import os, sys
import re
import yaml

from xml.etree.ElementTree import ElementTree, ParseError

logger = logging.getLogger()

class SvnHook(object):
    """Hook Handler Base Class"""

    def __init__(self, context, cfgfile):
        """Construct a new object of the class.

        Arguments:
        context -- Contextual information for hook processing.
        cfgfile -- Path name of hook configuration file.

        """
        if context == None:
            raise ValueError('Required argument missing: context')
        if cfgfile == None:
            raise ValueError('Required argument missing: cfgfile')
        if os.path.isfile(cfgfile) == False:
            raise IOError('Configuration file not found: '
                            + cfgfile)

        # If a co-located logging configuration file exists, use it.
        # Prefer a "*-log.yml" file over a "*-log.conf" file.
        logymlfile = re.sub(
            r'\.[^\.]+$', r'-log.yml', cfgfile)
        logconffile = re.sub(
            r'\.[^\.]+$', r'-log.conf', cfgfile)

        if os.path.isfile(logymlfile) == True:
            logcfg = yaml.load(open(logymlfile).read())
            logging.config.dictConfig(logcfg)
        elif os.path.isfile(logconffile) == True:
            logging.config.fileConfig(logconffile)
        else:
            logging.basicConfig()

        # For debugging, log the raw Python call.
        logger.debug('sys.argv: ' + ' '.join(sys.argv))

        # Read and parse the hook configuration file. If it has a
        # parse error, make sure to log it - before rethrowing it.
        try:
            self.cfg = ElementTree(file=cfgfile)
        except ParseError:
            logger.fatal(
                'Unable to parse hook configuration file!',
                exc_info=True)
            raise

        # Hang onto the context for use in the actions.
        self.context = context

    def run(self):
        """Execute top-level hook actions and set exit code."""
        # Construct a generic action list to perform the root hook
        # actions.
        exit(Filter(self.context, self.cfg.getroot()).run())

class StartCommit(SvnHook):
    """Start-Commit Hook Handler"""

    def __init__(self):

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

        # Parse the command line. Save the arguments as context
        # entries.
        args = cmdline.parse_args()

        # Construct the hook context. Initialize the tokens with
        # the available environment variables and the hook arguments.
        tokens = dict(os.environ)
        tokens['ReposPath']    = args.repospath
        tokens['User']         = args.user
        tokens['Capabilities'] = args.capabilities
        context = CtxStandard(tokens)

        # Perform parent initialization.
        super(StartCommit, self).__init__(context, args.cfgfile)

class PreCommit(SvnHook):
    """Pre-Commit Hook Handler"""

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

        # Parse the STDIN data.

        locktokens = []
        intotokens = False
        for inline in sys.stdin.read():
            if intotokens and re.search(r'\S', inline):
                locktokens.append(inline)
            elif re.match(r'LOCK-TOKENS:$', inline):
                intotoken = True

        # Construct the hook context.
        tokens = dict(os.environ)
        tokens['ReposPath']   = args.repospath
        tokens['Transaction'] = args.txnname
        tokens['LockTokens']  = locktokens
        context = CtxTransaction(tokens)

        # Perform parent initialization.
        super(PreCommit, self).__init__(context, args.cfgfile)

class PostCommit(SvnHook):
    """Post-Commit Hook Handler"""

    def __init__(self):

        # Define how to process the command line.
        cmdline = argparse.ArgumentParser(
            description='Handle post-commit hook calls.')

        cmdline.add_argument(
            '--cfgfile', required=True,
            help='Path name of the hook configuration file')

        cmdline.add_argument(
            'repospath', help='Path name of the repository root')
        cmdline.add_argument(
            'revision', help='Number of the completed revision')

        # Parse the command line.
        args = cmdline.parse_args()

        # Construct the hook context.
        tokens = dict(os.environ)
        tokens['ReposPath'] = args.repospath
        tokens['Revision']  = args.revision
        context = CtxRevision(tokens)

        # Perform parent initialization.
        super(PostCommit, self).__init__(context, args.cfgfile)

########################### end of file ##############################
