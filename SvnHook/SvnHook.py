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
import smtplib
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

    # Action Methods
    action_methods = (
        'set_token',
        'send_error',
        'send_smtp',
        'execute_cmd')

    def __init__(self, cfgfile):
        """Construct a new object of the class.

        Arguments:
        cfgfile -- Path name of hook configuration file.

        """
        if cfgfile == False:
            raise KeyError('Required argument missing: cfgfile')
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
        self.cfg = etree.parse(open(cfgfile))

        # Set dictionary of action methods.
        self.actions = {
            'SetToken':   self.set_token,
            'SendError':  self.send_error,
            'SendSmtp':   self.send_smtp,
            'ExecuteCmd': self.execute_cmd}

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
        # Make sure it's a valid handler.
        try:
            handler = self.actions[action.tag]
        except KeyError:
            raise RuntimeError(
                'Action not recognized: ' + action.tag)

        # Call the action method. Pass it the configuration
        # element.
        logging.debug('Calling {}...'.format(handler.__name__))
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
    # Base Action Methods
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
        if action.text == None:
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

    def send_smtp(self, action):
        """Send a mail message."""

        # Get the SMTP server host name.
        try:
            host = self.apply_tokens(action.attrib['server'])
        except KeyError:
            raise RuntimeError(
                'Required attribute missing: server')

        # Get the maximum number of connect seconds.
        try:
            timeout = int(action.get('seconds', default=60))
        except ValueError:
            raise ValueError('Illegal seconds attribute: {}'
                             .format(action.get('seconds')))

        # Get the from email address.
        fromtag = action.find('FromAddress')
        if fromtag == None:
            raise RuntimeError(
                'Required tag missing: FromAddress')
        fromaddress = self.apply_tokens(fromtag.text)
        
        # Get the recipient email addresses.
        toaddresses = []
        for totag in action.findall('ToAddress'):
            toaddresses.append(self.apply_tokens(totag.text))
        if len(toaddresses) == 0:
            raise RuntimeError(
                'Required tag missing: ToAddress')

        # Get the message subject line.
        subjecttag = action.find('Subject')
        if subjecttag == None:
            raise RuntimeError(
                'Required tag missing: Subject')
        subject = self.apply_tokens(subjecttag.text)

        # Get the message body.
        messagetag = action.find('Message')
        if messagetag == None:
            raise RuntimeError(
                'Required tag missing: Message')
        message = self.apply_tokens(messagetag.text)

        # Assemble the message content.
        content = 'From: {}\r\n'.format(fromaddress)
        for toaddress in toaddresses:
            content += 'To: {}\r\n'.format(toaddress)
        content += 'Subject: {}\r\n'.format(subject)

        content += '\r\n'
        for msgline in message.splitlines():
            content += '{}\r\n'.format(msgline)

        # Construct the SMTP connection.
        try:
            server = smtplib.SMTP(host, None, None, timeout)
        except SMTPConnectError as e:
            logging.critical(e)
            sys.stderr.write('Internal hook error.'
                             + ' Please notify administrator.')
            self.exitcode = -1
            return

        # Send the message.
        try:
            server.sendmail(fromaddress, toaddresses, content)
        except smtplib.SMTPRecipientsRefused as e:
            for recipient in e.recipients:
                logging.warning(
                    'Recipient refused: {}'.format(recipient))

        # Disconnect from the host.
        server.quit()

    def execute_cmd(self, action):
        """Execute a system command line."""
        if action.text == None:
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

    #-----------------------------------------------------------------
    # Filter Actions
    #-----------------------------------------------------------------

    def filter_users(self, action):
        """Filters operations based on user name."""
        # Get the user name regex tag.
        regextag = action.find('UserRegex')
        if regextag == None:
            raise RuntimeError(
                'Required tag missing: UserRegex')

        # Avoid tag reuse.
        action.remove(regextag)
        
        # Extract the comparison details.
        if regextag.text == None or regextag.text == '':
            raise RuntimeError(
                'Required tag content missing: UserRegex')

        regex = re.compile(r'(?i).*' + regextag.text + r'.*')
        sense = re.match(r'(?i)(1|true|yes)',
                         regextag.get('sense', default='true'))!=None

        # Apply the regex to the user name string.
        if sense:
            result = regex.match(self.user)!=None
        else:
            result = regex.match(self.user)==None
        if result == False: return

        # Perform the child actions.
        for subaction in action.iterfind(r'./*'):
            self.execute_action(subaction)
            if self.exitcode != 0: break
        
########################### end of file ##############################
