#!/usr/bin/env python
######################################################################
# Test User Filter
######################################################################
import os, re, sys, unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

class TestFilterUser(HookTestCase):
    """User Filter Tests"""

    def setUp(self):
        super(TestFilterUser, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_regex(self):
        """User regex missing"""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterUser>
              <SendError>Can't touch this.</SendError>
            </FilterUser>
          </Actions>
          ''')

        # Call the hook script.
        p = self.callHook(
            'pre-lock', self.repopath, '/fileA1.txt',
            self.username, 'mytoken', 1)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegex(
            stderrdata, r'Internal hook error',
            'Expected error message not found')

        # Verify the exit code is correct.
        self.assertEqual(
            p.returncode, 255,
            'Error exit code not found: '\
            ' exit code = {0}'.format(p.returncode))

        # Verify the proper error message is returned.
        self.assertRegex(
            stderrdata, r'Internal hook error',
            'Expected error message not found')

        # Verify that the detailed error is logged.
        self.assertLogRegexp(
            'pre-lock', r'\nValueError: Required tag missing',
            'Expected error not found in hook log')

    def test_02_match(self):
        """User match"""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterUser>
              <UserRegex>User</UserRegex>
              <SendError>Invalid lock user.</SendError>
            </FilterUser>
          </Actions>
          ''')

        # Apply the new lock.
        p = self.lockWcPath('fileA1.txt', user='user2')
        stdoutdata, stderrdata = p.communicate()

        # Verify that the error message was produced.
        self.assertRegex(
            stderrdata, r'Invalid lock user',
            'Expected error message not found')

        # Verify that an error was indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

    def test_03_mismatch(self):
        """User mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterUser>
              <UserRegex>zUser</UserRegex>
              <SendError>Invalid lock user.</SendError>
            </FilterUser>
          </Actions>
          ''')

        # Apply the new lock.
        p = self.lockWcPath('fileA1.txt', user='user2')
        stdoutdata, stderrdata = p.communicate()

        # Verify that an error message wasn't produced.
        self.assertRegex(
            stderrdata, r'(?s)^\s*$',
            'Unexpected error message found')

        # Verify that an error wasn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterUser]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
