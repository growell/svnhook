"""Subversion Hook Action Classes

Provide classes that handle non-filtering hook actions.
"""
__version__ = '3.00'
__all__     = ['Action', 'ExecuteCmd', 'SendError', 'SendLogSmtp',
               'SendSmtp', 'SetRevisionFile', 'SetToken']

import logging
import re
import smtplib
import sys, subprocess, shlex
import textwrap

logger = logging.getLogger()

class Action(object):

    def __init__(self, context, thistag):
        self.context = context
        self.thistag = thistag

    def expand(self, text):
        """Use current context to expand a string.

        Args:
          text: String to be expanded.

        Returns: Original string with tokens replaced.
        """
        return self.context.expand(text)

    def get_boolean(self, name, default=False):
        """Evaluate a boolean attribute of this tag.

        Args:
          name: Name of the attribute.
          default: State to assume when attribute not present.

        Returns: Effective boolean value of the attribute.
        """
        # Determine the default string value.
        if default: default = '1'
        else: default = '0'

        # Evaluate the attribute.
        return re.match(r'(1|true|yes)$',
                        self.thistag.get(name, default),
                        re.IGNORECASE) != None

class SetToken(Action):

    def __init__(self, *args, **kwargs):
        super(SetToken, self).__init__(*args, **kwargs)

        # Get the token name.
        try:
            self.name = self.thistag.attrib['name']
        except KeyError:
            raise ValueError(
                'Required attribute missing: name')

        # Get the token value.
        self.value = self.thistag.text or ''

    def run(self):
        """Set a token to be used in template substitutions.

        Returns: Exit code (zero) of the action.
        """
        # Set the token from the raw value.
        self.context.tokens[self.name] = self.value

        # Indicate a non-terminal action.
        return 0

class SendError(Action):

    def __init__(self, *args, **kwargs):
        super(SendError, self).__init__(*args, **kwargs)

        # Get the non-zero exit code.
        self.exitcode = int(self.thistag.get('exitCode', default=1))
        if self.exitcode == 0:
            raise ValueError(
                'Not a valid error exit code: exitCode')

        # Trim leading whitespace from the error message.
        if self.thistag.text == None:
            raise ValueError(
                'Required tag content missing: SendError')
        self.errormsg = textwrap.dedent(
                re.sub(r'(?s)^[\n\r]+', '', self.thistag.text))

    def run(self):
        """Send a STDERR message to Subversion.

        Returns: Exit code (non-zero) of the action.
        """
        # Apply any tokens.
        errormsg = self.expand(self.errormsg)

        # Log the error message lines.
        for e in errormsg.splitlines(): logger.error(e.lstrip())

        # Output the client message.
        sys.stderr.write(errormsg)

        # Return the terminal (non-zero) exit code.
        return self.exitcode

class _SendSmtp(Action):
    """SMTP Transmission Virtual Class"""

    def __init__(self, *args, **kwargs):
        super(_SendSmtp, self).__init__(*args, **kwargs)

        # Get the SMTP server host name and port number.
        try:
            self.host = self.thistag.attrib['server']
        except KeyError:
            self.host = 'localhost'

        try:
            self.port = self.thistag.attrib['port']
        except KeyError:
            self.port = None

        # Get the maximum number of connect seconds.
        try:
            self.timeout = int(
                self.thistag.get('seconds', default=60))
        except ValueError:
            raise ValueError('Illegal seconds attribute: {}'
                             .format(self.thistag.get('seconds')))

        # Get the from email address.
        fromtag = self.thistag.find('FromAddress')
        if fromtag == None:
            raise ValueError(
                'Required tag missing: FromAddress')
        self.fromaddress = fromtag.text
        
        # Get the recipient email addresses.
        self.toaddresses = []
        for totag in self.thistag.findall('ToAddress'):
            self.toaddresses.append(totag.text)
        if len(self.toaddresses) == 0:
            raise ValueError(
                'Required tag missing: ToAddress')

        # Get the message subject line.
        subjecttag = self.thistag.find('Subject')
        if subjecttag == None:
            raise ValueError(
                'Required tag missing: Subject')
        self.subject = subjecttag.text

    def run(self):
        """Send a mail message.

        Returns: Exit code (zero) of the action.
        """
        # Expand the message details
        host = self.expand(self.host)
        if self.port:
            port = self.expand(self.port)
        else:
            port = None
        fromaddress = self.expand(self.fromaddress)

        toaddresses = []
        for address in self.toaddresses:
            toaddresses.append(self.expand(address))

        subject = self.expand(self.subject)

        # Get the message body from a derived class.
        message = self.getMessage()

        # Assemble the message content.
        content = 'From: {}\r\n'.format(fromaddress)
        for toaddress in toaddresses:
            content += 'To: {}\r\n'.format(toaddress)
        content += 'Subject: {}\r\n'.format(subject)

        content += '\r\n'
        for msgline in message.splitlines():
            content += '{}\r\n'.format(msgline)

        # Construct the SMTP connection.
        server = smtplib.SMTP(host, port, None, self.timeout)

        # Send the message. Log warnings for unknown recipients.
        try:
            server.sendmail(fromaddress, toaddresses, content)
        except smtplib.SMTPRecipientsRefused as e:
            for recipient in e.recipients:
                logger.warning(
                    'Recipient refused: {}'.format(recipient))

        # Disconnect from the host.
        server.quit()

        # Indicate a non-terminal action.
        return 0

