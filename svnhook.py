#!/usr/bin/env python
"""Base Class for Hook Handlers

Provides core Subversion hook handler functionality.
"""
__author__    = 'Geoff Rowell'
__copyright__ = 'Copyright 2012, Geoff Rowell'
__license__   = 'Apache'
__version__   = '3.00'
__status__    = 'Development'
__all__       = ['SvnHook']

from svnhook.filter import Filter

import logging
import logging.config
import os
import re
import yaml

from xml.etree.ElementTree import ElementTree

logger = logging.getLogger(__name__)

class SvnHook(object):
    """Base class for hook-specific handlers."""

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

        # Read and parse the hook configuration file.
        self.cfg = ElementTree(file=cfgfile)

        # Hang onto the context for use in the actions.
        self.context = context

    def run(self):
        """Execute top-level hook actions and set exit code."""
        # Construct a generic action list to perform the root hook
        # actions.
        exit(Filter(self.context, self.cfg.getroot()).run())

########################### end of file ##############################
