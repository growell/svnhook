#!/usr/bin/env python
######################################################################
# Test SMTP Non-Filter Actions
######################################################################
import os, re, sys, unittest, time
import subprocess

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import SmtpTestCase

# Test Hook and Configuration File
testhook = 'start-commit'
testconf = 'start-commit.xml'

class TestActions(SmtpTestCase):

    def setUp(self):
        super(TestActions, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_basic(self):
        """Send a simple SMTP message."""
        # Define the message parameters.
        fromaddr = 'source@mydomain.com'
        toaddr = 'destination@yourdomain.com'
        subject = 'test @ {0}'.format(time.asctime())
        body = 'Hello World'

        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SendSmtp port="{0}">
              <FromAddress>{1}</FromAddress>
              <ToAddress>{2}</ToAddress>
              <Subject>{3}</Subject>
              <Message>{4}</Message>
            </SendSmtp>
          </Actions>
          '''.format(self.smtpport, fromaddr, toaddr, subject, body))

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')
        p.wait()

        # Check for the default exit code.
        self.assertEqual(
            p.returncode, 0,
            'Exit code not correct: {0}'.format(p.returncode))

        # Look for the email message.
        try:
            message = self.getMessage(subject=subject)
        except KeyError:
            self.fail('Message with subject not found: ' + subject)

        # Check the message details.
        self.assertFromAddress(message, fromaddr)
        self.assertToAddress(message, toaddr)
        self.assertBody(message, body)

    def test_02_multiple_to(self):
        """Send an email to multiple recipients."""
        # Define the message parameters.
        toaddrs = ['gal{0}@yourdomain.com'.format(idx)
                   for idx in range(1, 10)]
        subject = 'test @ {0}'.format(time.asctime())

        # Define the hook configuration.
        totags = ['<ToAddress>{0}</ToAddress>'.format(toaddr)
                  for toaddr in toaddrs]

        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SendSmtp port="{0}">
              <FromAddress>source@mydomain.com</FromAddress>
              {1}
              <Subject>{2}</Subject>
              <Message>Hello World!</Message>
            </SendSmtp>
          </Actions>
          '''.format(self.smtpport, ''.join(totags), subject))

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')
        p.wait()

        # Check for the default exit code.
        self.assertEqual(
            p.returncode, 0,
            'Exit code not correct: {0}'.format(p.returncode))

        # Get the received email message.
        try:
            message = self.getMessage(subject=subject)
        except KeyError:
            self.fail('Message with subject not found: ' + subject)

        # Check that all addresses are included.
        for toaddr in toaddrs: self.assertToAddress(message, toaddr)

# Allow manual execution of tests.
if __name__=='__main__':
    suite = unittest.TestLoader()\
        .loadTestsFromTestCase(TestActions)
    unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
