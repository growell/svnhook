#!/usr/bin/env python
"""Handler Class for start-commit Hook"""

from svnhook import SvnHook
from svnhook.context import CtxStandard

import argparse
import logging
import os

logger = logging.getLogger(__name__)

class StartCommit(SvnHook):
    """Handler for start-commit Hook"""

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

########################### end of file ##############################
