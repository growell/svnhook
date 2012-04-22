#!/usr/bin/env python
import logging
import logging.config

from lxml import etree

class SvnHook(object):
    """Base class for hook-specific handlers."""

    logger = logging.getLogger(__name__)

    def __init__(self, **args):
        """Construct a new object of the class."""
        
        # Initialize logging.
        logging.config.fileConfig(args['logcfgfile'])

        # Read and parse the hook configuration file.
        cfg = open(args['hookcfgfile'])
        self.cfg = etree.parse(cfg)

    def run(self):
        raise Exception('Handler not implemented')

########################### end of file ##############################