class SendSmtp(_SendSmtp):

    def __init__(self, *args, **kwargs):
        super(SendSmtp, self).__init__(*args, **kwargs)

        # Get the message body template.
        messagetag = self.thistag.find('Message')
        if messagetag == None:
            raise ValueError(
                'Required tag missing: Message')
        self.message = messagetag.text

    def getMessage(self):
        """Get the message body from the expanded tag content.

        Returns: Multi-line message, provided as tag content, with
        tokens expanded.
        """
        return self.expand(self.message)

class SendLogSmtp(_SendSmtp):

    def __init__(self, *args, **kwargs):
        super(SendLogSmtp, self).__init__(*args, **kwargs)

        # Get the verbose format flag.
        self.verbose = self.get_boolean('verbose', default=True)

    def getMessage(self):
        """Get the log entry for the current revision.

        Returns: Formatted log entry associated with the current
        revision.
        """
        return self.context.get_log(verbose=self.verbose)

class ExecuteCmd(Action):

    def __init__(self, *args, **kwargs):
        super(ExecuteCmd, self).__init__(*args, **kwargs)

        # Get the command line.
        if self.thistag.text == None:
            raise ValueError(
                'Required tag content missing: ExecuteCmd')
        self.cmdline = self.thistag.text

        # Get the minimum exit code needed to signal a hook failure.
        self.errorlevel = int(
            self.thistag.get('errorLevel', default=1))

    def run(self):
        """Execute a system command line.

        Returns: Masked exit code of the action.
        """
        # Apply tokens to the command line.
        cmdline = self.expand(self.cmdline)

        # Execute the tokenized system command. If the process fails
        # to start, it'll throw an OSError. Treat that as a
        # non-maskable hook failure.
        logger.debug('cmdline="{}", errorlevel={}'
                      .format(cmdline, self.errorlevel))

        p = subprocess.Popen(shlex.split(cmdline),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=False)

        # The process started, wait for it to finish.
        p.wait()

        # Compare the process exit code to the error level.
        if p.returncode >= self.errorlevel:
            errstr = p.stderr.read()
            logger.error(errstr)

            # Output the client message.
            sys.stderr.write(errstr)

            # Return the terminal exit code.
            return p.returncode
        else:
            logger.debug('exit code={}'.format(p.returncode))

        # Indicate a non-terminal action.
        return 0

class SetRevisionFile(Action):

    def __init__(self, *args, **kwargs):
        super(SetRevisionFile, self).__init__(*args, **kwargs)

        # Get the revision number.
        if 'Revision' not in self.context.tokens:
            raise RuntimeError(
                'Required token not found: Revision')
        self.revision = self.context.tokens['Revision']

        # Get the file path name.
        if self.thistag.text == None:
            raise ValueError(
                'Required tag content missing: SetRevisionFile')
        self.file = self.thistag.text

    def run(self):
        """Write the current revision number into a file.

        Returns: Exit code (zero) of the action.
        """
        # Get the revision file path name.
        revfile = self.expand(self.file)

        # Write the revision number into the file.
        with open(revfile, 'w') as f:
            f.write(self.revision + '\n')

        logger.info('Wrote revision #{} to "{}".'.format(
                self.revision, revfile))

        # Indicate a non-terminal action.
        return 0

########################### end of file ##############################
