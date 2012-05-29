#!/usr/bin/env python
######################################################################
# Test Commit Author Filter
######################################################################
import os, re, sys, unittest, time
from subprocess import CalledProcessError

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from tests.base import HookTestCase, SmtpTestCase

class TestFilterAuthor1(HookTestCase):
    """Pre-Commit Tests"""

    def setUp(self):
        super(TestFilterAuthor1, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_allow_author(self):
        """Exact blocked author commit."""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterAuthor>
              <AuthorRegex>ReadOnly</AuthorRegex>
              <SendError>Commits not allowed by ReadOnly</SendError>
            </FilterAuthor>
          </Actions>
          ''')

        # Apply a working copy change.
        self.addWcFile('fileA.txt')

        # Attempt to commit the change as the exact blocked author.
        p = self.commitWc(username='ReadWrite')

        # Check for unexpected error details.
        errstr = p.stderr.read()
        self.assertNotRegexpMatches(
            errstr, r'\S', 'Unexpected error message')

        # Check for the expected success.
        self.assertEqual(
            p.returncode, 0,
            'Expected success exit code not found')

    def test_02_block_author(self):
        """Exact blocked author commit."""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterAuthor>
              <AuthorRegex>ReadOnly</AuthorRegex>
              <SendError>Commits not allowed by ReadOnly</SendError>
            </FilterAuthor>
          </Actions>
          ''')

        # Apply a working copy change.
        self.addWcFile('fileA.txt')

        # Attempt to commit the change as the exact blocked author.
        p = self.commitWc(username='ReadOnly')

        # Check for the expected failure.
        self.assertNotEqual(
            p.returncode, 0,
            'Expected non-zero exit code not found!')

        # Check for the expected error details (via SendError).
        errstr = p.stderr.read()
        self.assertRegexpMatches(
            errstr, r'Commits not allowed by ReadOnly')

    def test_03_block_author_ci(self):
        """Case-insensitive blocked author commit."""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterAuthor>
              <AuthorRegex>readonly</AuthorRegex>
              <SendError>Commits not allowed by ${Author}</SendError>
            </FilterAuthor>
          </Actions>
          ''')

        # Apply a working copy change.
        self.addWcFile('fileA.txt')

        # Attempt to commit the change as the exact blocked author.
        p = self.commitWc(username='ReadOnly')

        # Check for the expected failure.
        self.assertNotEqual(
            p.returncode, 0,
            'Expected non-zero exit code not found!')

        # Check for the expected error details (via SendError).
        errstr = p.stderr.read()
        self.assertRegexpMatches(
            errstr, r'Commits not allowed by ReadOnly')

class TestFilterAuthor2(SmtpTestCase):
    """Post-Commit Tests"""

    def setUp(self):
        super(TestFilterAuthor2, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_04_block_author(self):
        """Suspicious author email"""
        # Define the message parameters.
        subject = 'test @ {}'.format(time.asctime())
        body = 'User ${Author} committed r${Revision}!'

        # Define the hook configuration. In actual use, you're more
        # likely to send a log message email.
        self.writeConf('post-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterAuthor>
              <AuthorRegex>ReadOnly</AuthorRegex>
              <SendSmtp port="{}">
                <FromAddress>source@mydomain.com</FromAddress>
                <ToAddress>destination@yourdomain.com</ToAddress>
                <Subject>{}</Subject>
                <Message>{}</Message>
              </SendSmtp>
            </FilterAuthor>
          </Actions>
          '''.format(self.smtpport, subject, body))

        # Apply a working copy change.
        self.addWcFile('fileA.txt')

        # Commit the change as the suspicious author.
        p = self.commitWc(username='ReadOnly')

        # Check for the expected success.
        self.assertEqual(
            p.returncode, 0,
            'Expected exit code not found')

        # Look for the email message. It'll be missing, if the
        # post-commit hook didn't fire.
        try:
            message = self.getMessage(subject=subject)
        except KeyError:
            self.fail('Message with subject not found: ' + subject)

        # Check the message details.
        self.assertBodyRegexp(
            message, r'User ReadOnly committed r\d+!')

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterAuthor1, TestFilterAuthor2]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
    unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
