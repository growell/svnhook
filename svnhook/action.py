"""Subversion Hook Action Classes

Provide classes that handle non-filtering hook actions.
"""
__version__ = '3.00'
__all__     = ['Action', 'SetToken', 'SendError', 'SendSmtp',
               'ExecuteCmd']

import logging
import re
import smtplib
import sys
import textwrap

logger = logging.getLogger()

class Action(object):

    def __init__(self, context, thistag):
        self.context = context
        self.thistag = thistag

class SetToken(Action):

    def run(self):
        """Set a token to be used in template substitutions.

        Returns:
        Exit code of the action.

        """
        try:
            name = self.thistag.attrib['name']
        except KeyError:
            raise ValueError(
                'Required attribute missing: name')

        # Set the token value.
        self.context.tokens[name] = self.thistag.text or ''

        # Indicate a non-terminal action.
        return 0

class SendError(Action):

    def run(self):
        """Send a STDERR message to Subversion.

        Returns:
        Terminal (non-zero) exit code of the action.

        """
        if self.thistag.text == None:
            raise ValueError(
                'Required tag content missing: SendError')

        # Trim leading whitespace from the error message. Apply any
        # tokens.
        errormsg = self.context.expand(textwrap.dedent(
                re.sub(r'(?s)^[\n\r]+', '', self.thistag.text)))

        # Log the error message lines.
        for e in errormsg.splitlines(): logger.error(e.lstrip())

        # Output the client message.
        sys.stderr.write(errormsg)

        # Return the terminal (non-zero) exit code.
        return int(self.thistag.get('exitCode', default=1))

class SendSmtp(Action):

    def run(self):
        """Send a mail message.

        Returns:
        Exit code of the action.

        """
        # Get the SMTP server host name.
        try:
            host = self.context.expand(self.thistag.attrib['server'])
        except KeyError:
            raise ValueError(
                'Required attribute missing: server')

        # Get the maximum number of connect seconds.
        try:
            timeout = int(self.thistag.get('seconds', default=60))
        except ValueError:
            raise ValueError('Illegal seconds attribute: {}'
                             .format(self.thistag.get('seconds')))

        # Get the from email address.
        fromtag = self.thistag.find('FromAddress')
        if fromtag == None:
            raise ValueError(
                'Required tag missing: FromAddress')
        fromaddress = self.context.expand(fromtag.text)
        
        # Get the recipient email addresses.
        toaddresses = []
        for totag in self.thistag.findall('ToAddress'):
            toaddresses.append(self.context.expand(totag.text))
        if len(toaddresses) == 0:
            raise ValueError(
                'Required tag missing: ToAddress')

        # Get the message subject line.
        subjecttag = self.thistag.find('Subject')
        if subjecttag == None:
            raise ValueError(
                'Required tag missing: Subject')
        subject = self.context.expand(subjecttag.text)

        # Get the message body.
        messagetag = self.thistag.find('Message')
        if messagetag == None:
            raise ValueError(
                'Required tag missing: Message')
        message = self.context.expand(messagetag.text)

        # Assemble the message content.
        content = 'From: {}\r\n'.format(fromaddress)
        for toaddress in toaddresses:
            content += 'To: {}\r\n'.format(toaddress)
        content += 'Subject: {}\r\n'.format(subject)

        content += '\r\n'
        for msgline in message.splitlines():
            content += '{}\r\n'.format(msgline)

        # Construct the SMTP connection.
        server = smtplib.SMTP(host, None, None, timeout)

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

class ExecuteCmd(Action):

    def run(self):
        """Execute a system command line.

        Returns:
        Exit code of the action.

        """
        if self.thistag.text == None:
            raise ValueError(
                'Required tag content missing: ExecuteCmd')

        # Apply tokens to the command line.
        cmdline = self.context.expand(self.thistag.text)

        # Get the minimum exit code needed to signal a hook failure.
        errorlevel = int(self.thistag.get('errorLevel', default=1))

        # Execute the tokenized system command. If the process fails
        # to start, it'll throw an OSError. Treat that as a
        # non-maskable hook failure.
        logger.debug('cmdline="{}", errorlevel={}'
                      .format(cmdline, errorlevel))

        p = subprocess.Popen(shlex.split(cmdline),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=False)

        # The process started, wait for it to finish.
        p.wait()

        # Compare the process exit code to the error level.
        if p.returncode >= errorlevel:
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

########################### end of file ##############################
