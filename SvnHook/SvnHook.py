#!/usr/bin/env python
"""Defines SvnHook base class."""
__author__    = 'Geoff Rowell'
__copyright__ = 'Copyright 2012, Geoff Rowell'
__license__   = 'Apache'
__version__   = '3.00'
__status__    = 'Development'

import inspect
import logging
import logging.config
import os
import re
import sys
import textwrap
import yaml

from lxml import etree

class SvnHook(object):
    """Base class for hook-specific handlers.

    Initializes logging. Reads and parses XML configuration.
    """

    def __init__(self, cfgfile):
        """Construct a new object of the class."""

        if cfgfile==False:
            raise KeyError('Required argument missing: cfgfile')
        if os.path.isfile(cfgfile)==False:
            raise IOError('Configuration file not found: '
                            + cfgfile)

        # If a co-located logging configuration file exists, use it.
        # Prefer a "*-log.yml" file over a "*-log.conf" file.
        logymlfile = re.sub(
            r'\.[^\.]+$', r'-log.yml', cfgfile)
        logconffile = re.sub(
            r'\.[^\.]+$', r'-log.conf', cfgfile)

        if os.path.isfile(logymlfile)==True:
            logcfg = yaml.load(open(logymlfile).read())
            logging.config.dictConfig(logcfg)
        elif os.path.isfile(logconffile)==True:
            logging.config.fileConfig(logconffile)
        else:
            logging.basicConfig()

        # Read and parse the hook configuration file.
        self.cfg = etree.parse(open(cfgfile))

        # Get the known action handler methods.
        self.handlers = dict(
            inspect.getmembers(self, predicate=inspect.ismethod))
        del self.handlers['__init__']
        del self.handlers['run']
        del self.handlers['execute_action']

        # Initialize the hook exit code.
        self.exitcode = 0

    def run(self):
        """Executes all top-level actions in hook configuration."""

        # Perform the hook actions.
        for action in self.cfg.getroot().iterfind(r'./*'):
            self.execute_action(action)

        # Exit with the final exit code.
        exit(self.exitcode)

    def execute_action(self, action):
        """Executes single hook handler action."""

        # Convert the mixed-case tag name into an underscored,
        # lower case, method name.
        tomethod = lambda pat: \
            pat.group(1) + '_' + pat.group(2).lower()
        method = re.sub(
            r'([a-z])([A-Z])', tomethod, action.tag).lower()

        # Make sure it's a valid handler.
        if method not in self.handlers:
            raise RuntimeError(
                'Action method not found: ' + method)
        handler = self.handlers[method]

        # Call the action method. Pass it the configuration
        # element.
        logging.debug('Calling {}...'.format(method))
        handler(action)

    def send_error(self, action):
        """Sends an error to Subversion.

        Emits an error message to STDERR and sets a non-zero exit
        code. For "pre-" hooks, this may abort a Subversion activity.
        """

        if action.text==None:
            raise RuntimeError(
                'Required tag content missing: SendError')

        # Trim leading whitespace from the error message.
        errormsg = textwrap.dedent(
            re.sub(r'(?s)^[\n\r]+', '', action.text))

        # Log the error message lines.
        for e in errormsg.splitlines(): logging.error(e.lstrip())

        # Send the message to STDERR and use the exit code.
        sys.stderr.write(errormsg)

        # Set the non-zero exit code.
        try:
            self.exitcode = int(action.get('exitCode', default=1))
        except ValueError:
            self.exitcode = -1

########################### end of file ##############################
