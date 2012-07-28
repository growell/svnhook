#!/usr/bin/env python
######################################################################
# Test SMTP Non-Filter Revision Actions
######################################################################
import os, re, sys, unittest, time
import subprocess

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import SmtpTestCase

# Test Hook and Configuration File
testhook = 'post-commit'
testconf = 'post-commit.xml'

class TestActions(SmtpTestCase):

    def setUp(self):
        super(TestActions, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_basic(self):
        """Send a log email to multiple recipients."""
        # Define the message parameters.
        fromaddr = 'source@mydomain.com'
        toaddrs = ['gal{}@yourdomain.com'.format(idx)
                   for idx in range(1, 10)]
        subject = 'test @ {}'.format(time.asctime())

        # Define the hook configuration.
        totags = ['<ToAddress>{}</ToAddress>'.format(toaddr)
                  for toaddr in toaddrs]

        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SendLogSmtp port="{}">
              <FromAddress>{}</FromAddress>
              {}
              <Subject>{}</Subject>
            </SendLogSmtp>
          </Actions>
          '''.format(self.smtpport, fromaddr, ''.join(totags),
                     subject))

        # Call the script that uses the configuration.
        p = self.callHook(testhook, self.repopath, '1')
        p.wait()

        # Check for the default exit code.
        self.assertEqual(
            p.returncode, 0,
            'Exit code not correct: {}'.format(p.returncode))

        # Get the received email message.
        try:
            message = self.getMessage(subject=subject)
        except KeyError:
            self.fail('Message with subject not found: ' + subject)

        # Check that all addresses are included.
        self.assertFromAddress(message, fromaddr)
        for toaddr in toaddrs: self.assertToAddress(message, toaddr)

        # Check that the message body is correct.
        self.assertBodyRegexp(
            message, r'\nChanged paths:\n\s+A\s+/dir1\n')
        self.assertBodyRegexp(message, r'(?m)^Initial import$')

    def test_02_minimal(self):
        """Send a stripped-down log email."""
        # Define the message parameters.
        subject = 'test @ {}'.format(time.asctime())

        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SendLogSmtp port="{}" verbose="no">
              <FromAddress>source@mydomain.com</FromAddress>
              <ToAddress>gal1@yourdomain.com</ToAddress>
              <Subject>{}</Subject>
            </SendLogSmtp>
          </Actions>
          '''.format(self.smtpport, subject))

        # Call the script that uses the configuration.
        p = self.callHook(testhook, self.repopath, '1')
        p.wait()

        # Check for the default exit code.
        self.assertEqual(
            p.returncode, 0,
            'Exit code not correct: {}'.format(p.returncode))

        # Get the received email message.
        try:
            message = self.getMessage(subject=subject)
        except KeyError:
            self.fail('Message with subject not found: ' + subject)

        # Check that the message body is correct.
        self.assertBodyNotRegexp(message, r'(?im)^Changed paths:$')
        self.assertBodyRegexp(message, r'(?m)^Initial import$')

# Allow manual execution of tests.
if __name__=='__main__':
    suite = unittest.TestLoader()\
        .loadTestsFromTestCase(TestActions)
    unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
