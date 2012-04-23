#!/usr/bin/env python
"""Defines SvnHook base class."""
__author__    = 'Geoff Rowell'
__copyright__ = 'Copyright 2012, Geoff Rowell'
__license__   = 'Apache'
__version__   = '3.00'
__status__    = 'Development'

import logging
import logging.config
import os
import re
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

    def run(self):
        raise Exception('Handler not implemented')

########################### end of file ##############################
