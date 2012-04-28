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

from xml.etree.ElementTree import ElementTree
from string import Template
from svnhook.RegexTag import RegexTag

class SvnHook(object):
    """Base class for hook-specific handlers."""

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

        # Initialize the logger with the instance class name.
        self.logger = logging.getLogger(self.__class__.__name__)

        # Read and parse the hook configuration file.
        self.cfg = ElementTree(file=cfgfile)

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

        # Perform the root hook actions.
        self.run_actions(self.cfg.getroot())

        # Exit with the final exit code.
        exit(self.exitcode)

    def run_actions(self, parent):
        """Execute child tag actions."""
        for action in parent.iterfind(r'./*'):

            # Make sure it's a valid handler.
            try:
                handler = self.actions[action.tag]
            except KeyError:
                raise RuntimeError(
                    'Action not recognized: ' + action.tag)

            # Call the action method. Pass it the configuration
            # element.
            self.debug('Calling {}...'.format(handler.__name__))
            handler(action)

            # If the handler set an exit code, stop executing the
            # hook actions.
            if self.exitcode != 0: break

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
    # Logging Utility Methods
    #-----------------------------------------------------------------
    def debug(self, msg, *args, **kwargs):
        """Log a message with severity DEBUG on the hook logger."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log a message with severity INFO on the hook logger."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log a message with severity WARNING on the hook logger."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log a message with severity ERROR on the hook logger."""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log a message with severity CRITICAL on the hook logger."""
        self.logger.critical(msg, *args, **kwargs)

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
        for e in errormsg.splitlines(): self.error(e.lstrip())

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
            self.critical(e)
            sys.stderr.write('Internal hook error.'
                             + ' Please notify administrator.')
            self.exitcode = -1
            return

        # Send the message.
        try:
            server.sendmail(fromaddress, toaddresses, content)
        except smtplib.SMTPRecipientsRefused as e:
            for recipient in e.recipients:
                self.warning(
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
        self.debug('cmdline="{}", errorlevel={}'
                      .format(cmdline, errorlevel))

        try:
            p = subprocess.Popen(shlex.split(cmdline),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=False)
        except OSError as e:
            self.critical(e)
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
            self.error(errstr)
            self.exitcode = p.returncode
        else:
            self.debug('exit code={}'.format(p.returncode))

    #-----------------------------------------------------------------
    # Filter Actions
    #-----------------------------------------------------------------

    def filter_authors(self, action):
        """Filter operations based on author (user) name."""

        # Get the user name regex tag.
        regextag = action.find('AuthorRegex')
        if regextag == None:
            raise RuntimeError(
                'Required tag missing: AuthorRegex')

        # Avoid tag reuse.
        action.remove(regextag)

        # Extract the comparison details.
        regex = RegexTag(regextag, re.IGNORECASE)

        # Get the current author.
        try:
            author = self.get_author()
        except AttributeError:
            raise RuntimeError(
                'Author not available for this hook type.')

        # Apply the regex to the user name string.
        if not regex.search(author): return

        # Set the author name token.
        self.tokens['AUTHOR'] = author

        # Perform the child actions.
        self.run_actions(action)

    def filter_changes(self, action):
        """Filter actions based on changes."""

        # Get the change path regex.
        pathregextag = action.find('ChgPathRegex')
        if pathregextag == None:
            pathregex = None
        else:
            action.remove(pathregextag)
            pathregex = RegexTag(pathregextag)

        # Get the change type regex.
        typeregextag = action.find('ChgTypeRegex')
        if typeregextag == None:
            typeregex = None
        else:
            action.remove(typeregextag)
            typeregex = RegexTag(typeregextag, re.IGNORECASE)

        # Require at least one regex tag.
        if typeregex == None and pathregex == None:
            raise RuntimeError(
                'Required tag missing: ChgPathRegex or ChgTypeRegex')

        # Get the dictionary of changes.
        try:
            changes = self.get_changes()
        except AttributeError:
            raise RuntimeError(
                'Changes not available for this hook type.')

        # Compare the changes to the regular expressions.
        for [chgpath, chgtype] in changes:
            pass

    def filter_log_messages(self, action):
        """Filter actions based on log message."""

        # Get the log message regex tag.
        regextag = action.find('LogMsgRegex')
        if regextag == None:
            raise RuntimeError(
                'Required tag missing: LogMsgRegex')

        # Avoid tag reuse.
        action.remove(regextag)
        
        # Extract the comparison details.
        regex = RegexTag(regextag)

        # Get the current log message.
        try:
            logmsg = self.get_log_message()
        except AttributeError:
            raise RuntimeError(
                'Log message not available for this hook type.')

        # Apply the regex to the log message.
        if not regex.search(logmsg): return

        # Set the log message token.
        self.tokens['LOGMSG'] = logmsg

        # Perform the child actions.
        self.run_actions(action)

    def filter_users(self, action):
        """Filter operations based on user name."""

        # Get the user name regex tag.
        regextag = action.find('UserRegex')
        if regextag == None:
            raise RuntimeError(
                'Required tag missing: UserRegex')

        # Avoid tag reuse.
        action.remove(regextag)
        
        # Extract the comparison details.
        regex = RegexTag(regextag, re.IGNORECASE)

        # Apply the regex to the user name string.
        if not regex.search(self.user): return

        # Set the user name token.
        self.tokens['USER'] = self.user

        # Perform the child actions.
        self.run_actions(action)

########################### end of file ##############################
