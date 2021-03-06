#!/usr/bin/env python
######################################################################
# Test Log Message Filter
######################################################################
import os, re, sys, unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

class TestFilterLogMsg(HookTestCase):
    """File Content Filter Tests"""

    def setUp(self):
        super(TestFilterLogMsg, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_regex(self):
        """No regex tag"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLogMsg>
              <SendError>Not gonna happen.</SendError>
            </FilterLogMsg>
          </Actions>
          ''')

        # Add a working copy change.
        self.addWcFile('fileA1.txt')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error is indicated. Please note that this is
        # NOT the hook script exit code. This is the "svn commit" exit
        # code - that indicates if the commit succeeded (zero) or
        # failed (one).
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Internal hook error',
            'Internal error message not returned')

        # Verify that the detailed error is logged.
        self.assertLogRegexp(
            'pre-commit', r'\nValueError: Required tag missing',
            'Expected error not found in hook log')

    def test_02_match(self):
        """Log message match"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLogMsg>
              <LogMsgRegex>secret</LogMsgRegex>
              <SendError>Cannot expose secret!</SendError>
            </FilterLogMsg>
          </Actions>
          ''')

        # Add a working copy change.
        self.addWcFile('fileA1.txt')

        # Attempt to commit the change.
        p = self.commitWc('Tell the secret.')

        # Verify that an error is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Cannot expose secret!',
            'Expected error message not found')

    def test_03_mismatch(self):
        """Log message mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLogMsg>
              <LogMsgRegex>secret</LogMsgRegex>
              <SendError>Cannot expose secret!</SendError>
            </FilterLogMsg>
          </Actions>
          ''')

        # Add a working copy change.
        self.addWcFile('fileA1.txt')

        # Attempt to commit the change.
        p = self.commitWc('I\'m not telling.')

        # Verify that an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

        # Verify that an error message isn't returned.
        self.assertRegexpMatches(
            p.stderr.read(), r'(?s)^\s*$',
            'Unexpected error message found')

    def test_04_no_required_msg(self):
        """Required log message missing"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLogMsg>
              <LogMsgRegex sense="0">\S</LogMsgRegex>
              <SendError>Log message is required.</SendError>
            </FilterLogMsg>
          </Actions>
          ''')

        # Add a working copy change.
        self.addWcFile('fileA1.txt')

        # Attempt to commit the change (without a message).
        p = self.commitWc()

        # Verify that an error is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Log message is required',
            'Expected error message not found')

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterLogMsg]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
