#!/usr/bin/env python
"""Base Class for Hook Handlers"""
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
import shlex, subprocess
import sys
import textwrap
import yaml

from lxml import etree
from string import Template

class SvnHook(object):
    """Base class for hook-specific handlers.

    Initializes logging.
    Reads and parses XML configuration.
    Defines base hook actions.
    """

    # Infrastructure Methods
    non_action_methods = (
        '__init__',
        'run',
        'execute_action',
        'apply_tokens')

    def __init__(self, cfgfile):
        """Construct a new object of the class.

        Arguments:
        cfgfile -- Path name of hook configuration file.

        """
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
        for m in SvnHook.non_action_methods: del self.handlers[m]

        # Initialize the token set with the current environment
        # variables.
        self.tokens = dict(os.environ)

        # Initialize the hook exit code.
        self.exitcode = 0

    def run(self):
        """Execute top-level hook actions and set exit code."""
        # Perform the hook actions.
        for action in self.cfg.getroot().iterfind(r'./*'):
            self.execute_action(action)
            if self.exitcode != 0: break

        # Exit with the final exit code.
        exit(self.exitcode)

    def execute_action(self, action):
        """Execute a hook handler action.

        Arguments:
        action -- Element object for action tag.

        """
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

    def apply_tokens(self, template):
        """Apply tokens to a template string.

        Arguments:
        template -- String containing tokens.

        Returns:
        Template string with token substitutions.

        """
        engine = Template(template)
        return engine.safe_substitute(self.tokens)

    #-----------------------------------------------------------------
    # Action Methods
    #-----------------------------------------------------------------

    def set_token(self, action):
        """Set a token to be used in template substitutions."""
        try:
            name = action.attrib['name']
        except KeyError:
            raise RuntimeError(
                'Required attribute missing: name')

        # Set the token value.
        self.tokens[name] = action.text or ''

    def send_error(self, action):
        """Send a STDERR message to Subversion and set exit code."""
        if action.text==None:
            raise RuntimeError(
                'Required tag content missing: SendError')

        # Trim leading whitespace from the error message. Apply any
        # tokens.
        errormsg = self.apply_tokens(textwrap.dedent(
                re.sub(r'(?s)^[\n\r]+', '', action.text)))

        # Log the error message lines.
        for e in errormsg.splitlines(): logging.error(e.lstrip())

        # Send the message to STDERR and use the exit code.
        sys.stderr.write(errormsg)

        # Set the non-zero exit code.
        try:
            self.exitcode = int(action.get('exitCode', default=1))
        except ValueError:
            self.exitcode = -1

    def execute_cmd(self, action):
        """Execute a system command line."""
        if action.text==None:
            raise RuntimeError(
                'Required tag content missing: ExecuteCmd')

        # Apply tokens to the command line.
        cmdline = self.apply_tokens(action.text)

        # Get the minimum exit code needed to signal a hook failure.
        errorlevel = int(action.get('errorLevel', default=1))

        # Execute the tokenized system command. If the process fails
        # to start, it'll throw an OSError. Treat that as a
        # non-maskable hook failure.
        logging.debug('cmdline = "{}", errorlevel = {}'
                      .format(cmdline, errorlevel))

        try:
            p = subprocess.Popen(shlex.split(cmdline),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=False)
        except OSError as e:
            logging.critical(e)
            sys.stderr.write('Internal hook error.'
                             + ' Please notify administrator.\n')
            self.exitcode = -1
            return

        # The process started, wait for it to finish.
        p.wait()

        # Compare the process exit code to the error level.
        if p.returncode >= errorlevel:
            errstr = p.stderr.read()
            sys.stderr.write(errstr)
            logging.error(errstr)
            self.exitcode = p.returncode
        else:
            logging.debug('exit code = {}'.format(p.returncode))

########################### end of file ##############################
