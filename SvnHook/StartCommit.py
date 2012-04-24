#!/usr/bin/env python
"""Defines handler class for start-commit hook."""

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

        # Parse the command line. Save the arguments as attibutes.
        args = cmdline.parse_args()
        self.repospath    = args.repospath
        self.user         = args.user
        self.capabilities = args.capabilities
        
        # Perform parent initialization.
        super(StartCommit, self).__init__(args.cfgfile)

        # Define the additional actions.
        self.actions['FilterCapabilities'] = self.filter_capabilities
        self.actions['FilterUser'] = self.filter_users

    #-----------------------------------------------------------------
    # Action Methods
    #-----------------------------------------------------------------

    def filter_capabilities(self, cfgtag):
        """Filters based on client capabilities."""

        logging.debug('capabilities ="{}"'.format(self.capabilities))

        # Find the required regex element.
        regextag = cfgtag.find('CapabilitiesRegex')

        if regextag==None:
            raise NameError('Required tag missing: CapabilitiesRegex')
        elif regextag.text==None:
            raise ValueError(
                'Required tag content missing: CapabilitiesRegex')

        # Prevent re-use of the regex element.
        cfgtag.remove(regextag)

        # Get the regex parameters. The capability items are
        # delimited by colons. The regular expression is sloppy
        # - i.e. it doesn't need to match the whole string.
        regex = re.compile(
            r'(?:.+\:)?' + regextag.text + r'(?:\:.+|$)')
        sense = re.match(r'(?i)(1|true|yes)',
                         regextag.get('sense', default='true'))!=None

        # Apply the regex to the capabilities string.
        if sense:
            result = regex.match(self.capabilities)!=None
        else:
            result = regex.match(self.capabilities)==None
        if result==False: return

        # Perform the child actions.
        for action in cfgtag.iterfind(r'./*'):
            self.execute_action(action)
            if self.exitcode != 0: break

########################### end of file ##############################
